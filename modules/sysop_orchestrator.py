#!/usr/bin/env python3
"""
===============================================================================
SYSOPS ENGINE - MASTER ORCHESTRATOR
===============================================================================
Mục đích: Điều phối toàn bộ vòng đời vận hành hạ tầng (Pipeline Orchestration)
Chuỗi luồng (Execution Order):
  1. Metrics Collector & Net Probe (C Socket + SSH System Metrics)
  2. Log Aggregator (Journalctl + Python Regex Log Analysis)
  3. Data Ingestor & Alert Trigger (SQLite Persistence + Telegram Alerts)
===============================================================================
"""

import os
import sys
import time
import subprocess
from datetime import datetime

# Đường dẫn thư mục làm việc chuẩn
MODULES_DIR = os.path.dirname(os.path.abspath(__file__))

def print_banner():
    banner = """
    ███████╗██╗   ██╗███████╗██████╗ ██████╗ ███████╗
    ██╔════╝╚██╗ ██╔╝██╔════╝██╔══██╗██╔══██╗██╔════╝
    ███████╗ ╚████╔╝ ███████╗██║  ██║██████╔╝███████╗
    ╚════██║  ╚██╔╝  ╚════██║██║  ██║██╔═══╝ ╚════██║
    ███████║   ██║   ███████║██████╔╝██║     ███████║
    ╚══════╝   ╚═╝   ╚══════╝╚═════╝ ╚═╝     ╚══════╝
    Agentless Orchestrator Engine v1.0.0
    """
    print(banner)

def run_step(step_number, step_name, script_name, extra_args=None):
    """
    Thực thi 1 module Python con và bắt luồng xuất (stdout/stderr)
    """
    script_path = os.path.join(MODULES_DIR, script_name)
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    print(f"\n[{timestamp}] ──────── STEP {step_number}: {step_name.upper()} ────────")
    
    if not os.path.exists(script_path):
        print(f"  [❌ LỖI] Không tìm thấy file module: {script_name}")
        return False

    cmd = [sys.executable, script_path]
    if extra_args:
        cmd.extend(extra_args)

    try:
        # Thực thi script con và hiển thị realtime output ra terminal
        result = subprocess.run(cmd, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"  [✓ SUCCESS] {step_name} đã hoàn thành xuất sắc!")
            return True
        else:
            print(f"  [⚠️ WARNING] {step_name} kết thúc với mã lỗi exit code: {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print(f"  [❌ TIMEOUT] {step_name} bị quá thời gian thực thi (120s)!")
        return False
    except Exception as e:
        print(f"  [❌ EXCEPTION] Lỗi không xác định khi chạy {step_name}: {str(e)}")
        return False

def execute_full_pipeline():
    start_time = time.time()
    print_banner()
    print("=" * 75)
    print(f"🚀 KÍCH HOẠT CHUỖI TỰ ĐỘNG HÓA PIPELINE LÚC: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # BƯỚC 1: C Socket Net Probe + Metrics Collector (CPU, RAM, Disk, Latency)
    # -------------------------------------------------------------------------
    step1_ok = run_step(
        step_number=1,
        step_name="Core Telemetries & Network Probe (C Socket + SSH Metrics)",
        script_name="metrics_collector.py"
    )

    # -------------------------------------------------------------------------
    # BƯỚC 2: Centralized Log Aggregator (Journalctl + SSH Brute-Force Regex)
    # -------------------------------------------------------------------------
    step2_ok = run_step(
        step_number=2,
        step_name="Centralized Log Aggregator & Threat Detector",
        script_name="log_aggregator.py"
    )

    

    # -------------------------------------------------------------------------
    # BƯỚC 3: Data Ingestor & Real-time Telegram Alert Notifier
    # -------------------------------------------------------------------------
    step4_ok = run_step(
        step_number=4,
        step_name="Data Ingestor (SQLite Synchronization & Telegram Alerting)",
        script_name="data_ingestor.py"
    )

    # -------------------------------------------------------------------------
    # KẾT THÚC PIPELINE
    # -------------------------------------------------------------------------
    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 75)
    print(f"🏁 PIPELINE HOÀN TẤT TRONG: {elapsed} GIÂY")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    
  
    execute_full_pipeline()
