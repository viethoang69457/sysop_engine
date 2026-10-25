# 🚀 SysOps Engine

  Agentless Linux Automation Management
> A lightweight, agentless Linux infrastructure automation suite: collects core system metrics, detects SSH security threats from system logs, manages automated backups, and provides web
dashboard ,RESTful API endpoints.

> ## 🛠 Architectural Overview: 4-Tier Layered Design

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

## ⚡ Core Features

- **Web Dashboard & REST API**: Real-time SLA/uptime monitoring (Chart.js) powered by a centralized FastAPI gateway.
- **Agentless Telemetry Collection**: Gathers node metrics (CPU, RAM, Disk, latency) with zero agent overhead via SSH (`metrics_collector.py`) and a native C-socket probe (`net_probe.c`).
- **Automated Disaster Recovery**: Zero-downtime LVM snapshots and remote Rsync synchronization managed by `backup_engine.py`.
- **Threat Alerting Pipeline**: Real-time SSH brute-force detection—ingesting logs (`data_ingestor.py`), analyzing threat patterns (`log_aggregator.py`), and dispatching instant Telegram alerts (`notifier.py`).

## 🛠️ Detailed Component Breakdown

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





















