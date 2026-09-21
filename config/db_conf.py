import os

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
DEFAULT_DATABASE_URL = (
    "mssql+aioodbc://localhost:1433/news?"
    "driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&trusted_connection=yes"
)#这里是SQL Server 2022数据库的连接方式,news是数据库名称
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
engine_options = {
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
}
# SQLite 内存数据库用于测试，不支持 SQL Server 使用的 QueuePool 参数。
if not DATABASE_URL.startswith("sqlite"):
    engine_options.update(pool_size=10, max_overflow=10)

async_engine=create_async_engine(DATABASE_URL, **engine_options)#创建异步引擎
#定义SQLAlchemy 提供的异步会话工厂类的实例
AsyncSessionLocal=async_sessionmaker(
    bind=async_engine, #绑定数据库引擎
    class_=AsyncSession, #指定会话类
    expire_on_commit=False #提交后会话不过期，不会重新查询数据库
)
#创建依赖项，使用Depends注入到处理函数（共享通用逻辑，减少代码重复，指定接口使用）（服务器提供的服务）
async def get_db():#为路由函数提供数据库会话
    async with AsyncSessionLocal() as session:
        try:
            yield session #返回数据库会话给路由处理函数
            await session.commit()  #提交事务
        except Exception:
            await session.rollback() #有异常，回滚
            raise
        finally:
            await session.close()  #关闭会话
