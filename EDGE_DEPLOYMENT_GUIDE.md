# Edge Deployment Guide: Raspberry Pi 5 & Industrial Mini-PC

## 1. Overview
This guide provides step-by-step instructions for installing and running the **Edge AI Based Smart EV Charging Station Optimizer** on local edge hardware (e.g. Raspberry Pi 5 8GB, Intel NUC, or industrial edge IPC) operating offline without cloud connectivity dependencies.

## 2. Hardware Requirements
- **Target Hardware:** Raspberry Pi 5 (8GB RAM recommended) or x86/ARM64 Mini-PC (e.g. Intel N100 / Core i3)
- **Operating System:** Debian 12 / Ubuntu 22.04 LTS / Raspberry Pi OS 64-bit
- **Storage:** Minimum 16 GB NVMe SSD or high-end Class 10 A2 MicroSD
- **Power Supply:** Official 27W USB-C PD power supply (for Raspberry Pi 5)
- **Local Network:** Ethernet (recommended) or Wi-Fi for local dashboard access

## 3. Operating System Setup & Dependencies

```bash
# Update package repositories
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3, pip, venv, and git
sudo apt-get install -y python3 python3-pip python3-venv git curl

# Install Node.js 20 LTS (optional for building frontend on device)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## 4. Application Installation

```bash
# Clone the project repository
sudo git clone https://github.com/project/edge-ai-ev-optimizer.git /opt/edge-ev-hub
cd /opt/edge-ev-hub

# Create isolated Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Generate benchmark datasets & train edge model
python backend/ml/generate_synthetic_data.py --days 90
python backend/ml/train_model.py
```

## 5. Systemd Service Configuration (Auto-Start on Boot)

Create systemd service file `/etc/systemd/system/edge-ev-optimizer.service`:

```ini
[Unit]
Description=Edge AI Smart EV Charging Station Optimizer Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/edge-ev-hub/backend
ExecStart=/opt/edge-ev-hub/venv/bin/python run_server.py
Restart=always
RestartSec=5
Environment=HOST=0.0.0.0
Environment=PORT=8000
Environment=EDGE_MODE=true
Environment=DEMO_MODE=true

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable edge-ev-optimizer.service
sudo systemctl start edge-ev-optimizer.service
sudo systemctl status edge-ev-optimizer.service
```

## 6. Frontend Serving via Nginx

```bash
# Build frontend bundle
cd /opt/edge-ev-hub/frontend
npm install
npm run build

# Install Nginx
sudo apt-get install -y nginx

# Configure site
sudo tee /etc/nginx/sites-available/edge-ev-hub << 'EOF'
server {
    listen 80;
    server_name _;

    root /opt/edge-ev-hub/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }
}
EOF

# Activate configuration
sudo ln -sf /etc/nginx/sites-available/edge-ev-hub /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

## 7. Verification & Offline Testing

```bash
# Test local backend health endpoint
curl http://localhost:8000/health

# Access dashboard from any laptop/tablet on the local network:
# Open browser at: http://<raspberry-pi-ip>/
```
