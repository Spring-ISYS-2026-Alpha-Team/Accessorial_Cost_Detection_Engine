# PACE Deployment Briefing — Oracle Cloud Server (daxori.com)

## What Is PACE?

PACE (Predictive Accessorial Cost Detection Engine) is a Streamlit web application that predicts accessorial charges and carrier risk scores using a custom FT-Transformer model. It is built by a university team and is being deployed to Oracle Cloud at `pace.daxori.com`.

---

## Server Details

| Property | Value |
|---|---|
| Host | `ubuntu@131.186.6.189` |
| OS | Ubuntu 22.04 |
| Domain | `daxori.com` (target subdomain: `pace.daxori.com`) |
| Docker | Installed and running |
| Nginx | Not installed yet |
| Python venv | `/home/ubuntu/PACE/venv` |

---

## What Has Already Been Done

1. Removed previous app (`/home/ubuntu/WebApp1.0/Geo`) — a .NET zip code lookup app that was running on port 8080
2. Cloned the PACE repo from GitHub:
   ```
   https://github.com/Spring-ISYS-2026-Alpha-Team/Accessorial_Cost_Detection_Engine.git
   ```
   Cloned to `/home/ubuntu/PACE/`
3. Created Python virtual environment at `/home/ubuntu/PACE/venv`
4. Installed all Python dependencies via `pip install -r requirements.txt`
5. Installed Claude Code CLI (`@anthropic-ai/claude-code`) globally via npm

---

## What Still Needs To Be Done (In Order)

### Step 1 — Transfer Model Files
The app cannot run without these two files, which are NOT in the GitHub repo:
- `/home/ubuntu/PACE/models/pace_transformer_weights.pt` — PyTorch FT-Transformer weights
- `/home/ubuntu/PACE/models/artifacts.pkl` — preprocessing artifacts (encoder, scaler, column metadata)

These need to be copied from wherever they are currently stored (GPU cluster, shared drive, etc.) to the server. Create the directory first:
```bash
mkdir -p /home/ubuntu/PACE/models
```

Transfer options:
- `scp <source> ubuntu@131.186.6.189:/home/ubuntu/PACE/models/`
- Upload via SFTP
- Download from a shared URL if hosted somewhere

### Step 2 — Configure Environment Variables
Create a `.env` file at `/home/ubuntu/PACE/.env` with the following (fill in real values):
```env
PACE_ENV=production
FRED_API_KEY=a9894999d90e9f5d08ebd26fe633927f
EIA_API_KEY=m0L8lnt78ncuKxNy9XaLTU0RqyMeMhchq9wDyLb2
OWM_API_KEY=d4426e1b18fe884f2fc25089952d8d3c
```
Note: These keys are currently hardcoded in `pipeline/config.py`. The app will work without the `.env` file but production API enrichment requires `PACE_ENV=production`.

### Step 3 — Test the App Locally on the Server
```bash
cd /home/ubuntu/PACE
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```
Verify it starts without errors before proceeding.

### Step 4 — Create a systemd Service
So the app runs persistently and restarts on reboot, create `/etc/systemd/system/pace.service`:

```ini
[Unit]
Description=PACE Streamlit App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/PACE
Environment="PATH=/home/ubuntu/PACE/venv/bin"
EnvironmentFile=/home/ubuntu/PACE/.env
ExecStart=/home/ubuntu/PACE/venv/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pace
sudo systemctl start pace
sudo systemctl status pace
```

### Step 5 — Install and Configure Nginx
```bash
sudo apt update && sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

Create `/etc/nginx/sites-available/pace`:
```nginx
server {
    listen 80;
    server_name pace.daxori.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

Enable it:
```bash
sudo ln -s /etc/nginx/sites-available/pace /etc/nginx/sites-enabled/pace
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6 — Open Firewall Ports
Oracle Cloud has a firewall that blocks ports by default. Open ports 80 and 443:
```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```
Also open ports 80 and 443 in the **OCI Console** under:
`Networking → Virtual Cloud Networks → your VCN → Security Lists → Ingress Rules`

### Step 7 — Add DNS Record
In whatever DNS provider manages `daxori.com`, add:
- **Type:** A
- **Name:** `pace`
- **Value:** `131.186.6.189`
- **TTL:** 300

### Step 8 — SSL Certificate (HTTPS)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d pace.daxori.com
```
Follow the prompts. Certbot will auto-configure Nginx for HTTPS and set up auto-renewal.

---

## App Architecture Summary

- **Entry point:** `app.py` → Streamlit multi-page app
- **Inference engine:** `pipeline/inference.py` → `PACEInference` class (singleton)
- **Model:** FT-Transformer with dual heads (regression + classification)
  - 152 input features (97 continuous, 55 categorical)
  - Outputs: risk score (0-100), risk label, charge type (6 classes)
- **External APIs called during inference** (production mode only):
  - FMCSA — carrier safety data
  - FRED — economic indicators
  - EIA — diesel prices
  - OpenWeatherMap — weather
  - National Weather Service — alerts
  - Census Bureau — facility density
  - BTS — freight indicators
- **Database:** Azure SQL Edge running in Docker on port 1433 (already running, do not touch)

---

## Notes

- The Azure SQL Edge Docker container (`sqlserver`) is already running on port 1433 — leave it alone
- The model runs on CPU fine — no GPU needed for inference at this model size
- Streamlit runs on port 8501 internally; Nginx proxies it externally on 80/443
- The repo is at `/home/ubuntu/PACE/` and the venv is at `/home/ubuntu/PACE/venv`
