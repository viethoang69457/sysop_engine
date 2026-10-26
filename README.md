# 🚀 SysOps Engine

  Agentless Linux Automation Management
> A lightweight, agentless Linux infrastructure automation suite: collects core system metrics, detects SSH security threats from system logs, manages automated backups, and provides web
dashboard ,RESTful API endpoints.

>## 🛠 Architectural Overview: 4-Tier Layered Design

`SysOps Engine` follows a strict **4-Tier Layered Architecture**...

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




## **⚡ Core Features**

- **Web Dashboard & REST API**: Real-time SLA/uptime monitoring (Chart.js) powered by a centralized FastAPI gateway.
- **Agentless Telemetry Collection**: Gathers node metrics (CPU, RAM, Disk, latency) with zero agent overhead via SSH (`metrics_collector.py`) and a native C-socket probe (`net_probe.c`).
- **Automated Disaster Recovery**: Zero-downtime LVM snapshots and remote Rsync synchronization managed by `backup_engine.py`.
- **Threat Alerting Pipeline**: Real-time SSH brute-force detection—ingesting logs (`data_ingestor.py`), analyzing threat patterns (`log_aggregator.py`), and dispatching instant Telegram alerts (`notifier.py`).

## **🛠️ Detailed Component Breakdown**

The system is designed with a modular, decoupled architecture, categorizing tasks into dedicated pipelines:

### 1. Telemetry & Log Collection Layer
* **`net_probe.c`**: Low-level C TCP socket probe checking target port availability (`UP`/`DOWN`) and measuring microsecond-level network latency with minimal footprint.
* **`metrics_collector.py`**: Extracts CPU, Memory, and Disk metrics via SSH, aggregates results from `net_probe`, and serializes the state into `metrics_collector.json`.
* **`log_aggregator.py`**: Scans and parses `journalctl` system logs to detect anomalies (such as SSH brute-force attempts) and dumps parsed events into `log_analyst.json`.

### 2. Ingestion, Storage & Alerting Pipeline
* **`database.py`**: Handles database initialization, creating and migrating relational schemas for `sysop-engine.db`.
* **`data_ingestor.py`**: Ingests both `metrics_collector.json` and `log_analyst.json` into `sysop-engine.db`. Analyzes threat severities and invokes alert routines.
* **`notifier.py`**: Formats alert payloads and instantly dispatches incident reports to administrators via Telegram Bot webhook.

### 3. API & Service Gateway
* **`api_gateway.py`**: High-performance FastAPI REST API exposing endpoints to query real-time metrics, historical telemetry, and security events from `sysop-engine.db`.
* **`sysop_service.py`**: Lifecycle manager responsible for bootstrapping and managing the API daemon and background workers.

### 4. Orchestration & Disaster Recovery
* **`sysop_orchestrator.py`**: Master workflow scheduler executing the automated collection cycle in sequence (`net_probe` ➔ `metrics_collector` ➔ `log_aggregator` ➔ `data_ingestor` ➔ `notifier`).
* **`backup_engine.py`**: Automated backup and disaster recovery module leveraging **LVM snapshots** and **Rsync** to replicate secondary node storage back to the primary node with zero downtime.

## 🔄 Data Execution Flow (RESTful API Coordination)

The system orchestrates data retrieval...

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
## **🧰 Tech Stack & Tooling**

- Backend & API: Python (FastAPI, Uvicorn)
- System & Low-Level: C (GCC, POSIX Sockets)
- Database: SQLite3 (Embedded)
- Infrastructure & OS: Linux, Systemd, Bash, OpenSSH,Python
- Disaster Recovery: LVM (Logical Volume Manager), Rsync
- UI & Notifications: Chart.js, Telegram Bot API

## **🔒 Security & Data Lifecycle**

- Zero Hardcoded Secrets — Sensitive credentials (Telegram Bot tokens, SSH credentials) are strictly managed via environment variables (`.env`).
- Runtime Data Isolation — All dynamic runtime files (`sysop-engine.db`, `*.json`) and backup artifacts are isolated via `.gitignore` to prevent credential and state leakage.

## **⚙️ Deployment Pipeline**

---

### Step 1: Infrastructure & SSH Security Setup

1. **Network Connectivity Requirements (Control Node & Target Node):**
   * Both nodes must be running **Ubuntu** and able to **ping each other**.
   * Configure NAT interface for Internet access to update packages and send Telegram notifications.
   ```bash
   ping -c 3 <IP_TARGET_NODE>
   ping -c 3 8.8.8.8

# Install OpenSSH Server
sudo apt update && sudo apt install -y openssh-server

# Generate SSH Key and copy public key to Target Node
ssh-keygen -t rsa -b 4096 -N "" -f ~/.ssh/id_rsa
ssh-copy-id <user>@<IP_TARGET_NODE>

# Disable direct root login via SSH
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

**Step 2: Directory Structure & Source Code Placement**
mkdir -p ~/sysop_engine/modules
mkdir -p ~/sysop_engine/templates

Place index.html inside ~/sysop_engine/templates/:
~/sysop_engine/templates/index.html
Place all all modules files into ~/sysop_engine/modules/
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

# Install GCC build tools
sudo apt install -y build-essential

# Place net_probe.c at ~/sysop_engine/modules and compile
gcc -O2 -o ~/sysop_engine/netprobe ~/sysop_engine/net_probe.c
chmod +x ~/sysop_engine/netprobe

**Step 3: Environment Setup & Telegram Token**
1.Install Python Libraries (Virtualenv recommended):
cd ~/sysop_engine
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn requests python-dotenv

2.Configure Telegram Environment Variables (.env):
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > ~/sysop_engine/.env
echo "TELEGRAM_CHAT_ID=your_chat_id_here" >> ~/sysop_engine/.env

Step 4: Systemd Service Configuration & Activation (sysop.service)
1.Create Systemd Service configuration at /etc/systemd/system/sysop.service:
sudo bash -c 'cat <<EOF> /etc/systemd/system/sysop.service
[Unit]
Description=SysOps Engine Monitoring & Core Daemon
After=network.target

[Service]
Type=simple
User='$USER'
WorkingDirectory=/home/'$USER'/sysop_engine
EnvironmentFile=/home/'$USER'/sysop_engine/modules/.env
ExecStart=/home/'$USER'/sysop_engine/venv/bin/python3 -m modules.api_gateway
Restart=

https://github.com/user-attachments/assets/e4ebac9d-6e34-4753-9aea-03de7285b368



always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF'

2. Enable and start Daemon Service:
sudo systemctl daemon-reload
sudo systemctl enable --now sysop.service
sudo systemctl status sysop.service
🎉 SysOps Engine deployment completed successfully!


## 📡 API Endpoints Reference

> FastAPI Gateway RESTful routes for dashboard visualization, background job orchestration, and telemetry retrieval.

### 1. Web Dashboard
| Method | Endpoint | Description | Payload / Query | Response |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | Serves the main web dashboard interface | None | `templates/index.html` |

### 2. Control & Orchestration (Background Jobs)
| Method | Endpoint | Description | Payload / Query | Response |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/trigger/pipeline` | Triggers background metrics & log collection pipeline | None | `{"status": "ACCEPTED", ...}` |
| **POST** | `/api/v1/trigger/backup` | Triggers background LVM snapshot emergency backup | None | `{"status": "ACCEPTED", ...}` |

### 3. Telemetry & Data Retrieval
| Method | Endpoint | Description | Payload / Query | Response |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/health` | Returns cluster status & monitored nodes count | None | `{"cluster_status": "HEALTHY", ...}` |
| **GET** | `/api/v1/metrics/latest` | Fetches latest metric records for all nodes | None | JSON Array (Latest node metrics) |
| **GET** | `/api/v1/metrics/uptime` | Calculates 24-hour uptime percentage per node | None | JSON Array (`uptime_percentage`, etc.) |
| **GET** | `/api/v1/metrics/history` | Fetches last 60 metric records for charting | None | JSON Array (`latency_us`, `cpu_load`, `time_label`) |
| **GET** | `/api/v1/security/alerts` | Fetches recent security events (last 20 logs) | None | JSON Array (Security event logs) |
| **GET** | `/api/v1/backups/history` | Fetches LVM backup history (last 10 records) | None | JSON Array (Backup execution logs) |

## VIDEO DEMO 

https://github.com/user-attachments/assets/5b21fab2-c54e-4a13-8635-fe5205354250



https://github.com/user-attachments/assets/096f5d6b-e35a-4dcb-9dfb-8de4adc580f0


https://github.com/user-attachments/assets/4f3b0aba-e9e9-43fe-8c7f-d54799883b00

































