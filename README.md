# My Finance

A personal finance management web app to track income, expenses, budgets and visualize financial health.

## 🚀 Features

✔️ Add and manage multiple accounts  
✔️ Track income and expenses  
✔️ Categorize transactions  
✔️ Budget creation & alerts  
✔️ Financial summary dashboard  
✔️ Export reports (CSV / Excel)  
✔️ Optional authentication (if implemented)  

---

## 📦 Tech Stack

This project is built with:

- **Python** – backend logic  
- **(Flask / Django / FastAPI)** – web framework *(replace with whichever your app uses)*  
- **HTML, CSS, JavaScript** – frontend  
- **SQLite / PostgreSQL** – database *(adjust accordingly)*  
- **Docker** – containerization  
- **docker-compose** – multi-container setup  

---

## 🧩 Project Structure

```

my-finance/
├── app/                     # Application source code
├── Dockerfile               # Docker container specification
├── docker-compose.yml       # Compose services
├── requirements.txt         # Python dependencies
├── .gitignore
├── LICENSE
└── README.md

````

---

## 📥 Setup & Installation

### 🛠 Local Development

1. **Clone the repository**

```bash
git clone https://github.com/HarpyTech/my-finance.git
cd my-finance
````

2. **Create a Python virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Update the `.env` file with your actual configuration. See [SECRET-MANAGEMENT.md](./SECRET-MANAGEMENT.md) for secure credential management options.

**Required Variables:**
- `SECRET_KEY` - JWT signing key (generate with `openssl rand -hex 32`)
- `MONGODB_URI` - MongoDB connection string
- `DEFAULT_LOGIN_PASSWORD` - Default user password
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token expiration time
- `DEFAULT_USER_EMAIL` - Default user email
- `DEFAULT_USER_NAME` - Default user name

For production deployments, use credential managers instead of `.env` files. See [🔐 Secret Management](#-secret-management) below.

5. **Run the app**

```bash
uvicorn app.main:app --reload
```

Your app should now be running at: **[http://localhost:8000](http://localhost:8000)** *(or configured port)*

---

## 🐳 Using Docker

If you prefer containerized setup:

```bash
docker build -t my-finance:latest .
docker-compose up
```

**Environment Configuration:**
- Docker Compose automatically loads from `.env` file if present
- If `.env` is not found, it falls back to default values specified in `docker-compose.yml`
- For production, use credential managers (see [🔐 Secret Management](#-secret-management))

**Using Credential Managers:**

Windows (PowerShell):
```powershell
.\load-secrets.ps1
docker-compose up
```

Linux/macOS (Bash):
```bash
./load-secrets.sh
docker-compose up
```

The application will be available at **[http://localhost:8000](http://localhost:8000)** *(if exposed via compose)*

---

## 🔐 Secret Management

For secure credential management in production environments, this project supports multiple approaches:

1. **Credential Managers** (Recommended for Production)
   - Windows: Credential Manager
   - macOS: Keychain
   - Linux: Secret Service (secret-tool)

2. **Azure Key Vault** (Enterprise)

3. **Docker Secrets** (Container Orchestration)

4. **Environment Variables** (Development Only)

**Quick Start:**

Windows:
```powershell
# Load secrets from Windows Credential Manager
.\load-secrets.ps1
```

Linux/macOS:
```bash
# Load secrets from system credential manager
./load-secrets.sh
```

**Full Documentation:**  
See [SECRET-MANAGEMENT.md](./SECRET-MANAGEMENT.md) for comprehensive setup instructions, examples, and best practices for each platform.

---

## ☁️ Auto Deploy to Google Cloud Run (GitHub Actions)

This repository includes a workflow at `.github/workflows/deploy-cloud-run.yml`.

It deploys automatically when code is pushed to `main` (and can also be run manually with `workflow_dispatch`).

### 1) Add Required GitHub Secrets

Add these in GitHub: **Settings -> Secrets and variables -> Actions -> Secrets**.

**Authentication Secrets (choose one)**

Google recommends [Workload Identity Federation (WIF)](https://cloud.google.com/iam/docs/workload-identity-federation) over long-lived service account keys to eliminate key leakage and rotation risk.

*Option A – Workload Identity Federation (recommended):*
- `GCP_WORKLOAD_IDENTITY_PROVIDER` = fully qualified WIF provider resource name  
  (example: `projects/123456789/locations/global/workloadIdentityPools/my-pool/providers/my-provider`)
- `GCP_SERVICE_ACCOUNT` = service account email to impersonate  
  (example: `my-sa@my-project.iam.gserviceaccount.com`)

*Option B – Service Account Key (fallback):*
- `GCP_SA_KEY` = full JSON of your GCP service account key  
  *(only used when `GCP_WORKLOAD_IDENTITY_PROVIDER` is not set)*

**Infrastructure Secrets**
- `GCP_PROJECT_ID` = your Google Cloud project ID
- `GCP_REGION` = Cloud Run region (example: `us-central1`)
- `CLOUD_RUN_SERVICE` = Cloud Run service name

**Application Runtime Secrets**
- `APP_SECRET_KEY` = JWT secret key (minimum 32 characters)
- `APP_DEFAULT_LOGIN_PASSWORD` = initial/default login password
- `APP_MONGODB_URI` = MongoDB connection string

### 2) Optional GitHub Secrets (App Overrides)

If omitted, app defaults are used where defaults exist.

- `APP_PROJECT_NAME`
- `APP_API_V1_STR`
- `APP_ACCESS_TOKEN_EXPIRE_MINUTES`
- `APP_ALGORITHM`
- `APP_MONGODB_DB`
- `APP_CORS_ORIGINS` (must be JSON array string, example: `["https://your-frontend-domain.com"]`)
- `CLOUD_RUN_ALLOW_UNAUTHENTICATED` = set to `true` to make the Cloud Run service publicly accessible  
  ⚠️ **Security note:** By default the service is deployed without `--allow-unauthenticated`, meaning only authenticated callers (via IAM) can invoke it. Set this secret to `true` only if you intentionally want the service to be publicly reachable without authentication. To further restrict access after deployment, configure [Cloud Run ingress settings](https://cloud.google.com/run/docs/securing/ingress) or [IAM policies](https://cloud.google.com/run/docs/securing/managing-access).

### 3) Push to `main`

After setting the secrets, push to `main` and the workflow will build and deploy to Cloud Run.

---

## 🤝 Contributing

We welcome contributions! To contribute:

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/xyz`)
3. Commit your changes (`git commit -m "Add xyz"`)
4. Push to your fork (`git push origin feature/xyz`)
5. Open a Pull Request

Please follow the code style and add tests where applicable.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

---

## 📞 Contact

Created by **HarpyTech** – feel free to reach out with questions or suggestions!

[1] [https://github.com/HarpyTech/my-finance](https://github.com/HarpyTech/my-finance) "GitHub - HarpyTech/my-finance"
