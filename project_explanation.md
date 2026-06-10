# AeroInbox: Beginner-Friendly Project Guide

This guide explains how **AeroInbox (AI-Powered Executive Email Assistant)** works, the microservices used, how routing operates, and how the cloud infrastructure keeps everything secure.

---

## 1. What is AeroInbox?

AeroInbox is an AI-powered assistant designed for busy users (such as CEOs, founders, and managers) who receive hundreds of emails every day. 

It connects securely to a user's Gmail, fetches unread emails, analyzes their content using Artificial Intelligence, scores them using custom business rules, automatically extracts calendar meetings, and organizes them into an executive dashboard sorted by priority.

---

## 2. The Microservices (The Build Blocks)

Instead of one giant program, the application is divided into **six independent microservices**. This architecture makes the system modular, stable, and easy to scale.

| Service Name | Technology | Primary Role |
| :--- | :--- | :--- |
| **Frontend Client** | React, Vite, Tailwind CSS | The visual web interface you interact with in the browser. |
| **API Service (Gateway)** | FastAPI (Python) | The central receptionist that authorizes users, manages sessions, and routes requests to other services. |
| **Redis Session Cache** | Redis (Sidecar) | A super-fast, short-term memory database that caches your login session so you stay logged in. |
| **Gmail Service** | FastAPI (Python) | Speaks directly with Google's APIs to read unread emails and spam messages. |
| **AI Service** | FastAPI (Python) | The cognitive brain. It summarizes emails, extracts deadlines, and detects meeting details using AI (Gemini or OpenAI). |
| **Rule Engine** | FastAPI (Python) | Evaluates sender domain boosts, VIP status, and custom user-defined keywords. |
| **Meeting Service** | FastAPI (Python) | Parses calendar files (.ics) and meeting links (Zoom/Meet/Teams) to populate the Calendar view. |

---

## 3. How Data Flows (The Routing & Communication)

Here is exactly how the microservices communicate with one another during key user actions.

### A. The Login Flow (Connecting Google Accounts)
To secure your credentials, the application uses a **stateless OAuth 2.0 flow** that hides your credentials from the browser:

```
[User Browser]
      │
      ▼ (1. Click Connect)
[Frontend client] ──(2. Redirects to /auth/login)──> [API Service (Gateway)]
                                                              │
                                                              ▼ (3. Redirects to Google)
[Google Consent Page] <──(4. Users grants permissions)── [User Browser]
      │
      ▼ (5. Google redirects with code)
[API Service (Gateway) /auth/callback]
      │
      ▼ (6. Exchanges code for Access & Refresh Tokens)
[Google Auth Servers]
      │
      ▼ (7. Stores tokens securely in Redis cache)
[Redis Session Cache]
      │
      ▼ (8. Redirects browser to Frontend with unique Session ID)
[Frontend Client] ──(9. Dashboard Loaded!)
```

---

### B. The Sync & Prioritization Flow (Dashboard Load)
When you load the dashboard, the Gateway orchestrates parallel workflows to score and categorize emails:

1. **Request**: The website calls the API Gateway: `GET /emails/unread` with your unique Session ID.
2. **Authorization**: The Gateway validates the Session ID and retrieves your Google Access Token from the **Redis Cache**.
3. **Orchestration**: The Gateway triggers the following tasks in parallel:
   * It tells the **Gmail Service** to fetch your unread messages (Inbox and Spam).
   * It tells the **Rule Engine** to fetch your custom scoring rules.
4. **Calculations**:
   * For every email, the Gateway checks the sender and subject line against the **Rule Engine** to get a static rule score.
   * At the same time, the Gateway sends the text of the email to the **AI Service** to evaluate urgency (0-100), summarize content, and scan for deadlines.
5. **Scoring**:
   The Gateway combines these metrics using a hybrid score formula:
   $$\text{Final Score} = \text{AI Urgency Score (0-100)} + \text{Rule Engine Boost}$$
   Based on the score, emails are grouped into priority lists:
   * **90+**: Critical (Red badge)
   * **70-89**: High (Orange badge)
   * **40-69**: Medium (Yellow badge)
   * **Below 40**: Low (Gray badge)
6. **Delivery**: The prioritized, summarized email list is returned to the Frontend dashboard.
7. **Background Meeting Scan**: While you read your emails, the Gateway offloads the emails to the **Meeting Service** in the background. The Meeting Service parses invitation files (.ics) and platform URLs (Zoom/Meet/Teams), updates the database, and updates your dashboard calendar tab.

---

## 4. The Cloud Architecture (Where it Runs in Azure)

To keep the application secure and compliant with enterprise standards, the resources are deployed inside an isolated **Microsoft Azure Virtual Network (VNet)**:

```
   Internet Traffic
          │
          ▼ (HTTPS)
   +-------------------------------------------+
   |   Azure Application Gateway / WAF v2      | <--- Protects application from malicious attacks
   +------------------+------------------------+
                      │ (Private Routing)
                      ▼
   +-------------------------------------------+
   |   Azure Container Apps Environment        | <--- Runs the Docker microservice containers
   |                                           |
   |  +-------------+     +-----------------+  |
   |  | api-service | <-> | Redis (Sidecar) |  | <--- Localhost communication for session caching
   |  +------+------+     +-----------------+  |
   |         │                                 |
   |         ▼ (Internal private DNS)          |
   |   [Microservices: Gmail, AI, Rules, Meet] |
   +------------------+------------------------+
                      │ (Secure Entra ID Access)
                      ▼
   +-------------------------------------------+
   |   Azure PostgreSQL Database               | <--- Stores rule engine tables and calendar tables
   +-------------------------------------------+
```

### Cloud Security Features:
* **Private Network Isolation**: None of the microservices are exposed to the public internet except the Gateway. They communicate internally inside the VNet.
* **Key Vault Integration**: Password files are not hardcoded. The microservices dynamically fetch client credentials and API keys from **Azure Key Vault** using Private Endpoints.
* **Entra ID Managed Identities**: The microservices authenticate to the PostgreSQL Database using Azure AD managed identity tokens, eliminating database passwords from configurations.
