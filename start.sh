#!/bin/bash

# Start the Backend (FastAPI)
echo "Starting Backend..."
uvicorn backend:app --host 0.0.0.0 --port 8000 &

# Start the Frontend (Streamlit)
echo "Starting Frontend..."
streamlit run main.py --server.port 8501 --server.address 0.0.0.0 &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
