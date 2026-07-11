"""
定义后端的所有接口
"""

#1、导入FastAPI
from fastapi import FastAPI
from pydantic import BaseModel,Field
from agent.langchain_assistant import assistant_query
# 导入StreamingResponse，用于发送事件流：EventStream
from starlette.responses import StreamingResponse
#2、创建一个application，简称app
app = FastAPI()

#3、配置app的路由映射函数，每一个端点所对应的处理函数
class ChatRequest(BaseModel):
    """
    定义 /chat的请求体
    """
    query:str = Field(description="用户查询")

#3.1 配置/chat接口
@app.post("/chat")
async def chat(request:ChatRequest):
    """
    处理用户查询，返回agent回复回复
    """
    query = request.query

    return StreamingResponse(
        assistant_query(query)  ,#传入一个异步生成器，用于逐块发送响应
        media_type="text/event-stream" #Http规范的事件流媒体类型
    )
   
