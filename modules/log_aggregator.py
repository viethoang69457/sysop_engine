#!/usr/bin/env python3
import json
import re
import subprocess
from datetime import datetime

# Cấu hình danh sách Target Nodes
TARGET_NODES = [
    {"name": "target01", "ip": "192.168.56.11", "user": "node01"},
    {"name": "target02", "ip": "192.168.56.12", "user": "node02"}
]

LOG_OUTPUT_FILE = "../log_analysis_state.json"

def run_ssh_cmd(user, ip, remote_command):
    """Thực thi câu lệnh remote SSH an toàn dưới dạng List Array để chống lỗi escape shell"""
    ssh_cmd = [
        "ssh", "-q",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=5",
        f"{user}@{ip}",
        remote_command
    ]
    try:
        res = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)
        return res.stdout.strip()
    except Exception:
        return ""

def analyze_node_logs(node):
    ip = node["ip"]
    user = node["user"]
    name = node["name"]

    print(f"[+] Analyzing System Logs for Node: {name} ({ip})...")

    # Trích xuất 100 dòng log mới nhất từ systemd journal (không dùng pager để tránh kẹt thread)
    cmd_journal = "sudo journalctl -n 100 --no-pager"
    raw_logs = run_ssh_cmd(user, ip, cmd_journal)

    # Biểu thức chính quy (Regex Patterns)
    # Bắt IP tấn công Brute-force SSH
    failed_ssh_pattern = re.compile(r"Failed password for .* from (\d+\.\d+\.\d+\.\d+)")
    # Bắt các từ khóa lỗi hệ thống/kernel nghiêm trọng
    error_pattern = re.compile(r"(ERROR|CRITICAL|FAILED|panic)", re.IGNORECASE)

    failed_login_ips = []
    system_errors = []

    if raw_logs:
        for line in raw_logs.splitlines():
            # 1. Quét dấu hiệu đăng nhập sai mật khẩu SSH
            ssh_match = failed_ssh_pattern.search(line)
            if ssh_match:
                failed_login_ips.append(ssh_match.group(1))

            # 2. Quét lỗi hệ thống nghiêm trọng
            if error_pattern.search(line):
                system_errors.append(line.strip())

    return {
        "node_name": name,
        "target_ip": ip,
        "timestamp": datetime.now().isoformat(),
        "ssh_failed_attempts_count": len(failed_login_ips),
        "suspicious_attacker_ips": list(set(failed_login_ips)),
        "critical_errors_found": len(system_errors),
        "recent_error_samples": system_errors[-5:]  # Lấy tối đa 5 log lỗi mới nhất
    }

def main():
    log_summary = {
        "generated_at": datetime.now().isoformat(),
        "nodes_analysis": []
    }

    for node in TARGET_NODES:
        node_result = analyze_node_logs(node)
        log_summary["nodes_analysis"].append(node_result)

    # Ghi dữ liệu kết quả ra file JSON đệm trung tâm
    with open(LOG_OUTPUT_FILE, "w") as f:
        json.dump(log_summary, f, indent=4)

    print(f"[✓] Log analysis completed. File saved to {LOG_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
