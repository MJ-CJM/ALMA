from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from rag_service import RAGService

app = FastAPI(title="RAG Simple API Server", description="简化的 RAG 文档检索服务")

# 初始化 RAG 服务
rag_service = RAGService()

# 响应模型
class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    top_k: int

@app.get("/")
async def root():
    """根路径"""
    return {"message": "RAG Simple API Server 正在运行", "status": "ready"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "RAG Simple API Server"}

@app.get("/search")
async def search_similar_texts(keyword: str, top_k: int = 5):
    """
    搜索接口
    
    Args:
        keyword: 搜索关键词
        top_k: 返回结果数量，默认5，最大20
        
    Returns:
        搜索结果列表
    """
    try:
        if not keyword.strip():
            raise HTTPException(status_code=400, detail="搜索关键词不能为空")
        
        if top_k <= 0 or top_k > 20:
            raise HTTPException(status_code=400, detail="top_k 必须在 1-20 之间")
        
        # 搜索相似文本
        results = rag_service.search_similar_texts(keyword, top_k)
        
        return SearchResponse(
            results=results,
            query=keyword,
            top_k=top_k
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 