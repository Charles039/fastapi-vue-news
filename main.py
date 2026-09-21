from routers import admin_news,admin_notification,news,users,favorite,history,notification
import datetime
import os
from fastapi import FastAPI,Path,Query,HTTPException,Depends#depends实现依赖注入，指定接口的代码复用
from pydantic import BaseModel,Field#field给请求体注解
#Basemodel检查进入系统的数据是否符合要求,自动将数据转换成 Python 对象提供友好的错误提示,自动生成 API 文档
from fastapi.responses import HTMLResponse,FileResponse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, Float, func

from fastapi.middleware.cors import CORSMiddleware

from utils.exception_handlers import register_exception_handlers


DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

#游览器安全机制，允许运行在一个源的Web应用，通过浏览器向另一个源的服务器发起跨域HTTP请求，并在服务器授权的前提下获取资源
#同源的三个条件：协议、域名、端口都需要相同
#解决：添加跨域资源共享CORS中间件，让后端主动告诉浏览器这个前端允许访问
#前端部分文件夹内CMD输入npm run dev 启动
#如果需要创建vue project：已安装node则使用npm create vue@latest
#记得找到Redis文件夹打开Redis缓存
app=FastAPI()
register_exception_handlers(app)#注册异常处理器

app.add_middleware(#中间键，自动给每个请求添加这个处理(CORS中间键)
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,  #允许携带Cookie
    allow_methods=["*"],     #允许的请求方法
    allow_headers=["*"],     #允许的请求头
)
#定义模块化路由->定义模型类->数据库crud->路由调用逻辑
@app.get("/")
async def root():
    return {"message":"Hello World"}

#挂载路由
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(admin_news.router)
app.include_router(notification.router)
app.include_router(admin_notification.router)
