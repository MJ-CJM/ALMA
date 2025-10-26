#!/usr/bin/env python3
"""
ALMA 项目启动脚本
支持命令行参数直接启动，避免用户交互
"""

import sys
import os
import argparse

def show_help():
    """显示帮助信息"""
    print("🚀 ALMA AI 助手启动脚本")
    print("=" * 50)
    print("使用方法:")
    print("  python start.py [选项]")
    print("")
    print("选项:")
    print("  -u, --user        启动用户前端 (端口 8501)")
    print("  -m, --manager     启动管理员前端 (端口 8502)")
    print("  -i, --init         初始化数据库")
    print("  -h, --help         显示帮助信息")
    print("")
    print("示例:")
    print("  python start.py -u          # 启动用户前端")
    print("  python start.py -m          # 启动管理员前端")
    print("  python start.py -i          # 初始化数据库")
    print("  python start.py -u -m       # 同时启动用户和管理员前端")

def start_user_frontend():
    """启动用户前端"""
    print("🚀 启动用户前端...")
    print("访问地址: http://localhost:8501")
    os.system("streamlit run front.py --server.port 8501")

def start_manager_frontend():
    """启动管理员前端"""
    print("🚀 启动管理员前端...")
    print("访问地址: http://localhost:8502")
    os.system("streamlit run manager_front.py --server.port 8502")

def start_both_frontends():
    """同时启动用户前端和管理员前端"""
    import subprocess
    import threading
    import time
    
    print("🚀 同时启动用户前端和管理员前端...")
    print("访问地址:")
    print("  - 用户前端: http://localhost:8501")
    print("  - 管理员前端: http://localhost:8502")
    print("按 Ctrl+C 停止所有服务")
    print("=" * 50)
    
    def run_user_frontend():
        """运行用户前端"""
        subprocess.run([
            "streamlit", "run", "front.py", 
            "--server.port", "8501",
            "--server.headless", "true"
        ])
    
    def run_manager_frontend():
        """运行管理员前端"""
        subprocess.run([
            "streamlit", "run", "manager_front.py", 
            "--server.port", "8502",
            "--server.headless", "true"
        ])
    
    try:
        # 创建线程
        user_thread = threading.Thread(target=run_user_frontend, daemon=True)
        manager_thread = threading.Thread(target=run_manager_frontend, daemon=True)
        
        # 启动线程
        user_thread.start()
        time.sleep(2)  # 等待用户前端启动
        manager_thread.start()
        
        # 等待线程完成
        user_thread.join()
        manager_thread.join()
        
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        print("✅ 服务已停止")

def init_database():
    """初始化数据库"""
    print("🚀 初始化数据库...")
    os.system("python init_database_sqlmodel.py")

def interactive_mode():
    """交互模式"""
    print("🚀 ALMA AI 助手启动脚本")
    print("=" * 50)
    print("请选择要启动的应用:")
    print("1. 用户前端 (front.py)")
    print("2. 管理员前端 (manager_front.py)")
    print("3. 数据库初始化 (init_database_sqlmodel.py)")
    print("=" * 50)
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == "1":
        start_user_frontend()
    elif choice == "2":
        start_manager_frontend()
    elif choice == "3":
        init_database()
    else:
        print("无效选择，请重新运行脚本")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ALMA AI 助手启动脚本",
        add_help=False
    )
    
    parser.add_argument('-u', '--user', action='store_true', 
                       help='启动用户前端')
    parser.add_argument('-m', '--manager', action='store_true', 
                       help='启动管理员前端')
    parser.add_argument('-i', '--init', action='store_true', 
                       help='初始化数据库')
    parser.add_argument('-h', '--help', action='store_true', 
                       help='显示帮助信息')
    
    args = parser.parse_args()
    
    # 如果没有参数，进入交互模式
    if len(sys.argv) == 1:
        interactive_mode()
        return
    
    # 显示帮助
    if args.help:
        show_help()
        return
    
    # 执行相应操作
    if args.init:
        init_database()
    
    # 如果同时指定了用户和管理员，则同时启动
    if args.user and args.manager:
        start_both_frontends()
    elif args.user:
        start_user_frontend()
    elif args.manager:
        start_manager_frontend()

if __name__ == "__main__":
    main()