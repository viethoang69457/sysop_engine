#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime

# Cấu hình danh sách Node trong hạ tầng
TARGET_NODES = [
    {"name": "target01", "ip": "192.168.56.11", "user": "node01"},
    {"name": "target02", "ip": "192.168.56.12", "user": "node02"}
]

PROBE_BINARY = "./net_probe"
OUTPUT_FILE = "../metrics_state.json"

def run_cmd(cmd_list):
    """Thực thi câu lệnh hệ thống an toàn dưới dạng List (chống lỗi Escape Shell)"""
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True, timeout=5)
        return res.stdout.strip()
    except Exception:
        return None

def collect_telemetry(node):
    """Thu thập toàn bộ chỉ số Health Check và OS Metrics của 1 Node"""
    ip = node["ip"]
    user = node["user"]
    
    # 1. Gọi binary C net_probe đo độ trễ Network
    probe_output = run_cmd([PROBE_BINARY, ip, "22"])
    try:
        data = json.loads(probe_output)
    except Exception:
        data = {"target": ip, "port": 22, "status": "DOWN", "latency_us": 0}

    # 2. Nếu Node UP, mở SSH dạng List thu thập Performance Metrics
    if data.get("status") == "UP":
        remote_script = (
            "cat /proc/loadavg | awk '{print $1}'; "
            "free -m | awk '/Mem:/ {print $3\"/\"$2}'; "
            "df -h / | awk 'NR==2 {print $5}' | tr -d '%'"
        )
        
        ssh_cmd = [
            "ssh", "-q",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=3",
            f"{user}@{ip}",
            remote_script
        ]
        
        metrics_raw = run_cmd(ssh_cmd)
        
        if metrics_raw:
            try:
                lines = metrics_raw.splitlines()
                data["cpu_load_1m"] = float(lines[0])
                data["ram_usage_mb"] = lines[1]
                data["disk_usage_percent"] = int(lines[2])
            except Exception as e:
                data["metrics_error"] = f"Parse error: {str(e)}"
        else:
            data["metrics_error"] = "Empty SSH response or Timeout"
            
    return data

def main():
    engine_state = {
        "timestamp": datetime.now().isoformat(),
        "nodes": []
    }

    for node in TARGET_NODES:
        node_data = collect_telemetry(node)
        node_data["node_name"] = node["name"]
        engine_state["nodes"].append(node_data)

    # Ghi dữ liệu ra file JSON đệm cho các Module phía sau sử dụng
    with open(OUTPUT_FILE, "w") as f:
        json.dump(engine_state, f, indent=4)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Telemetry collected successfully.")

if __name__ == "__main__":
    main()
