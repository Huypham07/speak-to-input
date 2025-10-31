#!/bin/bash
# Retry up to 3 times if whisper-server exits
MAX_RETRIES=3
COUNT=0

while [ $COUNT -lt $MAX_RETRIES ]; do
    echo "Starting whisper-server (attempt $((COUNT+1))/$MAX_RETRIES)..."
    ./build/bin/whisper-server --host 0.0.0.0 -m ./models/ggml-medium.bin --language vi --threads 8
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "whisper-server exited normally."
        exit 0
    else
        echo "whisper-server crashed with exit code $EXIT_CODE. Retrying..."
        COUNT=$((COUNT+1))
        sleep 2
    fi
done

echo "whisper-server failed $MAX_RETRIES times. Exiting."
exit 1
