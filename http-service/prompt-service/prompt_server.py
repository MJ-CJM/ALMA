from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
import uvicorn
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rag-module'))
from rag_service import RAGService

app = FastAPI(title="Prompt Service", description="问答和学习计划生成服务")

RAG_SERVICE_URL = "http://localhost:5000"
rag_service = RAGService()

class QuestionRequest(BaseModel):
    question: str
    limit: Optional[int] = 5

class StudyPlanRequest(BaseModel):
    goal: str
    timeframe: str
    limit: Optional[int] = 10

class PromptTemplateRequest(BaseModel):
    type: str
    parameters: Dict[str, Any]

class DifyQARequest(BaseModel):
    question: str

class DifyStudyPlanRequest(BaseModel):
    goal: str
    timeframe: str

class ContextSource(BaseModel):
    filename: str
    text: str
    score: float

class QuestionResponse(BaseModel):
    prompt: str
    context_sources: List[ContextSource]

class StudyPlanResponse(BaseModel):
    prompt: str
    learning_materials: List[ContextSource]

class DifyResponse(BaseModel):
    success: bool
    prompt: Optional[str] = None
    error: Optional[str] = None
    context_count: Optional[int] = None
    materials_count: Optional[int] = None
    timestamp: str

class PromptTemplate:
    def __init__(self):
        self.templates = {
            "qa": """基于以下相关文档内容，请回答用户的问题。如果文档内容不足以回答问题，请说明需要更多信息。

相关文档：
{context}

用户问题：{question}

请提供详细、准确的回答：""",
            
            "study_plan": """基于以下知识内容，为用户制定学习计划。

相关知识内容：
{context}

学习目标：{goal}
时间范围：{timeframe}

请制定一个详细的学习计划，包括：
1. 学习阶段划分
2. 每个阶段的具体内容
3. 建议的学习方法
4. 时间安排
5. 评估方式

学习计划："""
        }
    
    def build_prompt(self, template_type: str, **kwargs) -> str:
        if template_type not in self.templates:
            raise ValueError(f"Unknown template type: {template_type}")
        
        template = self.templates[template_type]
        return template.format(**kwargs)

prompt_template = PromptTemplate()

def query_rag_service_http(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """通过HTTP调用RAG服务"""
    try:
        response = requests.post(
            f"{RAG_SERVICE_URL}/search",
            json={"query": query, "limit": limit},
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.RequestException as e:
        print(f"Error querying RAG service via HTTP: {e}")
        return []

def query_rag_service_direct(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """直接调用RAG服务"""
    try:
        return rag_service.search(query, limit)
    except Exception as e:
        print(f"Error querying RAG service directly: {e}")
        return []

@app.post("/qa", response_model=QuestionResponse)
async def question_answer(request: QuestionRequest):
    """问答接口"""
    if not request.question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    rag_results = query_rag_service_direct(request.question, request.limit)
    
    if not rag_results:
        raise HTTPException(status_code=404, detail="No relevant documents found")
    
    context = "\n\n".join([
        f"文档: {result['filename']}\n内容: {result['text']}"
        for result in rag_results
    ])
    
    prompt = prompt_template.build_prompt(
        "qa",
        context=context,
        question=request.question
    )
    
    context_sources = [
        ContextSource(
            filename=result['filename'],
            text=result['text'][:200] + "..." if len(result['text']) > 200 else result['text'],
            score=result['score']
        )
        for result in rag_results
    ]
    
    return QuestionResponse(prompt=prompt, context_sources=context_sources)

@app.post("/study-plan", response_model=StudyPlanResponse)
async def generate_study_plan(request: StudyPlanRequest):
    """学习计划生成接口"""
    if not request.goal or not request.timeframe:
        raise HTTPException(status_code=400, detail="Goal and timeframe are required")
    
    rag_results = query_rag_service_direct(request.goal, request.limit)
    
    if not rag_results:
        raise HTTPException(status_code=404, detail="No relevant learning materials found")
    
    context = "\n\n".join([
        f"知识点: {result['filename']}\n内容: {result['text']}"
        for result in rag_results
    ])
    
    prompt = prompt_template.build_prompt(
        "study_plan",
        context=context,
        goal=request.goal,
        timeframe=request.timeframe
    )
    
    learning_materials = [
        ContextSource(
            filename=result['filename'],
            text=result['text'][:200] + "..." if len(result['text']) > 200 else result['text'],
            score=result['score']
        )
        for result in rag_results
    ]
    
    return StudyPlanResponse(prompt=prompt, learning_materials=learning_materials)

@app.post("/prompt-template")
async def build_custom_prompt(request: PromptTemplateRequest):
    """自定义Prompt模板构建"""
    if not request.type:
        raise HTTPException(status_code=400, detail="Template type is required")
    
    try:
        prompt = prompt_template.build_prompt(request.type, **request.parameters)
        return {"prompt": prompt}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required parameter: {e}")

@app.post("/dify-qa", response_model=DifyResponse)
async def dify_qa_endpoint(request: DifyQARequest):
    """Dify问答接口"""
    if not request.question:
        return DifyResponse(
            success=False,
            error="Question is required",
            timestamp=datetime.now().isoformat()
        )
    
    rag_results = query_rag_service_direct(request.question, 5)
    
    if not rag_results:
        return DifyResponse(
            success=False,
            error="No relevant documents found",
            timestamp=datetime.now().isoformat()
        )
    
    context = "\n\n".join([
        f"文档: {result['filename']}\n内容: {result['text']}"
        for result in rag_results
    ])
    
    prompt = prompt_template.build_prompt(
        "qa",
        context=context,
        question=request.question
    )
    
    return DifyResponse(
        success=True,
        prompt=prompt,
        context_count=len(rag_results),
        timestamp=datetime.now().isoformat()
    )

@app.post("/dify-study-plan", response_model=DifyResponse)
async def dify_study_plan_endpoint(request: DifyStudyPlanRequest):
    """Dify学习计划接口"""
    if not request.goal or not request.timeframe:
        return DifyResponse(
            success=False,
            error="Goal and timeframe are required",
            timestamp=datetime.now().isoformat()
        )
    
    rag_results = query_rag_service_direct(request.goal, 10)
    
    if not rag_results:
        return DifyResponse(
            success=False,
            error="No relevant learning materials found",
            timestamp=datetime.now().isoformat()
        )
    
    context = "\n\n".join([
        f"知识点: {result['filename']}\n内容: {result['text']}"
        for result in rag_results
    ])
    
    prompt = prompt_template.build_prompt(
        "study_plan",
        context=context,
        goal=request.goal,
        timeframe=request.timeframe
    )
    
    return DifyResponse(
        success=True,
        prompt=prompt,
        materials_count=len(rag_results),
        timestamp=datetime.now().isoformat()
    )

@app.get("/health")
async def health_check():
    """健康检查"""
    rag_health = True
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/health", timeout=5)
        rag_health = response.status_code == 200
    except:
        rag_health = False
    
    return {
        "status": "healthy" if rag_health else "degraded",
        "rag_service": "healthy" if rag_health else "unhealthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/templates")
async def get_templates():
    """获取可用模板"""
    return {
        "available_templates": list(prompt_template.templates.keys()),
        "templates": {
            template_type: {
                "description": "Question answering template" if template_type == "qa" else "Study plan generation template",
                "required_parameters": ["context", "question"] if template_type == "qa" else ["context", "goal", "timeframe"]
            }
            for template_type in prompt_template.templates.keys()
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)