import json
import requests
from typing import Dict, List, Optional
import os

class DifyBackend:
    """Dify 后端连接管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
        except json.JSONDecodeError:
            raise ValueError(f"配置文件 {self.config_file} 格式错误")
    
    def get_workflow_list(self) -> List[Dict]:
        """获取工作流列表"""
        return self.config.get('workflows', [])
    
    def get_workflow_by_id(self, workflow_id: str) -> Optional[Dict]:
        """根据ID获取工作流配置"""
        workflows = self.get_workflow_list()
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
        
        url = f"{workflow_config['api_base']}/v1/workflows/run"
        headers = {
            "Authorization": workflow_config['api_key'],
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

# 全局后端实例
dify_backend = DifyBackend()

def get_workflow_list() -> List[Dict]:
    """获取工作流列表"""
    return dify_backend.get_workflow_list()

def run_dify_workflow(question: str, user_id: str, workflow_id: str) -> str:
    """
    运行 Dify 工作流并返回解析后的答案
    """
    try:
        # 调用工作流
        response = dify_backend.run_dify_workflow_blocking(question, user_id, workflow_id)
        
        # 解析响应
        answer = dify_backend.parse_dify_response(response)
        
        return answer
        
    except Exception as e:
        return f"AI 回复生成失败: {str(e)}"

def test_all_workflows() -> Dict[str, Dict]:
    """测试所有工作流连接"""
    return dify_backend.get_workflow_status()
