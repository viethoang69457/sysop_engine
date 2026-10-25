#!/usr/bin/env python3
import subprocess
import sqlite3
import os
from datetime import datetime

TARGET_NODES = [
    {"name": "target01", "ip": "192.168.56.11", "user": "node01", "vg": "vg_data", "lv": "lv_app"},
    {"name": "target02", "ip": "192.168.56.12", "user": "node02", "vg": "vg_data", "lv": "lv_app"}
]

BACKUP_VAULT = "/home/dgna69/sysop_engine/backups"
DB_PATH = "../sysop_engine.db"

def record_backup_to_db(node_name, backup_path, status):
    """Ghi vết bản backup vào SQLite Database cho API Gateway truy vấn"""
    if not os.path.exists(DB_PATH):
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO backup_history (node_name, backup_path, status)
            VALUES (?, ?, ?)
        ''', (node_name, backup_path, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] DB Log Error: {e}")

def run_backup_for_node(node):
    ip = node["ip"]
    user = node["user"]
    name = node["name"]
    vg = node["vg"]
    lv = node["lv"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_name = f"{lv}_snap_{timestamp}"
    dest_dir = f"{BACKUP_VAULT}/{name}/{timestamp}"

    print(f"\n[+] Starting Automated LVM Backup for Node: {name} ({ip})")

    # 1. Tạo LVM Snapshot
    cmd_snap = f"sudo lvcreate -L 200M -s -n {snap_name} /dev/{vg}/{lv}"
    ssh_snap = ["ssh", "-q", "-o", "StrictHostKeyChecking=no", f"{user}@{ip}", cmd_snap]
    res = subprocess.run(ssh_snap, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  [!] Failed to create snapshot on {name}")
        record_backup_to_db(name, "N/A", "FAILED_SNAPSHOT")
        return

    # 2. Mount Snapshot ra thư mục tạm
    mount_point = f"/mnt/snap_{timestamp}"
    cmd_mount = f"sudo mkdir -p {mount_point} && sudo mount /dev/{vg}/{snap_name} {mount_point}"
    ssh_mount = ["ssh", "-q", "-o", "StrictHostKeyChecking=no", f"{user}@{ip}", cmd_mount]
    subprocess.run(ssh_mount)

    # 3. Pull data bằng Rsync
    os.makedirs(dest_dir, exist_ok=True)
    rsync_cmd = [
        "rsync", "-avz", "--delete",
        "-e", "ssh -o StrictHostKeyChecking=no",
        f"{user}@{ip}:{mount_point}/",
        f"{dest_dir}/"
    ]
    rsync_res = subprocess.run(rsync_cmd, capture_output=True, text=True)

    # 4. Dọn dẹp Snapshot
    cmd_cleanup = f"sudo umount {mount_point} && sudo rm -rf {mount_point} && sudo lvremove -f /dev/{vg}/{snap_name}"
    ssh_cleanup = ["ssh", "-q", "-o", "StrictHostKeyChecking=no", f"{user}@{ip}", cmd_cleanup]
    subprocess.run(ssh_cleanup)

    if rsync_res.returncode == 0:
        print(f"  [✓] Backup successful! Data saved to: {dest_dir}")
        record_backup_to_db(name, dest_dir, "SUCCESS")
    else:
        print(f"  [!] Rsync failed for {name}")
        record_backup_to_db(name, dest_dir, "FAILED_RSYNC")

def main():
    os.makedirs(BACKUP_VAULT, exist_ok=True)
    for node in TARGET_NODES:
        run_backup_for_node(node)

if __name__ == "__main__":
    main()
