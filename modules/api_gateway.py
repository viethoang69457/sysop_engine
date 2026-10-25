#!/usr/bin/env python3
import os
import subprocess
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
from database import get_db_connection

app = FastAPI(
    title="SysOps Engine RESTful API Gateway",
    description="Centralized Monitoring, Disaster Recovery & Security API Engine",
    version="2.1.0"
)

def run_sysop_script(script_name: str, extra_args: list = None):
    """Hàm bổ trợ chạy script Python ngầm bên dưới OS"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, script_name)
    cmd = ["python3", script_path]
    if extra_args:
        cmd.extend(extra_args)
    subprocess.run(cmd)

# =============================================================================
# 1. WEB DASHBOARD ROUTE
# =============================================================================
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "../templates/index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Error: templates/index.html NOT FOUND!</h1>"

# =============================================================================
# 2. CONTROL ACTION POST ENDPOINTS (BACKGROUND EXECUTION)
# =============================================================================
@app.post("/api/v1/trigger/pipeline")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """Kích hoạt 1 vòng cào Metrics + Logs ngầm"""
    background_tasks.add_task(run_sysop_script, "sysop_orchestrator.py", ["--no-backup"])
    return {"status": "ACCEPTED", "message": "Pipeline cào dữ liệu đã được kích hoạt chạy ngầm!"}

@app.post("/api/v1/trigger/backup")
def trigger_backup(background_tasks: BackgroundTasks):
    """Kích hoạt kịch bản LVM Snapshot Backup khẩn cấp ngầm"""
    background_tasks.add_task(run_sysop_script, "backup_engine.py")
    return {"status": "ACCEPTED", "message": "Kịch bản LVM Snapshot Backup đã được kích hoạt chạy ngầm!"}

# =============================================================================
# 3. GET DATA ENDPOINTS
# =============================================================================
@app.get("/api/v1/health")
def get_cluster_health():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(DISTINCT node_name) as total_nodes FROM metrics_history')
    row = cursor.fetchone()
    nodes_count = row["total_nodes"] if row else 0
    conn.close()
    return {
        "cluster_status": "HEALTHY" if nodes_count > 0 else "NO_DATA",
        "monitored_nodes_count": nodes_count,
        "active_modules": ["net_probe", "metrics_collector", "backup_engine", "log_aggregator", "data_ingestor", "telegram_notifier"]
    }

@app.get("/api/v1/metrics/latest")
def get_latest_metrics():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m1.* 
        FROM metrics_history m1
        INNER JOIN (
            SELECT node_name, MAX(id) as max_id 
            FROM metrics_history 
            GROUP BY node_name
        ) m2 ON m1.node_name = m2.node_name AND m1.id = m2.max_id
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/v1/metrics/uptime")
def get_24h_uptime():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            node_name,
            target_ip,
            COUNT(*) as total_checks,
            SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END) as up_checks
        FROM metrics_history
        WHERE created_at >= datetime('now', '-1 day')
        GROUP BY node_name
    ''')
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        total = row["total_checks"]
        up = row["up_checks"]
        uptime_pct = round((up / total * 100), 2) if total > 0 else 0.0
        results.append({
            "node_name": row["node_name"],
            "target_ip": row["target_ip"],
            "total_checks": total,
            "up_checks": up,
            "uptime_percentage": uptime_pct
        })
    return results

@app.get("/api/v1/metrics/history")
def get_metrics_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT node_name, latency_us, cpu_load, strftime('%H:%M:%S', created_at) as time_label
        FROM metrics_history
        ORDER BY id DESC LIMIT 60
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in reversed(rows)]

@app.get("/api/v1/security/alerts")
def get_security_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM security_events ORDER BY id DESC LIMIT 20')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/v1/backups/history")
def get_backup_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM backup_history ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
