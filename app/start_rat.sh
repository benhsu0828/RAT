#!/bin/bash
# 給腳本執行權限
# chmod +x start_rat.sh

# 1. 設定環境變數
source setup.sh
# 語言模型設定
# export MODEL_TYPE=ollama
export MODEL_TYPE=openai

# # 2. 檢查 Ollama 服務
# echo "📡 檢查 Ollama 服務..."
# if ! curl -s http://localhost:11434/api/version > /dev/null; then
#     echo "啟動 Ollama 服務..."
#     ollama serve &
#     sleep 10
# fi

# # 3. 確保模型存在
# echo "🤖 檢查 Llama2 模型..."
# if ! ollama list | grep -q "llama2"; then
#     echo "下載 Llama2 模型..."
#     ollama pull llama2
# fi

# 4. 啟動 RAT 應用
echo "🎯 啟動 RAT 應用..."
python gradio_app.py