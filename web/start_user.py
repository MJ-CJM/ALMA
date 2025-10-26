#!/usr/bin/env python3
"""
直接启动用户前端
"""

import os
import sys

print("🚀 启动 ALMA 用户前端...")
print("访问地址: http://localhost:8501")
print("按 Ctrl+C 停止服务")
print("=" * 50)

os.system("streamlit run front.py --server.port 8501")
