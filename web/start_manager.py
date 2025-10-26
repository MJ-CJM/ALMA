#!/usr/bin/env python3
"""
直接启动管理员前端
"""

import os
import sys

print("🚀 启动 ALMA 管理员前端...")
print("访问地址: http://localhost:8502")
print("管理员密码: admin123456")
print("按 Ctrl+C 停止服务")
print("=" * 50)

os.system("streamlit run manager_front.py --server.port 8502")
