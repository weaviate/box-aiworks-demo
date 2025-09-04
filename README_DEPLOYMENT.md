# Deployment Guide

This guide explains how to deploy the Weaviate Enterprise Search application with the backend on Railway and frontend on Streamlit Community Cloud.

## Architecture

- **Backend (FastAPI)**: Deployed on Railway
- **Frontend (Streamlit)**: Deployed on Streamlit Community Cloud
- **Database**: Weaviate Cloud (external service)

## Backend Deployment (Railway)

### 1. Deploy to Railway

1. Push your code to GitHub
2. Connect your GitHub repository to Railway
3. Railway will automatically detect the `Procfile` and deploy your FastAPI app

### 2. Set Environment Variables in Railway

In your Railway project dashboard, set these environment variables:

```
WCD_URL=your_weaviate_cloud_url
WCD_API_KEY=your_weaviate_api_key
ANTHROPIC_APIKEY=your_anthropic_api_key (optional)
OPENAI_API_KEY=your_openai_api_key (optional)
```

### 3. Get Your Railway URL

After deployment, Railway will provide you with a URL like:
`https://your-app-name.railway.app`

## Frontend Deployment (Streamlit Community Cloud)

### 1. Prepare Your Repository

Make sure your repository has:
- `streamlit_app.py` (your Streamlit app)
- `streamlit_requirements.txt` (minimal requirements for Streamlit)
- `requirements.txt` (full requirements for Railway backend)

### 2. Deploy to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Set the main file path to `streamlit_app.py`
4. Set the requirements file to `streamlit_requirements.txt`

### 3. Set Environment Variables in Streamlit

In your Streamlit Community Cloud app settings, set:

```
API_BASE_URL=https://your-railway-app-url.railway.app
```

Replace `your-railway-app-url.railway.app` with your actual Railway URL.

## Local Development

### Backend (FastAPI)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the backend
uvicorn app:app --reload --port 8000
```

### Frontend (Streamlit)

```bash
# Install Streamlit dependencies
pip install -r streamlit_requirements.txt

# Set environment variable for local development
export API_BASE_URL=http://localhost:8000

# Run the frontend
streamlit run streamlit_app.py
```

## Testing

1. **Backend API**: Visit `https://your-railway-url.railway.app/docs` for API documentation
2. **Frontend**: Visit your Streamlit Community Cloud URL
3. **Integration**: The Streamlit app should connect to your Railway backend

## Troubleshooting

### CORS Issues
If you encounter CORS issues, make sure your FastAPI app has CORS middleware configured (already included in your `app.py`).

### API Connection Issues
- Verify the `API_BASE_URL` environment variable is set correctly in Streamlit
- Check that your Railway backend is running and accessible
- Ensure the Railway URL doesn't have a trailing slash

### Environment Variables
- Double-check all environment variables are set in both Railway and Streamlit
- Make sure there are no typos in variable names
