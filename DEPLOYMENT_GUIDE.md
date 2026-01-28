# 🚀 Hosting your Backend on Render.com

This guide will walk you through the steps to host your Python FastAPI backend using the newly created `Dockerfile` and `render.yaml`.

## 1. Prerequisites
*   A **GitHub** account with your code pushed to a repository.
*   A **Render.com** account (linked to your GitHub).
*   Your **MongoDB URI** (from MongoDB Atlas).

## 2. Pushing to GitHub
Ensure you have added and pushed the new files in the `backend` folder:
*   `Dockerfile`
*   `requirements.txt`
*   `render.yaml`
*   `main.py` (with the updated CORS settings)

## 3. Deploying using Render Blueprints (Recommended)
Render will automatically detect the `render.yaml` file.
1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. Click the **"New +"** button and select **"Blueprint"**.
3. Connect your GitHub repository.
4. Render will read the `render.yaml` and show you the configuration.
5. **Important**: You will see a field for `MONGO_URI`. Paste your connection string there.
6. Click **"Apply"**.

## 4. Manual Configuration (Alternative)
If you prefer not to use Blueprints:
1. Click **"New +"** -> **"Web Service"**.
2. Connect your repository.
3. Choose **"Docker"** as the Runtime.
4. Set the **Root Directory** to `backend`.
5. Under **Environment Variables**, add:
    *   `MONGO_URI`: Your connection string.
    *   `SECRET_KEY`: A long random string.
    *   `PORT`: `8000`

## 5. Final Step: Link it to the Frontend
Once the backend is live, Render will give you a URL (e.g., `https://intellexa-backend.onrender.com`).
You must update your frontend `API_BASE_URL` or environment variables to point to this new address.

---
**Note**: Render's Free Tier "sleeps" after 15 minutes of inactivity. The first request after a break may take ~30 seconds to wake up the server.
