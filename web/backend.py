import json
import requests
from typing import Dict, List, Optional
import os

class DifyBackend:
    """Dify 后端连接管理类"""
    
    def __init__(self, config_file: str = "config.json", db_manager=None):
        self.config_file = config_file
        self.config = self.load_config()
        self.db_manager = db_manager
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
        except json.JSONDecodeError:
            raise ValueError(f"配置文件 {self.config_file} 格式错误")
    
    def _workflow_to_dict(self, workflow) -> Dict:
        """将 Workflow 对象转换为字典格式"""
        return {
            'id': workflow.workflow_id,
            'name': workflow.name,
            'description': workflow.description,
            'api_base': workflow.api_base,
            'api_key': workflow.api_key
        }
    
    def get_workflow_list(self, user_id: Optional[int] = None) -> List[Dict]:
        """
        获取工作流列表
        优先从数据库读取，如果数据库为空则从 config.json 导入
        如果提供了 user_id，则只返回用户可见的工作流
        """
        # 如果提供了 db_manager，尝试从数据库读取
        if self.db_manager:
            try:
                # 如果提供了用户ID，获取用户可见的工作流
                if user_id:
                    workflows = self.db_manager.get_user_accessible_workflows(user_id)
                    if workflows:
                        return [self._workflow_to_dict(w) for w in workflows]
                
                # 否则获取所有启用的工作流（管理员用）
                all_workflows = self.db_manager.get_all_workflows()
                active_workflows = [w for w in all_workflows if w.status == 'active']
                if active_workflows:
                    return [self._workflow_to_dict(w) for w in active_workflows]
                
                # 如果数据库为空，尝试从 config.json 导入
                imported = self.db_manager.import_workflows_from_config(is_global=True)
                if imported > 0:
                    # 重新获取
                    all_workflows = self.db_manager.get_all_workflows()
                    active_workflows = [w for w in all_workflows if w.status == 'active']
                    if active_workflows:
                        return [self._workflow_to_dict(w) for w in active_workflows]
            except Exception as e:
                print(f"从数据库读取工作流失败: {e}，回退到配置文件")
        
        # 回退到配置文件
        return self.config.get('workflows', [])
    
    def get_workflow_by_id(self, workflow_id: str) -> Optional[Dict]:
        """根据ID获取工作流配置"""
        # 优先从数据库查找
        if self.db_manager:
            try:
                workflow = self.db_manager.get_workflow_by_workflow_id(workflow_id)
                if workflow:
                    return self._workflow_to_dict(workflow)
            except Exception as e:
                print(f"从数据库查找工作流失败: {e}")
        
        # 回退到配置文件
        workflows = self.config.get('workflows', [])
        for workflow in workflows:
            if workflow.get('id') == workflow_id:
                return workflow
        return None
    
    def run_dify_workflow_blocking(self, question: str, user_id: str, workflow_id: str) -> Dict:
        """
        调用 Dify 工作流（blocking 模式），返回 JSON
        """
        workflow_config = self.get_workflow_by_id(workflow_id)
        if not workflow_config:
            raise ValueError(f"工作流 {workflow_id} 不存在")
        
        # 处理 API Key 格式：确保有 Bearer 前缀
        api_key = workflow_config['api_key'].strip()
        if not api_key.startswith('Bearer '):
            # 如果没有 Bearer 前缀，添加它
            api_key = f"Bearer {api_key}" if api_key else api_key
        
        # 清理 api_base，确保没有尾部斜杠
        api_base = workflow_config['api_base'].rstrip('/')
        
        url = f"{api_base}/v1/workflows/run"
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "inputs": {"question": question},
            "response_mode": "blocking",
            "user": user_id,
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            raise ConnectionError(f"Dify API 调用失败: {str(e)}")
    
    def parse_dify_response(self, data: Dict) -> str:
        """
        解析 Dify 响应，提取答案内容
        兼容不同的响应结构
        """
        try:
            # 尝试不同的响应结构
            payload = data.get("data") or data
            
            # 尝试从 outputs 中获取答案
            outputs = payload.get("outputs") or {}
            answer = (
                outputs.get("answer") or
                outputs.get("text") or
                outputs.get("result") or
                outputs.get("response")
            )
            
            if answer:
                return str(answer)
            
            # 尝试从 message 字段获取
            message = payload.get("message")
            if isinstance(message, str):
                return message
            
            # 兜底：返回整个 outputs 的 JSON
            if outputs:
                return json.dumps(outputs, ensure_ascii=False, indent=2)
            
            # 最后兜底
            return "暂时无法生成回复，请稍后重试"
            
        except Exception as e:
            return f"解析回复失败: {str(e)}"
    
    def test_workflow_connection(self, workflow_id: str) -> tuple[bool, str]:
        """
        测试工作流连接
        返回: (是否成功, 错误信息)
        """
        try:
            workflow_config = self.get_workflow_by_id(workflow_id)
            if not workflow_config:
                return False, f"工作流 {workflow_id} 不存在"
            
            # 发送测试请求
            test_result = self.run_dify_workflow_blocking(
                "测试连接", 
                "test_user", 
                workflow_id
            )
            
            # 尝试解析响应
            answer = self.parse_dify_response(test_result)
            
            if "暂时无法生成回复" in answer or "解析回复失败" in answer:
                return False, f"工作流响应异常: {answer}"
            
            return True, "连接正常"
            
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"
    
    def get_workflow_status(self) -> Dict[str, Dict]:
        """
        获取所有工作流的状态
        返回: {workflow_id: {"status": "ok/error", "message": "..."}}
        """
        workflows = self.get_workflow_list()
        status = {}
        
        for workflow in workflows:
            workflow_id = workflow.get('id')
            workflow_name = workflow.get('name', workflow_id)
            
            try:
                is_ok, message = self.test_workflow_connection(workflow_id)
                status[workflow_id] = {
                    "name": workflow_name,
                    "status": "ok" if is_ok else "error",
                    "message": message
                }
            except Exception as e:
                status[workflow_id] = {
                    "name": workflow_name,
                    "status": "error",
                    "message": f"测试失败: {str(e)}"
                }
        
        return status

# 全局后端实例（延迟初始化，需要 db_manager）
_dify_backend = None

def get_dify_backend(db_manager=None):
    """获取 DifyBackend 实例（单例模式）"""
    global _dify_backend
    if _dify_backend is None:
        _dify_backend = DifyBackend(db_manager=db_manager)
    elif db_manager and _dify_backend.db_manager is None:
        _dify_backend.db_manager = db_manager
    return _dify_backend

def get_workflow_list(user_id: Optional[int] = None, db_manager=None) -> List[Dict]:
    """获取工作流列表，支持用户权限过滤"""
    backend = get_dify_backend(db_manager)
    return backend.get_workflow_list(user_id)

def run_dify_workflow(question: str, user_id: str, workflow_id: str, db_manager=None) -> str:
    """
    运行 Dify 工作流并返回解析后的答案
    """
    try:
        backend = get_dify_backend(db_manager)
        # 调用工作流
        response = backend.run_dify_workflow_blocking(question, user_id, workflow_id)
        
        # 解析响应
        answer = backend.parse_dify_response(response)
        
        return answer
        
    except Exception as e:
        return f"AI 回复生成失败: {str(e)}"

def test_all_workflows(db_manager=None) -> Dict[str, Dict]:
    """测试所有工作流连接"""
    backend = get_dify_backend(db_manager)
    return backend.get_workflow_status()
