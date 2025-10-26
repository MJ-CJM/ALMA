#!/usr/bin/env python3
"""
同时启动用户前端和管理员前端
"""

import subprocess
import threading
import time
import signal
import sys

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    print("\n🛑 正在停止所有服务...")
    sys.exit(0)

def run_user_frontend():
    """运行用户前端"""
    try:
        subprocess.run([
            "streamlit", "run", "front.py", 
            "--server.port", "8501",
            "--server.headless", "true"
        ])
    except Exception as e:
        print(f"用户前端启动失败: {e}")

def run_manager_frontend():
    """运行管理员前端"""
    try:
        subprocess.run([
            "streamlit", "run", "manager_front.py", 
            "--server.port", "8502",
            "--server.headless", "true"
        ])
    except Exception as e:
        print(f"管理员前端启动失败: {e}")

def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 同时启动 ALMA 用户前端和管理员前端...")
    print("=" * 60)
    print("访问地址:")
    print("  📱 用户前端: http://localhost:8501")
    print("  🔧 管理员前端: http://localhost:8502")
    print("  🔑 管理员密码: admin123456")
    print("=" * 60)
    print("按 Ctrl+C 停止所有服务")
    print()
    
    try:
        # 创建线程
        user_thread = threading.Thread(target=run_user_frontend, daemon=True)
        manager_thread = threading.Thread(target=run_manager_frontend, daemon=True)
        
        # 启动用户前端
        print("🚀 启动用户前端...")
        user_thread.start()
        time.sleep(3)  # 等待用户前端启动
        
        # 启动管理员前端
        print("🚀 启动管理员前端...")
        manager_thread.start()
        time.sleep(2)  # 等待管理员前端启动
        
        print("✅ 两个前端都已启动！")
        print("现在可以同时访问用户前端和管理员前端了")
        print()
        
        # 等待线程完成
        user_thread.join()
        manager_thread.join()
        
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        print("✅ 服务已停止")

if __name__ == "__main__":
    main()
