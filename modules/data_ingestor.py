#!/usr/bin/env python3
import json
import os
from database import get_db_connection
from notifier import send_alert

METRICS_JSON = "../metrics_state.json"
LOGS_JSON = "../log_analysis_state.json"

def sync_metrics_to_db():
    if not os.path.exists(METRICS_JSON):
        return
    
    with open(METRICS_JSON, "r") as f:
        data = json.load(f)

    conn = get_db_connection()
    cursor = conn.cursor()

    for node in data.get("nodes", []):
        cursor.execute('''
            INSERT INTO metrics_history (node_name, target_ip, status, latency_us, cpu_load, ram_usage, disk_usage_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            node.get("node_name"),
            node.get("target"),
            node.get("status"),
            node.get("latency_us", 0),
            node.get("cpu_load_1m", 0.0),
            node.get("ram_usage_mb", "N/A"),
            node.get("disk_usage_percent", 0)
        ))

        # Cảnh báo nếu Node bị DOWN hoặc Disk > 80%
        if node.get("status") == "DOWN":
            send_alert(f"⚠️ **CRITICAL: Node {node.get('node_name')} ({node.get('target')}) is DOWN!**")
        elif node.get("disk_usage_percent", 0) > 80:
            send_alert(f"⚠️ **WARNING: High Disk Usage on {node.get('node_name')}: {node.get('disk_usage_percent')}%**")

    conn.commit()
    conn.close()

def sync_logs_to_db():
    if not os.path.exists(LOGS_JSON):
        return

    with open(LOGS_JSON, "r") as f:
        data = json.load(f)

    conn = get_db_connection()
    cursor = conn.cursor()

    for node in data.get("nodes_analysis", []):
        cursor.execute('''
            INSERT INTO security_events (node_name, target_ip, ssh_failed_count, attacker_ips, critical_errors_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            node.get("node_name"),
            node.get("target_ip"),
            node.get("ssh_failed_attempts_count", 0),
            ",".join(node.get("suspicious_attacker_ips", [])),
            node.get("critical_errors_found", 0)
        ))

        # Cảnh báo tự động nếu phát hiện tấn công Brute-Force SSH
        if node.get("ssh_failed_attempts_count", 0) > 0:
            send_alert(
                f"🔥 **SECURITY THREAT: SSH Brute-Force Detected!**\n"
                f"- **Target Node:** {node.get('node_name')} ({node.get('target_ip')})\n"
                f"- **Failed Attempts:** {node.get('ssh_failed_attempts_count')}\n"
                f"- **Attacker IP:** {', '.join(node.get('suspicious_attacker_ips'))}"
            )

    conn.commit()
    conn.close()

def main():
    sync_metrics_to_db()
    sync_logs_to_db()
    print("[✓] Sync completed: JSON State -> SQLite Database.")

if __name__ == "__main__":
    main()
