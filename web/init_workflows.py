#!/usr/bin/env python3
"""
从 config.json 导入 workflow 到数据库的初始化脚本
"""

import sys
from models import DatabaseManager

def main():
    """主函数"""
    print("=" * 50)
    print("工作流初始化脚本")
    print("=" * 50)
    
    try:
        db_manager = DatabaseManager()
        
        # 检查数据库中是否已有工作流
        existing_workflows = db_manager.get_all_workflows()
        
        if existing_workflows:
            print(f"数据库中已有 {len(existing_workflows)} 个工作流")
            response = input("是否继续导入？(y/n): ").strip().lower()
            if response != 'y':
                print("已取消")
                return
        
        # 询问是否全局可见
        is_global_input = input("导入的工作流是否设置为全局可见？(y/n，默认 y): ").strip().lower()
        is_global = is_global_input != 'n'
        
        print("\n开始导入工作流...")
        
        # 导入工作流
        imported_count = db_manager.import_workflows_from_config(is_global=is_global)
        
        if imported_count > 0:
            print(f"✅ 成功导入 {imported_count} 个工作流")
            print(f"   全局可见: {'是' if is_global else '否'}")
        else:
            print("ℹ️  没有新工作流需要导入（可能已存在）")
        
        # 显示导入后的工作流列表
        all_workflows = db_manager.get_all_workflows()
        if all_workflows:
            print("\n当前数据库中的工作流列表：")
            print("-" * 50)
            for wf in all_workflows:
                status_icon = "✅" if wf.status == "active" else "❌"
                global_icon = "🌐" if wf.is_global else "👤"
                print(f"{status_icon} {global_icon} {wf.workflow_id} - {wf.name}")
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

