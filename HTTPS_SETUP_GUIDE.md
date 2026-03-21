# 🔒 HTTPS Setup Guide — Financial Planning Suite on TerraMaster F4-223

This guide walks you through getting your financial app running at a secure URL like:
```
https://finance.yourdomain.com
```

All traffic is encrypted. Free SSL certificates auto-renew. Your friends just need the URL and a login.

---

## Overview: What We're Building

```
Friends' browsers
       │
       ▼ (HTTPS, port 443)
┌──────────────────────────────────┐
│  Your Router                     │
│  Port 80  → NAS IP:80            │
│  Port 443 → NAS IP:443           │
└──────────┬───────────────────────┘
           │
┌──────────▼───────────────────────┐
│  TerraMaster NAS (Docker)        │
│                                  │
│  ┌─────────────────────────┐     │
│  │ Nginx Proxy Manager     │     │
│  │ (ports 80, 443, 81)     │     │
│  │ • SSL termination       │     │
│  │ • Let's Encrypt certs   │     │
│  │ • HTTPS → HTTP proxy    │     │
│  └────────┬────────────────┘     │
│           │ (internal, port 8501)│
│  ┌────────▼────────────────┐     │
│  │ Financial Planner App   │     │
│  │ (Streamlit)             │     │
│  └─────────────────────────┘     │
│                                  │
└──────────────────────────────────┘
```

---

## Phase 1: Get It Running Locally First (15 minutes)

Before touching domains or SSL, let's confirm everything works on your home network.

### Step 1.1: Transfer files to NAS

```bash
# From your PC, copy files to your NAS
scp -r ./* admin@tm223_nas:/Volume1/docker/financial-planner/

# Or use SMB: copy the folder to your NAS shared folder via File Explorer
```

Your folder should look like:
```
/Volume1/docker/financial-planner/
├── Dockerfile
├── docker-compose.yml          ← HTTPS version (for later)
├── docker-compose-local.yml    ← Local version (start here)
├── requirements.txt
├── streamlit_config.toml
├── FinancialApp_V14.py
└── Launcher.py
```

### Step 1.2: Build and test locally

```bash
# SSH into your NAS
ssh admin@tm223_nas

cd /Volume1/docker/financial-planner

# Build and start LOCAL version first (no proxy, just the app)
docker-compose -f docker-compose-local.yml build
docker-compose -f docker-compose-local.yml up -d

# Check it's running
docker-compose -f docker-compose-local.yml ps
docker-compose -f docker-compose-local.yml logs -f
```

### Step 1.3: Test in browser

Open `http://tm223_nas:8501` (or `http://YOUR_NAS_IP:8501`).

You should see the login page. Create an account, make sure everything works.

### Step 1.4: Stop the local version

```bash
docker-compose -f docker-compose-local.yml down
```

---

## Phase 2: Get a Domain Name (10 minutes)

You need a domain that points to your home's public IP. Two options:

### Option A: Buy a cheap domain (~$1-10/year) ⭐ RECOMMENDED

Providers like **Namecheap**, **Porkbun**, or **Cloudflare Registrar** sell `.xyz`, `.site`, or `.click` domains for as little as $1/year. Some `.com` domains are ~$10/year.

Example: `smithfinance.xyz` for ~$1/year.

After purchasing:
1. Go to the domain's DNS settings
2. Create an **A record**: `finance` → `YOUR_PUBLIC_IP`
   - Name: `finance` (or `@` for root domain)
   - Type: `A`
   - Value: Your public IP (find it at https://whatismyip.com)
   - TTL: Auto or 300

This makes `finance.yourdomain.xyz` point to your home IP.

### Option B: Free Dynamic DNS (DuckDNS)

If you don't want to buy a domain:

1. Go to https://www.duckdns.org/
2. Sign in with Google/GitHub
3. Create a subdomain, e.g., `smithfinance.duckdns.org`
4. Point it to your public IP

DuckDNS is free and works with Let's Encrypt.

### Important: Dynamic IP?

Most home internet connections have a dynamic public IP that changes occasionally. Options:
- **Check quarterly**: Most ISPs don't change it often
- **DuckDNS**: Has a cron script to auto-update
- **Namecheap**: Offers a Dynamic DNS client
- **Your router**: Many routers have built-in DDNS support

---

## Phase 3: Configure Your Router (5 minutes)

Forward these ports from your router to your NAS's internal IP:

| External Port | Internal IP     | Internal Port | Protocol |
|--------------|-----------------|---------------|----------|
| 80           | (Your NAS IP)   | 80            | TCP      |
| 443          | (Your NAS IP)   | 443           | TCP      |

⚠️ Do **NOT** forward port 81 — that's the Nginx Proxy Manager admin panel and should only be accessible on your local network.

How to find your NAS IP: Look at your NAS dashboard — it's displayed in the Network section, or check your router's connected devices list.

How to set up port forwarding (varies by router brand):
- **Netgear**: Advanced → Advanced Setup → Port Forwarding
- **TP-Link**: Advanced → NAT Forwarding → Port Forwarding  
- **ASUS**: WAN → Virtual Server / Port Forwarding
- **Xfinity/Comcast**: Gateway → Advanced → Port Forwarding

---

## Phase 4: Start the HTTPS Stack (10 minutes)

### Step 4.1: Start the full stack

```bash
ssh admin@tm223_nas
cd /Volume1/docker/financial-planner

# Start both containers (Nginx Proxy Manager + Financial App)
docker-compose build
docker-compose up -d

# Verify both are running
docker-compose ps
```

You should see two containers running: `nginx-proxy` and `financial-planner`.

### Step 4.2: Log into Nginx Proxy Manager

Open in your browser (LOCAL network only):
```
http://tm223_nas:81
```

Default login credentials:
```
Email:    admin@example.com
Password: changeme
```

You'll be prompted to change these immediately. Set a strong password.

### Step 4.3: Create SSL Certificate

In the Nginx Proxy Manager admin panel:

1. Click **SSL Certificates** in the top menu
2. Click **Add SSL Certificate** → **Let's Encrypt**
3. Fill in:
   - **Domain Names**: `finance.yourdomain.xyz` (your actual domain)
   - **Email Address**: Your real email (for Let's Encrypt notifications)
   - Toggle **"I Agree to the Let's Encrypt Terms of Service"**
4. Click **Save**

Wait 15-30 seconds. If successful, you'll see a green certificate entry. If it fails, double-check that ports 80/443 are forwarded correctly and your domain points to your public IP.

### Step 4.4: Create Proxy Host

1. Click **Hosts** → **Proxy Hosts** in the top menu
2. Click **Add Proxy Host**
3. **Details tab**:
   - **Domain Names**: `finance.yourdomain.xyz`
   - **Scheme**: `http`
   - **Forward Hostname / IP**: `financial-planner`  (the Docker container name)
   - **Forward Port**: `8501`
   - Toggle **"Block Common Exploits"**: ON
   - Toggle **"Websockets Support"**: ON  (important for Streamlit!)
4. **SSL tab**:
   - **SSL Certificate**: Select the one you just created
   - Toggle **"Force SSL"**: ON  (redirects HTTP → HTTPS)
   - Toggle **"HTTP/2 Support"**: ON
5. **Advanced tab** — paste this to handle Streamlit's WebSocket connections:
   ```
   proxy_read_timeout 86400s;
   proxy_send_timeout 86400s;
   proxy_set_header X-Forwarded-Proto $scheme;
   ```
6. Click **Save**

### Step 4.5: Test it!

Open in any browser:
```
https://finance.yourdomain.xyz
```

You should see:
- 🔒 A padlock icon in the browser address bar
- The Financial Planning Suite login page
- Certificate issued by Let's Encrypt

---

## Phase 5: Share with Friends

Send your friends this message:

> Hey! I set up a financial planning tool for us. 
> Go to: https://finance.yourdomain.xyz
> 
> 1. Click "Register" and create an account
> 2. Under "Household Setup", choose "Create new household"
> 3. Note your household code and share it with your partner
> 4. Your partner registers and enters the code to join your household
> 5. You'll both see the same financial plan!

Each couple gets their own isolated household. Your data, their data — completely separate.

---

## Maintenance & Troubleshooting

### SSL Certificate Renewal
Let's Encrypt certificates expire every 90 days. Nginx Proxy Manager **auto-renews** them. No action needed.

### Updating the App
```bash
cd /Volume1/docker/financial-planner

# Replace FinancialApp_V14.py with the new version, then:
docker-compose build --no-cache
docker-compose up -d
```

### Checking Logs
```bash
# Financial app logs
docker logs financial-planner -f

# Nginx Proxy Manager logs
docker logs nginx-proxy -f
```

### Common Issues

| Problem | Fix |
|---------|-----|
| Can't reach the site from outside | Check port forwarding (80, 443). Test at https://www.yougetsignal.com/tools/open-ports/ |
| SSL certificate won't generate | Ensure domain points to your public IP. Ensure port 80 is forwarded. Wait 5 min for DNS propagation. |
| "502 Bad Gateway" | The financial planner container might not be running: `docker-compose ps` |
| Site loads but WebSocket errors | Make sure "Websockets Support" is ON in the proxy host, and add the Advanced config above |
| Site works locally but not externally | Port forwarding issue. Check router config. |
| NAS IP changed | Update port forwarding rules with new NAS IP, or set a static IP for your NAS |
| Public IP changed | Update your domain's A record with the new IP |
| NPM admin panel won't load | Access only via LOCAL IP: `http://NAS_IP:81` — never from outside |

### Backup Everything
```bash
cd /Volume1/docker/financial-planner

# Backup user data + nginx config
tar -czf backup-$(date +%Y%m%d).tar.gz app-data/ nginx-data/ nginx-letsencrypt/
```

---

## Security Checklist

- [x] HTTPS encryption via Let's Encrypt (free, auto-renewing)
- [x] Passwords hashed with PBKDF2-SHA256 (100,000 iterations)
- [x] Each household's data isolated in separate files
- [x] NPM admin panel (port 81) NOT forwarded to internet
- [x] "Block Common Exploits" enabled in proxy host
- [x] "Force SSL" enabled (no unencrypted access)
- [ ] Optional: Set a static IP for your NAS in router DHCP settings
- [ ] Optional: Enable "Access Lists" in NPM to restrict by IP/country
- [ ] Optional: Set up DuckDNS cron job if your public IP changes frequently
