from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="RAG Mock Search API (字符串版)")


# 请求模型
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    filename: Optional[str] = None

@app.post("/search", response_model=str)
async def search(request: SearchRequest):
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="查询不能为空")
        if request.top_k <= 0 or request.top_k > 20:
            raise HTTPException(status_code=400, detail="top_k 应在 1~20 之间")

        answer = "测试数据"
        return answer

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("rag_service_xw:app", host="0.0.0.0", port=8000, reload=False)