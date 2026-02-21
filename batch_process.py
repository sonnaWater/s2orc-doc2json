import os
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import json

# ================= 配置區塊 =================
# 路徑需對應 docker-compose.yml 中的掛載設定
INPUT_DIR = Path("/app/data/input_pdfs")
OUTPUT_DIR = Path("/app/data/output_json")
TEMP_DIR = Path("/app/temp")
# 舊的：ERROR_LOG = Path("/app/data/error_log.json")
# 請改成下面這行：
ERROR_LOG = Path("/app/data/output_json/error_log.json")

# 併發數量：建議設定為 (CPU 核心數 * 2)，因為這主要卡在等待 Grobid API 的網路 I/O
MAX_WORKERS = 8 
# 單檔超時保護 (秒)：防止 Grobid 遇到破損 PDF 導致死鎖
TIMEOUT_SECONDS = 300 
# ============================================

def setup_directories():
    """確保目錄存在"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

def process_single_pdf(pdf_path: Path):
    """單一 PDF 的處理 Worker (使用 subprocess 達到記憶體與崩潰隔離)"""
    expected_json = OUTPUT_DIR / f"{pdf_path.stem}.json"
    
    # 【斷點續傳機制】如果目標 JSON 已存在，直接跳過
    if expected_json.exists():
        return (str(pdf_path), "SKIPPED", None)

    # 封裝要呼叫的指令
    cmd = [
        # 舊的："python", "doc2json/pdf2json/process_pdf.py",
        # 請改成 grobid2json：
        "python", "doc2json/grobid2json/process_pdf.py",
        "-i", str(pdf_path),
        "-t", str(TEMP_DIR),
        "-o", str(OUTPUT_DIR)
    ]
    
    try:
        # 執行外部指令，擷取輸出
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=TIMEOUT_SECONDS
        )
        if result.returncode == 0:
            return (str(pdf_path), "SUCCESS", None)
        else:
            return (str(pdf_path), "ERROR", result.stderr)
            
    except subprocess.TimeoutExpired:
        return (str(pdf_path), "TIMEOUT", f"Execution exceeded {TIMEOUT_SECONDS}s")
    except Exception as e:
        return (str(pdf_path), "EXCEPTION", str(e))

def main():
    setup_directories()
    
    # 取得所有 PDF 檔案清單
    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    print(f"[*] 發現 {len(pdf_files)} 份 PDF 檔案。")
    if not pdf_files:
        return

    failed_records = []

    # 啟動執行緒池
    print(f"[*] 啟動批次處理，配置 {MAX_WORKERS} 個 Worker...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 將任務派發給 Worker
        future_to_pdf = {executor.submit(process_single_pdf, pdf): pdf for pdf in pdf_files}
        
        # 使用 tqdm 建立進度條
        for future in tqdm(as_completed(future_to_pdf), total=len(pdf_files), desc="Processing"):
            pdf_path, status, error_msg = future.result()
            
            if status not in ("SUCCESS", "SKIPPED"):
                failed_records.append({
                    "file": pdf_path,
                    "status": status,
                    "error": error_msg
                })

    # 將錯誤紀錄輸出成 JSON，方便後續 Debug 或重試
    if failed_records:
        with open(ERROR_LOG, "w", encoding="utf-8") as f:
            json.dump(failed_records, f, indent=4, ensure_ascii=False)
        print(f"[!] 處理完成。共有 {len(failed_records)} 份檔案失敗，詳情請見 {ERROR_LOG}")
    else:
        print("[*] 完美收工！所有檔案皆成功處理或跳過。")

if __name__ == "__main__":
    main()