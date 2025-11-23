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
    print("  -p, --port         指定端口号 (默认 8501)")
    print("  -i, --init         初始化数据库")
    print("  -h, --help         显示帮助信息")
    print("")
    print("示例:")
    print("  python start.py              # 启动统一应用 (端口 8501)")
    print("  python start.py -p 8502       # 启动统一应用 (指定端口)")
    print("  python start.py -i             # 初始化数据库")
    print("")
    print("说明:")
    print("  现在只需要启动一个服务，登录时选择用户或管理员身份即可")

def start_unified_app(port: int = 8501):
    """启动统一应用（包含用户和管理员界面）"""
    print("🚀 启动 ALMA AI 助手统一应用...")
    print("=" * 50)
    print(f"访问地址: http://localhost:{port}")
    print("")
    print("使用说明:")
    print("  - 登录时选择 '👤 用户登录' 进入用户界面")
    print("  - 登录时选择 '🔧 管理员登录' 进入管理员界面")
    print("  - 按 Ctrl+C 停止服务")
    print("=" * 50)
    os.system(f"streamlit run front.py --server.port {port}")

def init_database():
    """初始化数据库"""
    print("🚀 初始化数据库...")
    os.system("python init_database_sqlmodel.py")

def interactive_mode():
    """交互模式"""
    print("🚀 ALMA AI 助手启动脚本")
    print("=" * 50)
    print("请选择要执行的操作:")
    print("1. 启动统一应用 (front.py)")
    print("2. 数据库初始化 (init_database_sqlmodel.py)")
    print("=" * 50)
    
    choice = input("请输入选择 (1-2): ").strip()
    
    if choice == "1":
        port_input = input("请输入端口号 (直接回车使用默认 8501): ").strip()
        port = int(port_input) if port_input.isdigit() else 8501
        start_unified_app(port)
    elif choice == "2":
        init_database()
    else:
        print("无效选择，请重新运行脚本")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ALMA AI 助手启动脚本",
        add_help=False
    )
    
    parser.add_argument('-p', '--port', type=int, default=8501,
                       help='指定端口号 (默认 8501)')
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
    else:
        # 默认启动统一应用
        start_unified_app(args.port)

if __name__ == "__main__":
    main()