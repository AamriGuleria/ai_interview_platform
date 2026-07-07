
set -e  # exit on first error

MODEL="${1:-qwen2.5:3b}"   # default model if none passed in

echo "=================================================="
echo " Ollama Environment Setup"
echo " Target model: $MODEL"
echo "=================================================="

# 1. Install Ollama if not already installed
if ! command -v ollama &> /dev/null; then
    echo "[1/4] Ollama not found. Installing..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "[1/4] Ollama already installed: $(ollama --version)"
fi

# 2. Start the Ollama server in the background (if not already running)
echo "[2/4] Checking if Ollama server is running..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "      Starting Ollama server in background..."
    nohup ollama serve > /tmp/ollama_serve.log 2>&1 &
    sleep 3   # give it a moment to boot up
else
    echo "      Ollama server already running."
fi

# 3. Pull the model (safe to re-run, no-op if already present)
echo "[3/4] Pulling model: $MODEL"
ollama pull "$MODEL"

# 4. Confirm setup
echo "[4/4] Verifying installed models:"
ollama list

echo "=================================================="
echo " Setup complete!"
echo " To start an interactive session, run:"
echo "   ollama run $MODEL"
echo "=================================================="

# ollama list                    # show downloaded models
# ollama pull qwen2.5:3b          # download a model (without running)
# ollama run qwen2.5:3b           # download (if needed) + open interactive chat session
# ollama serve                    # start the background server (usually auto-starts)
# ollama ps                       # show currently loaded/running models
# ollama rm qwen2.5:3b             # remove a model