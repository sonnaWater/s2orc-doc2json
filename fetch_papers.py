import os
import urllib.request
from pathlib import Path

# 目標：三篇極具代表性、排版複雜的 AI/量化論文
PAPERS = {
    "Deep_Learning_in_Finance": "https://arxiv.org/pdf/2002.05780.pdf",
    "Attention_Is_All_You_Need": "https://arxiv.org/pdf/1706.03762.pdf",
    "Reinforcement_Learning_Quant": "https://arxiv.org/pdf/1911.10107.pdf"
}

TARGET_DIR = Path("data/input_pdfs")
TARGET_DIR.mkdir(parents=True, exist_ok=True)

print("[*] 開始下載壓力測試 PDF...")
for name, url in PAPERS.items():
    filepath = TARGET_DIR / f"{name}.pdf"
    if not filepath.exists():
        print(f"  -> 下載中: {name}.pdf")
        urllib.request.urlretrieve(url, filepath)
        print(f"  -> 成功: {filepath}")
    else:
        print(f"  -> 已存在: {name}.pdf (跳過)")

print("[*] 下載完成，請檢查 data/input_pdfs/ 目錄。")