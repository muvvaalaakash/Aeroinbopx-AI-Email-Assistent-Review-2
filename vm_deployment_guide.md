# AeroInbox: Azure VM Deployment & Exposure Guide

This guide details the step-by-step instructions required to securely deploy, expose, and configure SSL for AeroInbox on your Azure VM.

---

## Step 1: Open Azure VM Firewall Ports (Network Security Group)
Ensure that your VM's **Network Security Group (NSG)** on the Azure Portal has inbound security rules configured to allow traffic on the following public ports:
*   **Port 22** (SSH) - For remote access.
*   **Port 80** (HTTP) - For standard web traffic and Let's Encrypt verification.
*   **Port 443** (HTTPS) - For secure encrypted web traffic.

---

## Step 2: Configure the Host Nginx Reverse Proxy
In our `docker-compose.yml`, the frontend container's Nginx is mapped to `127.0.0.1:8080:80` for security. To expose it to the internet under your custom domain (e.g. `aeroinbox.qzz.io`), you must configure an Nginx instance running directly on the **host VM** to proxy public traffic.

1.  **Install Nginx on the VM:**
    ```bash
    sudo apt-get update
    sudo apt-get install -y nginx
    ```

2.  **Configure the Server Block:**
    Open the default configuration file:
    ```bash
    sudo nano /etc/nginx/sites-available/default
    ```

3.  **Replace the file contents with the following proxy configuration:**
    *(Replace `aeroinbox.qzz.io` with your actual domain or VM public IP if you don't have a domain)*:
    ```nginx
    server {
        listen 80;
        server_name aeroinbox.qzz.io;

        location / {
            proxy_pass http://127.0.0.1:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support (for hot reloading / future features)
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
    ```

4.  **Test and reload Nginx:**
    ```bash
    sudo nginx -t
    sudo systemctl restart nginx
    ```

---

## Step 3: Install SSL Certificates with Let's Encrypt (Certbot)
To secure the application with HTTPS (`https://aeroinbox.qzz.io`), run the Certbot client on the host VM:

1.  **Install Certbot for Nginx:**
    ```bash
    sudo apt-get install -y certbot python3-certbot-nginx
    ```

2.  **Request and Install the Certificate:**
    *(Certbot will automatically verify your domain, request the certificate, and update the host Nginx configuration with SSL settings)*:
    ```bash
    sudo certbot --nginx -d aeroinbox.qzz.io
    ```
    *Follow the interactive prompts to complete the registration.*

---

## Step 4: Configure Google OAuth Consent Screen
Since Google OAuth restricts credentials redirect URIs to HTTPS domains for production, ensure your Google Cloud Console parameters are updated:

1.  Go to the **Google Cloud Console** -> **APIs & Services** -> **OAuth consent screen**.
2.  Go to **Credentials**, edit your Web Application client ID.
3.  Set the following parameters:
    *   **Authorized JavaScript origins:**
        `https://aeroinbox.qzz.io`
    *   **Authorized redirect URIs:**
        `https://aeroinbox.qzz.io/auth/callback`
4.  Save the changes (Google changes can take a couple of minutes to propagate).

---

## Step 5: Update `.env` and Rebuild Container Cluster
1.  Navigate to your repository root on the VM:
    ```bash
    cd /home/Akash/AI-Powered-Executive-Email-Assistant
    ```

2.  Ensure your `.env` matches the new secure URLs:
    ```env
    GOOGLE_REDIRECT_URI=https://aeroinbox.qzz.io/auth/callback
    FRONTEND_URL=https://aeroinbox.qzz.io
    ```

3.  Rebuild the frontend asset pack with the correct environment bindings and start the containers:
    ```bash
    docker compose build --build-arg VITE_API_URL=""
    docker compose up -d
    ```

---

## Troubleshooting commands on the VM:
*   Check running containers status:
    ```bash
    docker compose ps
    ```
*   View live logs for the orchestrator:
    ```bash
    docker compose logs -f api-service
    ```
*   View live logs for Nginx host proxy:
    ```bash
    sudo tail -f /var/log/nginx/error.log
    ```
