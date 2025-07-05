from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from rag_service import RAGService

app = FastAPI(title="RAG API Server", description="RAG 文档检索服务")

# 初始化 RAG 服务
rag_service = RAGService()

# 请求模型
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    filename: Optional[str] = None

class RescanRequest(BaseModel):
    pdf_dir: Optional[str] = "data/pdf"

# 响应模型
class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    top_k: int
    filename: Optional[str] = None

class FileSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    filename: str
    count: int

class RescanResponse(BaseModel):
    message: str
    new_files: List[str]
    total_files: List[str]

class CollectionInfoResponse(BaseModel):
    collection_name: str
    num_entities: int
    available_files: List[str]
    processed_files_count: int
    stats: Dict[str, Any]

@app.get("/")
async def root():
    """根路径"""
    return {"message": "RAG API Server 正在运行", "status": "ready"}

@app.post("/search", response_model=SearchResponse)
async def search_similar_texts(request: SearchRequest):
    """搜索相似文本，支持按文件名过滤"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="查询文本不能为空")
        
        if request.top_k <= 0 or request.top_k > 20:
            raise HTTPException(status_code=400, detail="top_k 必须在 1-20 之间")
        
        # 搜索相似文本
        results = rag_service.search_similar_texts(
            request.query, 
            request.top_k, 
            request.filename
        )
        
        return SearchResponse(
            results=results,
            query=request.query,
            top_k=request.top_k,
            filename=request.filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.get("/search/file/{filename}", response_model=FileSearchResponse)
async def search_by_filename(filename: str, top_k: int = 10):
    """按文件名搜索文档内容"""
    try:
        if not filename.strip():
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        if top_k <= 0 or top_k > 50:
            raise HTTPException(status_code=400, detail="top_k 必须在 1-50 之间")
        
        # 按文件名搜索
        results = rag_service.search_by_filename(filename, top_k)
        
        return FileSearchResponse(
            results=results,
            filename=filename,
            count=len(results)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"按文件名搜索失败: {str(e)}")

@app.post("/rescan", response_model=RescanResponse)
async def rescan_pdf_directory(request: RescanRequest):
    """重新扫描 PDF 目录，处理新文件"""
    try:
        import os
        
        if not os.path.exists(request.pdf_dir):
            raise HTTPException(
                status_code=404, 
                detail=f"目录 {request.pdf_dir} 不存在"
            )
        
        # 获取所有 PDF 文件
        all_files = []
        for filename in os.listdir(request.pdf_dir):
            if filename.lower().endswith('.pdf'):
                all_files.append(filename)
        
        if not all_files:
            raise HTTPException(
                status_code=404, 
                detail=f"目录 {request.pdf_dir} 中没有找到 PDF 文件"
            )
        
        # 重新扫描并处理新文件
        rag_service.auto_load_pdf_files(request.pdf_dir)
        
        # 获取可用文件列表
        available_files = rag_service.get_available_files()
        
        return RescanResponse(
            message="重新扫描完成",
            new_files=all_files,  # 这里简化处理，实际应该返回新处理的文件
            total_files=available_files
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新扫描失败: {str(e)}")

@app.get("/files", response_model=List[str])
async def get_available_files():
    """获取可用的文件列表"""
    try:
        files = rag_service.get_available_files()
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@app.get("/collection-info", response_model=CollectionInfoResponse)
async def get_collection_info():
    """获取集合信息"""
    try:
        info = rag_service.get_collection_info()
        
        if not info:
            raise HTTPException(status_code=500, detail="获取集合信息失败")
        
        return CollectionInfoResponse(**info)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取集合信息失败: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "RAG API Server"}

if __name__ == "__main__":
    uvicorn.run(
        "rag_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False  # 禁用热重载以避免数据库文件冲突
    )
