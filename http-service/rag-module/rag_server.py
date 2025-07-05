from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from rag_service import RAGService
import psutil
import gc
import time
import os

app = FastAPI(title="RAG Service", description="PDF文档检索服务")

# 初始化 RAG 服务
print("正在初始化RAG服务...")
try:
    # 使用硬编码的API密钥
    api_key = "sk-1f0b08f7ee4742c39dbb63254f3db29e"
    rag_service = RAGService(api_key=api_key)
    print("RAG服务初始化成功")
except Exception as e:
    print(f"RAG服务初始化失败: {e}")
    rag_service = None

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    score_threshold: Optional[float] = None

class SearchResult(BaseModel):
    text: str
    filename: str
    score: float
    text_length: int

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int

class ProcessRequest(BaseModel):
    batch_size: Optional[int] = 5  # API版本可以使用更大的批次

@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """搜索相关文档"""
    if not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    if rag_service is None:
        raise HTTPException(status_code=500, detail="RAG service not initialized")
    
    try:
        # 检查内存状态
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            raise HTTPException(status_code=503, detail="System memory usage too high")
        
        results = rag_service.search(request.query, request.limit, request.score_threshold)
        
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                text=result.get('text', ''),
                filename=result.get('filename', ''),
                score=result.get('score', 0.0),
                text_length=result.get('text_length', 0)
            ))
        
        return SearchResponse(results=search_results, total=len(search_results))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/process")
async def process_pdf_documents(request: ProcessRequest = ProcessRequest()):
    """处理PDF文档并建立索引"""
    if rag_service is None:
        raise HTTPException(status_code=500, detail="RAG service not initialized")
    
    try:
        # 检查内存状态
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            raise HTTPException(
                status_code=503, 
                detail=f"System memory usage too high ({memory.percent:.1f}%). Please free up memory first."
            )
        
        print(f"开始处理PDF文档，批次大小: {request.batch_size}")
        print(f"当前内存使用: {memory.percent:.1f}%")
        
        rag_service.process_pdfs(batch_size=request.batch_size)
        
        # 处理完成后清理内存
        gc.collect()
        
        return {
            "message": "PDF documents processed successfully", 
            "batch_size": request.batch_size,
            "final_memory_usage": f"{psutil.virtual_memory().percent:.1f}%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查"""
    import psutil
    memory_info = psutil.virtual_memory()
    
    status = "healthy"
    if memory_info.percent > 90:
        status = "warning"
    elif memory_info.percent > 95:
        status = "critical"
    
    return {
        "status": status, 
        "service": "RAG Service",
        "memory_usage": f"{memory_info.percent:.1f}%",
        "available_memory": f"{memory_info.available / 1024 / 1024 / 1024:.2f}GB",
        "rag_service_ready": rag_service is not None,
        "api_key_configured": True
    }

@app.get("/stats")
async def get_collection_stats():
    """获取集合统计信息"""
    if rag_service is None:
        raise HTTPException(status_code=500, detail="RAG service not initialized")
    
    try:
        stats = rag_service.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

@app.get("/memory")
async def get_memory_info():
    """获取详细内存信息"""
    memory = psutil.virtual_memory()
    return {
        "total": f"{memory.total / 1024 / 1024 / 1024:.2f}GB",
        "available": f"{memory.available / 1024 / 1024 / 1024:.2f}GB",
        "used": f"{memory.used / 1024 / 1024 / 1024:.2f}GB",
        "percent": f"{memory.percent:.1f}%",
        "status": "normal" if memory.percent < 80 else "warning" if memory.percent < 90 else "critical"
    }


if __name__ == "__main__":
    import os
    
    print("RAG服务正在启动...")
    

    
    # 检查系统内存
    memory = psutil.virtual_memory()
    print(f"系统内存状态: {memory.percent:.1f}% 已使用, 可用: {memory.available / 1024 / 1024 / 1024:.2f}GB")
    
    if memory.percent > 75:
        print("警告: 系统内存使用率较高，建议释放一些内存后再启动")
        print("建议操作:")
        print("1. 关闭不必要的应用程序")
        print("2. 清理浏览器缓存")
        print("3. 重启系统")
    
    if memory.percent > 90:
        print("错误: 内存使用率过高，无法启动服务")
        print("请释放内存后重试")
        exit(1)
    
    print("提示：首次使用请先调用 /process 接口处理PDF文档")
    print("建议使用: POST /process {'batch_size': 5}")
    
    port = int(os.getenv("PORT", 8000))
    print(f"服务将在 http://localhost:{port} 启动")
    
    uvicorn.run(app, host="0.0.0.0", port=port) 