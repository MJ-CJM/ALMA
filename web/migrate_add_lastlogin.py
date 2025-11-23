"""
数据库迁移脚本：添加 last_login 字段到 user 表
"""
import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import DatabaseManager
from sqlalchemy import text, inspect

def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """检查表中是否存在指定列"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def add_last_login_column():
    """添加 last_login 字段到 user 表"""
    print("🚀 开始数据库迁移：添加 last_login 字段")
    print("=" * 50)
    
    try:
        db_manager = DatabaseManager()
        engine = db_manager.engine
        
        # 检查字段是否已存在
        if check_column_exists(engine, 'user', 'last_login'):
            print("✅ last_login 字段已存在，无需迁移")
            return True
        
        print("📝 正在添加 last_login 字段...")
        
        # 使用 ALTER TABLE 添加字段
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE `user` "
                "ADD COLUMN `last_login` DATETIME NULL "
                "AFTER `created_at`"
            ))
            conn.commit()
        
        print("✅ last_login 字段添加成功！")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_last_login_column()
    sys.exit(0 if success else 1)

