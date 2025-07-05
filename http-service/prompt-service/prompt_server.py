from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from prompt_builder import PromptBuilder, PromptType

app = FastAPI(title="Prompt Service", description="Prompt 构建服务")

# 初始化 Prompt 构建器
prompt_builder = PromptBuilder()

# 请求模型
class QAPromptRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    filename: Optional[str] = None

class LearningPlanRequest(BaseModel):
    goal: str
    time_range: str
    learning_background: Optional[str] = ""
    top_k: Optional[int] = 5

class SummaryRequest(BaseModel):
    content: str
    summary_requirements: str
    top_k: Optional[int] = 5

class ExplanationRequest(BaseModel):
    concept: str
    explanation_requirements: str
    top_k: Optional[int] = 5

class CustomPromptRequest(BaseModel):
    prompt_type: str
    query: str
    top_k: Optional[int] = 5
    filename: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None

class TemplateRequest(BaseModel):
    prompt_type: str
    template: str

# 响应模型
class PromptResponse(BaseModel):
    prompt: str
    prompt_type: str
    query: str
    search_results_count: int

class TemplateResponse(BaseModel):
    prompt_type: str
    template: str
    message: str

class AvailableTypesResponse(BaseModel):
    available_types: List[str]
    total_count: int

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Prompt Service 正在运行", "status": "ready"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "Prompt Service"}

@app.post("/prompt/qa", response_model=PromptResponse)
async def build_qa_prompt(request: QAPromptRequest):
    """构建问答 Prompt"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        if request.top_k <= 0 or request.top_k > 20:
            raise HTTPException(status_code=400, detail="top_k 必须在 1-20 之间")
        
        # 构建问答 Prompt
        prompt = prompt_builder.build_qa_prompt(
            query=request.query,
            top_k=request.top_k,
            filename=request.filename
        )
        
        # 获取搜索结果数量
        search_results = prompt_builder.search_knowledge(
            request.query, 
            request.top_k, 
            request.filename
        )
        
        return PromptResponse(
            prompt=prompt,
            prompt_type="qa",
            query=request.query,
            search_results_count=len(search_results)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建问答 Prompt 失败: {str(e)}")

@app.post("/prompt/learning-plan", response_model=PromptResponse)
async def build_learning_plan_prompt(request: LearningPlanRequest):
    """构建学习计划 Prompt"""
    try:
        if not request.goal.strip():
            raise HTTPException(status_code=400, detail="学习目标不能为空")
        
        if not request.time_range.strip():
            raise HTTPException(status_code=400, detail="时间范围不能为空")
        
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
        search_results = prompt_builder.search_knowledge(request.goal, request.top_k)
        
        return PromptResponse(
            prompt=prompt,
            prompt_type="learning_plan",
            query=request.goal,
            search_results_count=len(search_results)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建学习计划 Prompt 失败: {str(e)}")

@app.post("/prompt/summary", response_model=PromptResponse)
async def build_summary_prompt(request: SummaryRequest):
    """构建总结 Prompt"""
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="总结内容不能为空")
        
        if not request.summary_requirements.strip():
            raise HTTPException(status_code=400, detail="总结要求不能为空")
        
        if request.top_k <= 0 or request.top_k > 20:
            raise HTTPException(status_code=400, detail="top_k 必须在 1-20 之间")
        
        # 构建总结 Prompt
        prompt = prompt_builder.build_summary_prompt(
            content=request.content,
            summary_requirements=request.summary_requirements,
            top_k=request.top_k
        )
        
        # 获取搜索结果数量
        search_results = prompt_builder.search_knowledge(request.content, request.top_k)
        
        return PromptResponse(
            prompt=prompt,
            prompt_type="summary",
            query=request.content,
            search_results_count=len(search_results)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建总结 Prompt 失败: {str(e)}")

@app.post("/prompt/explanation", response_model=PromptResponse)
async def build_explanation_prompt(request: ExplanationRequest):
    """构建解释 Prompt"""
    try:
        if not request.concept.strip():
            raise HTTPException(status_code=400, detail="解释概念不能为空")
        
        if not request.explanation_requirements.strip():
            raise HTTPException(status_code=400, detail="解释要求不能为空")
        
        if request.top_k <= 0 or request.top_k > 20:
            raise HTTPException(status_code=400, detail="top_k 必须在 1-20 之间")
        
        # 构建解释 Prompt
        prompt = prompt_builder.build_explanation_prompt(
            concept=request.concept,
            explanation_requirements=request.explanation_requirements,
            top_k=request.top_k
        )
        
        # 获取搜索结果数量
        search_results = prompt_builder.search_knowledge(request.concept, request.top_k)
        
        return PromptResponse(
            prompt=prompt,
            prompt_type="explanation",
            query=request.concept,
            search_results_count=len(search_results)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建解释 Prompt 失败: {str(e)}")

@app.post("/prompt/custom", response_model=PromptResponse)
async def build_custom_prompt(request: CustomPromptRequest):
    """构建自定义 Prompt"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        
        if not request.prompt_type.strip():
            raise HTTPException(status_code=400, detail="Prompt 类型不能为空")
        
        if request.top_k <= 0 or request.top_k > 20:
            raise HTTPException(status_code=400, detail="top_k 必须在 1-20 之间")
        
        # 检查 Prompt 类型是否支持
        available_types = prompt_builder.get_available_types()
        if request.prompt_type not in available_types:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的 Prompt 类型: {request.prompt_type}。支持的类型: {available_types}"
            )
        
        # 搜索相关知识
        search_results = prompt_builder.search_knowledge(
            request.query, 
            request.top_k, 
            request.filename
        )
        
        # 构建自定义 Prompt
        from prompt_builder import PromptContext
        context = PromptContext(
            query=request.query,
            search_results=search_results,
            additional_context=request.additional_context
        )
        
        prompt = prompt_builder.build_prompt(PromptType(request.prompt_type), context)
        
        return PromptResponse(
            prompt=prompt,
            prompt_type=request.prompt_type,
            query=request.query,
            search_results_count=len(search_results)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建自定义 Prompt 失败: {str(e)}")

@app.post("/template/add", response_model=TemplateResponse)
async def add_template(request: TemplateRequest):
    """添加新的 Prompt 模板"""
    try:
        if not request.prompt_type.strip():
            raise HTTPException(status_code=400, detail="Prompt 类型不能为空")
        
        if not request.template.strip():
            raise HTTPException(status_code=400, detail="模板内容不能为空")
        
        # 添加新模板
        prompt_builder.add_template(request.prompt_type, request.template)
        
        return TemplateResponse(
            prompt_type=request.prompt_type,
            template=request.template,
            message="模板添加成功"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加模板失败: {str(e)}")

@app.get("/types", response_model=AvailableTypesResponse)
async def get_available_types():
    """获取可用的 Prompt 类型"""
    try:
        available_types = prompt_builder.get_available_types()
        return AvailableTypesResponse(
            available_types=available_types,
            total_count=len(available_types)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Prompt 类型失败: {str(e)}")

@app.get("/rag/health")
async def check_rag_health():
    """检查 RAG 服务健康状态"""
    try:
        import requests
        response = requests.get(f"{prompt_builder.rag_api_base}/health", timeout=5)
        response.raise_for_status()
        return {"status": "connected", "rag_service": "healthy"}
    except Exception as e:
        return {"status": "disconnected", "rag_service": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "prompt_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )
