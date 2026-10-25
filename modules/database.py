#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = "../sysop_engine.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Trả về kết quả dạng Dictionary
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Bảng lưu trữ chỉ số Performance OS & Network
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_name TEXT NOT NULL,
            target_ip TEXT NOT NULL,
            status TEXT NOT NULL,
            latency_us INTEGER,
            cpu_load REAL,
            ram_usage TEXT,
            disk_usage_percent INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Bảng lưu trữ nhật ký sự cố & tấn công bảo mật
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_name TEXT NOT NULL,
            target_ip TEXT NOT NULL,
            ssh_failed_count INTEGER,
            attacker_ips TEXT,
            critical_errors_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Bảng lưu vết lịch sử LVM Backup
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backup_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_name TEXT NOT NULL,
            backup_path TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("[✓] Database initialized successfully at sysop_engine.db")

if __name__ == "__main__":
    init_db()
