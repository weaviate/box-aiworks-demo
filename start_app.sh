# start_app.sh
#!/bin/bash

echo "🚀 Starting Weaviate Enterprise Search Application..."

# Start FastAPI backend
echo "📡 Starting FastAPI backend..."
uvicorn app:app --host 0.0.0.0 --port 8000 --reload &

# Wait a moment for the backend to start
sleep 3

# Start Streamlit frontend
echo "�� Starting Streamlit frontend..."
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0

echo "✅ Application started!"
echo "📡 Backend API: http://localhost:8000"
echo "🎨 Frontend UI: http://localhost:8501"
