from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
from prompt_builder import PromptBuilder

app = FastAPI(title="Prompt Simple Service", description="简化的 Prompt 构建服务")

# 初始化 Prompt 构建器
prompt_builder = PromptBuilder()

# 请求模型
class QAPromptRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class LearningPlanRequest(BaseModel):
    goal: str
    time_range: Optional[str] = ""
    learning_background: Optional[str] = ""
    top_k: Optional[int] = 5

# 响应模型
class PromptResponse(BaseModel):
    prompt: str
    prompt_type: str
    query: str
    search_results_count: int

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Prompt Simple Service 正在运行", "status": "ready"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "Prompt Simple Service"}

@app.post("/ask", response_model=PromptResponse)
async def build_qa_prompt(request: QAPromptRequest):
    """
    问答 Prompt 接口
    
    接收用户问答问题，返回格式化后的问答 Prompt
    """
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        if request.top_k <= 0 or request.top_k > 20:
            raise HTTPException(status_code=400, detail="top_k 必须在 1-20 之间")
        
        # 构建问答 Prompt
        prompt = prompt_builder.build_qa_prompt(
            query=request.query,
            top_k=request.top_k
        )
        
        # 获取搜索结果数量
        search_results = prompt_builder.search_knowledge(
            request.query, 
            request.top_k
        )
        
        return PromptResponse(
            prompt=prompt,
            prompt_type="qa",
            query=request.query,
            search_results_count=len(search_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建问答 Prompt 时出错: {str(e)}")

@app.post("/plan", response_model=PromptResponse)
async def build_learning_plan_prompt(request: LearningPlanRequest):
    """
    学习计划 Prompt 接口
    
    接收用户学习目标，返回格式化后的学习计划 Prompt
    """
    try:
        if not request.goal.strip():
            raise HTTPException(status_code=400, detail="学习目标不能为空")
        
        if request.top_k <= 0 or request.top_k > 20:
            raise HTTPException(status_code=400, detail="top_k 必须在 1-20 之间")
        
        # 构建学习计划 Prompt
        prompt = prompt_builder.build_learning_plan_prompt(
            goal=request.goal,
            time_range=request.time_range,
            learning_background=request.learning_background,
            top_k=request.top_k
        )
        
        # 获取搜索结果数量
        search_results = prompt_builder.search_knowledge(
            request.goal, 
            request.top_k
        )
        
        return PromptResponse(
            prompt=prompt,
            prompt_type="learning_plan",
            query=request.goal,
            search_results_count=len(search_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建学习计划 Prompt 时出错: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 