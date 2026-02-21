# 使用輕量級的 Python 3.9 作為基底
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統層級的依賴（處理 LaTeX 解析必要的工具）
RUN apt-get update && apt-get install -y \
    texlive-extra-utils \
    tralics \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製專案所有原始碼到容器內
COPY . /app

# 安裝專案本身的 Python 依賴包
RUN pip install --no-cache-dir -e .
# (請加入這行，永久安裝進度條套件)
RUN pip install -r requirements.txt

# 設定預設指令：保持容器在背景運行，做為一個 Worker 節點
CMD ["tail", "-f", "/dev/null"]