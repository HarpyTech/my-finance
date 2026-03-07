# Secret Management Guide

This guide explains how to manage secrets and credentials for the My Finance application using various credential managers instead of storing them in `.env` files.

## Overview

The application supports loading secrets from multiple sources in this priority order:

1. **`.env` file** (development)
2. **System credential managers** (recommended for local development)
3. **Environment variables** (CI/CD, containers)
4. **Docker secrets** (production with Docker Swarm)
5. **Default values** (fallback only)

## Quick Start

### Option 1: Use .env file (Development)

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env
```

### Option 2: Use Credential Manager (Recommended)

#### Windows (PowerShell)

```powershell
# Install credential manager module
Install-Module -Name CredentialManager -Force

# Store secrets
New-StoredCredential -Target 'MyFinanceApp-SecretKey' -UserName 'app' -Password 'your-secret-key-here' -Persist LocalMachine
New-StoredCredential -Target 'MyFinanceApp-DefaultPassword' -UserName 'app' -Password 'your-password-here' -Persist LocalMachine

# Load secrets and start application
. .\load-secrets.ps1
docker-compose up
```

#### macOS (Keychain)

```bash
# Store secrets in macOS Keychain
security add-generic-password -s 'MyFinanceApp' -a 'SecretKey' -w 'your-secret-key-here'
security add-generic-password -s 'MyFinanceApp' -a 'DefaultPassword' -w 'your-password-here'

# Load secrets and start application
source ./load-secrets.sh
docker-compose up
```

#### Linux (secret-tool)

```bash
# Install secret-tool (part of libsecret)
sudo apt-get install libsecret-tools  # Debian/Ubuntu
# sudo dnf install libsecret            # Fedora
# sudo pacman -S libsecret              # Arch

# Store secrets
secret-tool store --label='MyFinanceApp Secret Key' service MyFinanceApp account SecretKey
# Enter your secret when prompted

secret-tool store --label='MyFinanceApp Default Password' service MyFinanceApp account DefaultPassword
# Enter your password when prompted

# Load secrets and start application
source ./load-secrets.sh
docker-compose up
```

### Option 3: Use Environment Variables

```bash
# Set environment variables directly
export SECRET_KEY="your-secret-key-here"
export DEFAULT_LOGIN_PASSWORD="your-password-here"
export PROJECT_NAME="My Finance App"
export MONGODB_URI="mongodb://localhost:27017"

# Start application
docker-compose up
```

### Option 4: Docker Secrets (Production)

For production deployments with Docker Swarm:

```bash
# Create secrets
echo "your-secret-key" | docker secret create secret_key -
echo "your-password" | docker secret create default_password -

# Uncomment the secrets section in docker-compose.yml
# Then deploy with:
docker stack deploy -c docker-compose.yml my-finance
```

## Docker Compose Configuration

The `docker-compose.yml` file is configured to:

1. Attempt to load from `.env` file (silently ignores if missing)
2. Use environment variables with fallback defaults using `${VAR:-default}` syntax
3. Support Docker secrets for production deployments

Example environment variable with fallback:
```yaml
- SECRET_KEY=${SECRET_KEY:-your-super-secret-key-change-in-prod}
```

## Security Best Practices

### Development
- ✅ Use credential managers (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- ✅ Use `.env` file with proper `.gitignore` (already configured)
- ❌ Never commit `.env` to version control

### CI/CD
- ✅ Use GitHub Secrets, GitLab CI/CD variables, or Azure DevOps Secure Files
- ✅ Inject as environment variables during build/deploy
- ❌ Never log secret values

### Production
- ✅ Use Docker Secrets (Docker Swarm)
- ✅ Use Kubernetes Secrets (Kubernetes)
- ✅ Use cloud provider secret managers (Azure Key Vault, AWS Secrets Manager, Google Secret Manager)
- ✅ Rotate secrets regularly
- ❌ Never use default values in production

## Required Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | ⚠️ Change in prod | JWT signing key (min 32 chars) |
| `DEFAULT_LOGIN_PASSWORD` | Yes | `ChangeMe123!` | Default password for initial users |
| `PROJECT_NAME` | No | `My Finance App` | Application name |
| `BUILD_VERSION` | No | `dev` | Build/deployment version |
| `API_V1_STR` | No | `/api/v1` | API prefix |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Token expiration time |
| `MONGODB_URI` | No | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB` | No | `my_finance` | Database name |

## Troubleshooting

### "Failed to load configuration" error

Check that required variables are set:
```bash
# Windows
$env:SECRET_KEY
$env:DEFAULT_LOGIN_PASSWORD

# Linux/macOS
echo $SECRET_KEY
echo $DEFAULT_LOGIN_PASSWORD
```

### Docker Compose can't find variables

Ensure you've sourced the load script:
```bash
# Windows PowerShell
. .\load-secrets.ps1

# Linux/macOS
source ./load-secrets.sh
```

### Still seeing default values

Check the priority order - environment variables override `.env` file values.

## References

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Windows Credential Manager PowerShell Module](https://www.powershellgallery.com/packages/CredentialManager)
- [Linux Secret Service (libsecret)](https://wiki.gnome.org/Projects/Libsecret)
