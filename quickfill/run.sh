# Kill the process that is running on port 8080
if [[ "$(uname)" == "Darwin" ]]; then
    # For Mac OS
    lsof -ti :8080 | xargs kill -9
elif [[ "$(uname -a)" == *"Microsoft"* ]]; then
    # For Windows Subsystem for Linux (WSL)
    lsof -ti :8080 | xargs --no-run-if-empty kill -9
else
    echo "Unsupported operating system."
    exit 1
fi

# Start App
uvicorn --port 8080 --host 127.0.0.1 quickfill.main:app --reload