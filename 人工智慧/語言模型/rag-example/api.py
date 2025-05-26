from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, AsyncGenerator
import uvicorn
from rag import RAGSystem
import os
import json
import asyncio

app = FastAPI(title="RAG API", description="使用Langchain和Ollama的RAG應用API")

# 掛載靜態文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 設置模板
templates = Jinja2Templates(directory="templates")

# 初始化RAG系統
rag_system = None

class Query(BaseModel):
    question: str
    stream: bool = False

class ContextDoc(BaseModel):
    content: str
    source: str

class QueryResponse(BaseModel):
    answer: str
    context_docs: List[ContextDoc]

@app.on_event("startup")
async def startup_event():
    global rag_system
    
    # 檢查數據目錄
    if not os.path.exists("data") or not any(file.endswith('.txt') for file in os.listdir("data")):
        from main import create_sample_document
        create_sample_document()
    
    # 初始化RAG系統
    rag_system = RAGSystem()
    rag_system.initialize()
    print("RAG系統已初始化完成")

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """提供前端網頁介面"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query", response_model=QueryResponse)
async def query(query: Query):
    global rag_system
    
    if rag_system is None:
        raise HTTPException(status_code=500, detail="RAG系統尚未初始化")
    
    try:
        # 如果不是流式輸出，使用普通模式
        if not query.stream:
            result = rag_system.query(query.question)
            return {
                "answer": result["result"],
                "context_docs": result.get("context_docs", [])
            }
        else:
            # 這裡不應該執行到，因為流式請求應該由 /stream_query 處理
            raise HTTPException(status_code=400, detail="流式查詢請使用 /stream_query 端點")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢處理失敗: {str(e)}")

@app.post("/stream_query")
async def stream_query_post(query: Query):
    """處理 POST 請求的流式回應查詢"""
    return await process_stream_query(query.question)

@app.get("/stream_query")
async def stream_query_get(question: str):
    """處理 GET 請求的流式回應查詢"""
    return await process_stream_query(question)

async def process_stream_query(question: str):
    """統一處理流式查詢邏輯"""
    global rag_system
    
    if rag_system is None:
        raise HTTPException(status_code=500, detail="RAG系統尚未初始化")
    
    try:
        # 獲取上下文文檔和生成器
        generator, context_docs = rag_system.query(question, stream=True)
        
        # 首先發送上下文文檔
        async def stream_generator():
            # 發送上下文文檔
            context_data = {
                "type": "context",
                "data": context_docs
            }
            yield f"data: {json.dumps(context_data)}\n\n"
            
            # 流式發送答案
            for chunk in generator:
                answer_data = {
                    "type": "answer",
                    "data": chunk
                }
                yield f"data: {json.dumps(answer_data)}\n\n"
                await asyncio.sleep(0.01)  # 添加少量延遲以避免瀏覽器過載
            
            # 發送完成信號
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式查詢處理失敗: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def start_api():
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_api() 