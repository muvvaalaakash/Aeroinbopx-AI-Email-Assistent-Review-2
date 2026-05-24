# AeroInbox: AI-Powered Executive Email Assistant MVP

AeroInbox is a real-world, industry-level email intelligence assistant built for managers, founders, and CEOs to reduce the time spent reading, organizing, and replying to emails. It connects securely to Gmail, fetches unread mail, uses OpenAI `gpt-4o-mini` to extract structured executive summaries, computes priority levels, and draft responses.

## Key Features
- **Secure Gmail Authentication**: Fully stateless OAuth 2.0 flow.
- **On-Demand AI Analysis**: Processes single emails to control token costs and speed up response times.
- **Executive Summary & Priority Badging**: Sorts emails into High, Medium, and Low priorities instantly.
- **Draft Copy Actions**: Generate high-quality professional drafts with one-click copy capability.

---

## Folder Structure

```
ai-executive-assistant/
├── backend/                  # FastAPI Backend
│   ├── config/               # Settings & Configuration (Pydantic)
│   ├── routes/               # API Router Handlers (Auth, Email, AI)
│   ├── services/             # Core Integrations (Gmail, OpenAI)
│   ├── main.py               # Application bootstrap
│   ├── requirements.txt      # Python package list
│   └── .env                  # Backend credentials config
│
└── frontend/                 # React SPA (Vite + Tailwind CSS v4)
    ├── src/
    │   ├── components/       # Visual elements (Sidebar, Header, cards)
    │   ├── pages/            # View frames (Login, Dashboard, Callback)
    │   ├── services/         # Axios API Client interceptors
    │   ├── App.jsx           # Routing index
    │   └── main.jsx          # Entry point script
    ├── vite.config.js        # Vite & Tailwind compilation plugin
    ├── package.json          # Node packages and build metadata
    └── .env                  # Frontend build configs
```

---

## Prerequisites
- **Python 3.9+**
- **Node.js 18+**
- **Google Cloud Platform Project** with Gmail API enabled and OAuth Web Application credentials set up.
- **OpenAI API Key** (access to `gpt-4o-mini`).

---

## Local Setup & Run

### 1. Backend Setup
1. Open a terminal and navigate to the `backend/` folder:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your environment variables. Open `.env` and fill in the values:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_CLIENT_ID=your_gcp_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_gcp_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
   FRONTEND_URL=http://localhost:5173
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
   The backend API will run on `http://localhost:8000`. You can inspect the Swagger interactive documentation at `http://localhost:8000/docs`.

### 2. Frontend Setup
1. Open a new terminal and navigate to the `frontend/` folder:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Configure the frontend API endpoint in `.env`:
   ```env
   VITE_API_URL=http://localhost:8000
   ```
4. Spin up the Vite development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## Google Cloud Credentials Configuration

Ensure your Google OAuth 2.0 configuration has the following:
1. **Authorized JavaScript origins**: `http://localhost:5173`
2. **Authorized redirect URIs**: `http://localhost:8000/auth/callback`
3. **Enabled Scopes**:
   - `openid`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `https://www.googleapis.com/auth/gmail.readonly`

---

## Azure Production Deployment

### 1. Backend Deployment (Azure App Service - F1 Free Tier)
1. In the Azure Portal, create a new **Web App**:
   - **Runtime Stack**: Python (choose your version, e.g., Python 3.11).
   - **Operating System**: Linux.
   - **Pricing Plan**: Free F1.
2. In your Web App's **Configuration / Environment Variables** section, add:
   - `OPENAI_API_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI` (update to `https://<your-app-service-name>.azurewebsites.net/auth/callback`)
   - `FRONTEND_URL` (update to the Azure Static Web Apps URL)
3. Set the startup command to:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```
4. Deploy the contents of the `backend/` folder via GitHub Actions or Git Local.

### 2. Frontend Deployment (Azure Static Web Apps)
1. Create a new **Static Web App** in Azure.
2. Select your repository and specify the deployment configuration:
   - **App location**: `/frontend`
   - **Api location**: (Leave blank, as we run FastAPI on App Service)
   - **Output location**: `dist`
3. In Azure Static Web Apps dashboard, under Environment variables, set:
   - `VITE_API_URL` = `https://<your-app-service-name>.azurewebsites.net`
4. Deploy the build via the automatically configured GitHub Action workflow.
5. Make sure to update the **GCP Console Credentials** with the production URL of your backend callback and frontend origin.
