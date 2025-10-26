#!/usr/bin/env python3
"""
基于 SQLModel 的数据库初始化脚本
创建所有必要的表和初始数据
"""

import json
import os
from datetime import datetime, timedelta
from models import DatabaseManager, User, InviteCode, Conversation, Message, UploadedFile

def load_config(config_file: str = "config.json") -> dict:
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 配置文件 {config_file} 不存在")
        return None
    except json.JSONDecodeError:
        print(f"错误: 配置文件 {config_file} 格式错误")
        return None

def create_database_and_tables():
    """创建数据库和所有表"""
    try:
        db_manager = DatabaseManager()
        
        # 创建所有表
        db_manager.create_tables()
        print("✅ 数据库和表创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 创建数据库和表失败: {e}")
        return False

def init_default_data():
    """初始化默认数据"""
    try:
        db_manager = DatabaseManager()
        
        # 创建默认邀请码
        default_codes = [
            {
                'code': 'ALMA2024001',
                'max_uses': 1,
                'description': '默认测试邀请码'
            },
            {
                'code': 'ALMA2024002', 
                'max_uses': 3,
                'description': '多次使用测试码'
            },
            {
                'code': 'ALMA2024003',
                'max_uses': 1,
                'expires_days': 180,
                'description': '半年有效期测试码'
            }
        ]
        
        for code_info in default_codes:
            # 检查邀请码是否已存在
            if not db_manager.validate_invite_code(code_info['code']):
                expires_days = code_info.get('expires_days', 365)
                db_manager.create_invite_code(
                    code_info['code'],
                    code_info['max_uses'],
                    expires_days,
                    code_info['description']
                )
        
        print("✅ 默认邀请码创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 初始化默认数据失败: {e}")
        return False

def create_upload_directories():
    """创建上传目录"""
    try:
        config = load_config()
        if not config:
            return False
            
        upload_path = config['file_upload']['upload_path']
        if not os.path.exists(upload_path):
            os.makedirs(upload_path, exist_ok=True)
            print(f"✅ 创建上传目录: {upload_path}")
        else:
            print(f"✅ 上传目录已存在: {upload_path}")
        return True
    except Exception as e:
        print(f"❌ 创建上传目录失败: {e}")
        return False

def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    try:
        config = load_config()
        if not config:
            return False
            
        db_config = config['database']
        
        # 先连接到 MySQL 服务器（不指定数据库）
        from sqlalchemy import create_engine, text
        
        server_url = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}"
            f"?charset=utf8mb4"
        )
        
        engine = create_engine(server_url, echo=False)
        
        with engine.connect() as conn:
            # 创建数据库
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            print(f"✅ 数据库 {db_config['database']} 创建成功")
            return True
            
    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    try:
        # 先创建数据库
        if not create_database_if_not_exists():
            return False
            
        db_manager = DatabaseManager()
        
        # 测试连接
        with db_manager.get_session() as session:
            from sqlalchemy import text
            # 执行简单查询测试连接
            result = session.exec(text("SELECT 1")).first()
            if result:
                print("✅ 数据库连接测试成功")
                return True
            else:
                print("❌ 数据库连接测试失败")
                return False
                
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始初始化 ALMA 数据库 (SQLModel 版本)...")
    
    # 加载配置
    config = load_config()
    if not config:
        return False
    
    # 测试数据库连接
    if not test_database_connection():
        print("❌ 数据库连接失败，请检查配置")
        return False
    
    # 创建数据库和表
    if not create_database_and_tables():
        return False
    
    # 初始化默认数据
    if not init_default_data():
        return False
    
    # 创建上传目录
    if not create_upload_directories():
        return False
    
    print("🎉 数据库初始化完成！")
    print("\n📋 默认邀请码:")
    print("  - ALMA2024001 (单次使用)")
    print("  - ALMA2024002 (3次使用)")  
    print("  - ALMA2024003 (半年有效期)")
    print("\n🔧 管理员密码: admin123456")
    print("\n📁 上传目录: uploads/")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("❌ 初始化失败，请检查配置和数据库连接")
        exit(1)
