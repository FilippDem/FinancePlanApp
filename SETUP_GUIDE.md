# 🚀 Financial Planning Suite V14 — TerraMaster NAS Deployment Guide

## What's New in V14

### Bug Fixes
1. **SS Income Variability Fix** — Monte Carlo variability now only applies to employment income, not Social Security (SS payments are fixed government checks)
2. **maintenance_rate Now Active** — House `maintenance_rate` (percentage of home value) is now used in simulation alongside flat `upkeep_costs`
3. **Healthcare Inflation Fix** — Children's Healthcare expenses now use the separate `healthcare_inflation_rate` from your economic scenario instead of general inflation

### New Features
4. **User Authentication** — Login/registration with password hashing (PBKDF2-SHA256)
5. **Household Profiles** — Couples share a household code; both partners see the same financial plan
6. **Persistent Storage** — Plans auto-save to disk (survives Docker restarts)
7. **Users Tab** — Manage profile, view household members, share invite code, change password
8. **Sidebar Quick Save/Logout** — One-click save and logout from any tab

---

## Deployment on Your TerraMaster F4-223

### Prerequisites
Your NAS has everything needed:
- ✅ Intel Celeron N4505 (x86_64)
- ✅ 32GB RAM
- ✅ Docker Engine installed
- ✅ TOS 5.1

### Step 1: Transfer Files to NAS

Create a folder on your NAS for the app. You can use the TOS File Manager or SSH:

```bash
# SSH into your NAS (replace with your NAS IP)
ssh admin@tm223_nas

# Create app directory
mkdir -p /Volume1/docker/financial-planner
cd /Volume1/docker/financial-planner
```

Transfer these files into that folder:
```
financial-planner/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── streamlit_config.toml
├── FinancialApp_V14.py
└── data/                    ← Created automatically
    ├── users.json
    └── households/
```

You can transfer files via:
- **TOS File Manager**: Upload to a shared folder, then SSH to move them
- **SCP from your PC**: `scp -r ./docker-deploy/* admin@tm223_nas:/Volume1/docker/financial-planner/`
- **SMB/CIFS**: Map the NAS share on your PC and copy directly

### Step 2: Build and Start the Container

SSH into your NAS and run:

```bash
cd /Volume1/docker/financial-planner

# Build the Docker image (takes 2-3 minutes first time)
docker-compose build

# Start the container
docker-compose up -d

# Check it's running
docker-compose ps

# View logs if needed
docker-compose logs -f
```

### Step 3: Verify It Works

Open a browser on your local network and go to:
```
http://tm223_nas:8501
```
Or use your NAS's IP address:
```
http://192.168.x.x:8501
```

You should see the login/registration page.

### Step 4: Create Your Account

1. First user to register creates the household
2. Note the **household code** displayed after registration
3. Share this code with your partner
4. Your partner registers and enters the household code to join

---

## Letting Friends Access from Outside Your Network

When you're ready, you have several options:

### Option A: Port Forwarding (Simplest)
1. Log into your router admin panel
2. Forward external port 8501 → NAS IP:8501 (TCP)
3. Friends access: `http://YOUR_PUBLIC_IP:8501`
4. Find your public IP at https://whatismyip.com

⚠️ **Security note**: This exposes the app to the internet. The built-in password protection helps, but consider Option B or C for better security.

### Option B: Reverse Proxy with HTTPS (Recommended)
If you have a domain name, use Nginx Proxy Manager (also runs in Docker):

```yaml
# Add to docker-compose.yml
  nginx-proxy:
    image: jc21/nginx-proxy-manager:latest
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
      - "81:81"
    volumes:
      - ./nginx/data:/data
      - ./nginx/letsencrypt:/etc/letsencrypt
    restart: unless-stopped
```

Then configure your domain → NAS IP with free Let's Encrypt SSL.

### Option C: Tailscale VPN (Most Secure)
1. Install Tailscale on your NAS and friends' devices
2. Everyone joins your Tailscale network
3. Access via Tailscale IP — no port forwarding needed
4. Fully encrypted, zero configuration networking

---

## Managing the App

### Common Commands

```bash
# Stop the app
docker-compose down

# Restart the app
docker-compose restart

# Update the app (after replacing FinancialApp_V14.py)
docker-compose build --no-cache
docker-compose up -d

# View logs
docker-compose logs -f financial-planner

# Check resource usage
docker stats financial-planner
```

### Backup User Data

All user data lives in the `./data` folder:
```bash
# Backup
cp -r ./data ./data-backup-$(date +%Y%m%d)

# Restore
cp -r ./data-backup-YYYYMMDD/* ./data/
docker-compose restart
```

### Adding New Users

New users self-register through the web interface. To join an existing household, they need the household code from an existing member (visible in the Users tab).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't reach http://NAS:8501 | Check: `docker-compose ps` — is the container running? |
| Container keeps restarting | Check: `docker-compose logs` for error messages |
| "Permission denied" on data folder | Run: `chmod -R 777 ./data` |
| Slow Monte Carlo simulations | Reduce simulations to 500 or reduce years to 20 |
| Users can't see each other's changes | Click "Save Plan to Household" then other user clicks "Load Plan from Household" |
| Forgot password | Delete the user entry from `./data/users.json` and re-register |

---

## Architecture

```
┌─────────────────────────────┐
│   Your Friends' Browsers    │
│   http://NAS_IP:8501        │
└──────────┬──────────────────┘
           │
┌──────────▼──────────────────┐
│   TerraMaster F4-223 NAS    │
│   Docker Container          │
│   ┌───────────────────┐     │
│   │ Streamlit Server  │     │
│   │ (Port 8501)       │     │
│   └────────┬──────────┘     │
│            │                │
│   ┌────────▼──────────┐     │
│   │ /app/data/        │     │
│   │ ├── users.json    │ ◄── Persisted on NAS Volume
│   │ └── households/   │     │
│   │     ├── abc123.json│    │
│   │     └── def456.json│    │
│   └───────────────────┘     │
└─────────────────────────────┘
```

Each household gets its own JSON file. Multiple households are fully isolated — friends can't see each other's financial data.
