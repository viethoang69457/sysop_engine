# 🚀 SysOps Engine

**Agentless Linux Automation Management**

> A lightweight, agentless Linux infrastructure automation suite: collects core system metrics, detects SSH security threats from system logs, manages automated backups, and provides a web dashboard with RESTful API endpoints.

---

## 🛠 Architectural Overview: 4-Tier Layered Design

`SysOps Engine` follows a strict **4-Tier Layered Architecture**, separating the presentation UI from the control plane, orchestration logic, and target infrastructure.

```text
┌─────────────────────────────────────────────────────────┐
│                 1. PRESENTATION LAYER                   │
│         TailwindCSS | Chart.js | Sync Polling (5s)      │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 2. CONTROL PLANE CORE                   │
│     FastAPI RESTful | Uvicorn (2 Workers) | Systemd     │
│          Background Tasks (0.1s Execution Rate)         │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│              3. ORCHESTRATION & STORAGE                 │
│                                                         │
│  [ Master Orchestrator ]       [ Backup Vault Engine ]  │
│  (sysop_orchestrator.py)       (backup_engine.py)       │
│             │                           │               │
│             └─────────────┬─────────────┘               │
│                           ▼                             │
│               [ SQLite Database (3NF) ]                 │
│           (sysop_engine.db) + Telegram Alerts           │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│               4. TARGET INFRASTRUCTURE                  │
│    Ubuntu Server 22.04 LTS (Strict Agentless Mode)      │
│   Ed25519 SSH Keys | Password Auth Disabled | No Root   │
└─────────────────────────────────────────────────────────┘
```

---

## ⚡ Core Features

- **Web Dashboard & REST API**: Real-time SLA/uptime monitoring (Chart.js) powered by a centralized FastAPI gateway.
- **Agentless Telemetry Collection**: Gathers node metrics (CPU, RAM, Disk, latency) with zero agent overhead via SSH (`metrics_collector.py`) and a native C-socket probe (`net_probe.c`).
- **Automated Disaster Recovery**: Zero-downtime LVM snapshots and remote Rsync synchronization managed by `backup_engine.py`.
- **Threat Alerting Pipeline**: Real-time SSH brute-force detection — ingesting logs (`data_ingestor.py`), analyzing threat patterns (`log_aggregator.py`), and dispatching instant Telegram alerts (`notifier.py`).

---

## 🛠️ Detailed Component Breakdown

The system is designed with a modular, decoupled architecture, categorizing tasks into dedicated pipelines:

### 1. Telemetry & Log Collection Layer
- **`net_probe.c`**: Low-level C TCP socket probe checking target port availability (`UP`/`DOWN`) and measuring microsecond-level network latency with minimal footprint.
- **`metrics_collector.py`**: Extracts CPU, Memory, and Disk metrics via SSH, aggregates results from `net_probe`, and serializes the state into `metrics_collector.json`.
- **`log_aggregator.py`**: Scans and parses `journalctl` system logs to detect anomalies (such as SSH brute-force attempts) and dumps parsed events into `log_analyst.json`.

### 2. Ingestion, Storage & Alerting Pipeline
- **`database.py`**: Handles database initialization, creating and migrating relational schemas for `sysop_engine.db`.
- **`data_ingestor.py`**: Ingests both `metrics_collector.json` and `log_analyst.json` into `sysop_engine.db`. Analyzes threat severities and invokes alert routines.
- **`notifier.py`**: Formats alert payloads and instantly dispatches incident reports to administrators via Telegram Bot webhook.

### 3. API & Service Gateway
- **`api_gateway.py`**: High-performance FastAPI REST API exposing endpoints to query real-time metrics, historical telemetry, and security events from `sysop_engine.db`.

### 4. Orchestration & Disaster Recovery
- **`sysop_orchestrator.py`**: Master workflow scheduler executing the automated collection cycle in sequence (`net_probe` ➔ `metrics_collector` ➔ `log_aggregator` ➔ `data_ingestor` ➔ `notifier`).
- **`backup_engine.py`**: Automated backup and disaster recovery module leveraging **LVM snapshots** and **Rsync** to replicate secondary node storage back to the primary node with zero downtime.

---

## 🔄 Data Execution Flow

The system orchestrates data retrieval and execution through an asynchronous API gateway communicating with independent backend workers.

```text
       [ Dark Theme Web Dashboard ]
                    │
                    │ API Request (GET/POST)
                    ▼
           [ RESTful API Gateway ] ◄─────────────────────────┐
                (FastAPI)                                    │
                    │                                        │
        ┌───────────┴───────────┐                            │
        │ BackgroundTasks       │ BackgroundTasks            │
        ▼                       ▼                            │
[ sysop_orchestrator ]     [ backup_engine.py ]              │
│       │                       │                            │ Read Data
│       │ Full Pipeline         │ LVM Snapshot & Rsync       │ (logs, metrics,
│       ▼                       ▼                            │  backup history)
│ [ Target Nodes ]        [ Target Nodes ]                   │
│       │                       │                            │
│       │ Insert Data           │ Backup History             │
│       └───────────┬───────────┘                            │
│                   ▼                                        │
│          [ SQLite Database ] ──────────────────────────────┘
│           (sysop_engine.db)
▼
[ Telegram Bot ] ───► "SSH BRUTE-FORCE Detected! IP: 192.168.x.x"
```

---

## 🧰 Tech Stack & Tooling

| Category | Technologies |
|---|---|
| **Backend & API** | Python, FastAPI, Uvicorn |
| **System & Low-Level** | C (GCC, POSIX Sockets) |
| **Database** | SQLite3 (Embedded) |
| **Infrastructure & OS** | Linux, Systemd, Bash, OpenSSH |
| **Disaster Recovery** | LVM (Logical Volume Manager), Rsync |
| **UI & Notifications** | TailwindCSS, Chart.js, Telegram Bot API |

---

## 🔒 Security & Data Lifecycle

- **Zero Hardcoded Secrets** — Sensitive credentials (Telegram Bot tokens, SSH credentials) are strictly managed via environment variables (`.env`).
- **Runtime Data Isolation** — All dynamic runtime files (`sysop_engine.db`, `*.json`) and backup artifacts are isolated via `.gitignore` to prevent credential and state leakage.

---

## ⚙️ Deployment Pipeline

### Step 1: Infrastructure & SSH Security Setup

Both nodes must be running **Ubuntu 22.04 LTS** and able to ping each other. Configure NAT for Internet access (Telegram notifications).

```bash
# Verify connectivity
ping -c 3 <IP_TARGET_NODE>
ping -c 3 8.8.8.8

# Install OpenSSH Server
sudo apt update && sudo apt install -y openssh-server

# Generate SSH key and copy to Target Node
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
ssh-copy-id <user>@<IP_TARGET_NODE>

# Harden SSH: disable root login
sudo sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### Step 2: Directory Structure & Source Code Placement

```bash
mkdir -p ~/sysop_engine/modules
mkdir -p ~/sysop_engine/templates
```

```text
~/sysop_engine/
├── templates/
│   └── index.html
└── modules/
    ├── .env
    ├── api_gateway.py
    ├── backup_engine.py
    ├── data_ingestor.py
    ├── database.py
    ├── log_aggregator.py
    ├── metrics_collector.py
    ├── net_probe.c
    ├── notifier.py
    └── sysop_orchestrator.py
```

```bash
# Install GCC and compile the network probe
sudo apt install -y build-essential
gcc -O2 -o ~/sysop_engine/modules/netprobe ~/sysop_engine/modules/net_probe.c
chmod +x ~/sysop_engine/modules/netprobe
```

### Step 3: Environment Setup & Telegram Token

```bash
# Create virtual environment and install dependencies
cd ~/sysop_engine
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn requests python-dotenv

# Configure Telegram credentials
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > ~/sysop_engine/modules/.env
echo "TELEGRAM_CHAT_ID=your_chat_id_here" >> ~/sysop_engine/modules/.env
```

### Step 4: Systemd Service Configuration & Activation

```bash
SERVICE_USER=$(whoami)

sudo bash -c "cat <<EOF > /etc/systemd/system/sysop.service
[Unit]
Description=SysOps Engine FastAPI Web Dashboard & REST Gateway
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=/home/${SERVICE_USER}/sysop_engine/modules
EnvironmentFile=/home/${SERVICE_USER}/sysop_engine/modules/.env
ExecStart=/home/${SERVICE_USER}/sysop_engine/venv/bin/uvicorn api_gateway:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=3
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF"
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sysop.service
sudo systemctl status sysop.service
```

🎉 **SysOps Engine deployment completed successfully!**

---

## 📡 API Endpoints Reference

### 1. Web Dashboard
| Method | Endpoint | Description | Response |
|:---|:---|:---|:---|
| **GET** | `/` | Serves the main web dashboard | `templates/index.html` |

### 2. Control & Orchestration
| Method | Endpoint | Description | Response |
|:---|:---|:---|:---|
| **POST** | `/api/v1/trigger/pipeline` | Triggers metrics & log collection pipeline | `{"status": "ACCEPTED"}` |
| **POST** | `/api/v1/trigger/backup` | Triggers LVM snapshot emergency backup | `{"status": "ACCEPTED"}` |

### 3. Telemetry & Data Retrieval
| Method | Endpoint | Description | Response |
|:---|:---|:---|:---|
| **GET** | `/api/v1/health` | Cluster status & monitored nodes count | `{"cluster_status": "HEALTHY"}` |
| **GET** | `/api/v1/metrics/latest` | Latest metric records for all nodes | JSON Array |
| **GET** | `/api/v1/metrics/uptime` | 24-hour uptime percentage per node | JSON Array |
| **GET** | `/api/v1/metrics/history` | Last 60 metric records for charting | JSON Array |
| **GET** | `/api/v1/security/alerts` | Recent security events (last 20) | JSON Array |
| **GET** | `/api/v1/backups/history` | LVM backup history (last 10) | JSON Array |

---

## 🎬 Video Demo

https://github.com/user-attachments/assets/5b21fab2-c54e-4a13-8635-fe5205354250

https://github.com/user-attachments/assets/096f5d6b-e35a-4dcb-9dfb-8de4adc580f0

https://github.com/user-attachments/assets/4f3b0aba-e9e9-43fe-8c7f-d54799883b00
