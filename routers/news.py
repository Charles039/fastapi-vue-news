from fastapi import HTTPException

from fastapi import APIRouter,Depends,Query,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_conf import get_db
from crud import news
#模块化路由就是把每个业务功能的接口拆分到独立文件里，再统一挂载到主文件中
#创建APIRouter实例
#prefix路由前缀(API接口规范文档）
#tags分组标签
router=APIRouter(prefix="/api/news",tags=["news"])
#接口实现流程：
#1，模块化路由->API 接口规范文档（当前文件） 定义APIRouter实例，注册路由
#2，定义模型类->数据库表（数据库设计文档）   class Base(DeclarativeBase) pass; class Category(Base):__tablename__=...
#3，在crud文件夹里面创建文件，封装操作数据库的方法  select(模型类) add()。。。
#4，在路由处理函数里面调用crud封装好的方法，响应结果  Depends注入数据库依赖，调用查询逻辑，响应结果


@router.get("/categories")
async def get_categories(skip: int=0, limit:int =100,db: AsyncSession=Depends(get_db)):
    #先获取数据库里面新闻分类数据->先定义模型类(models文件夹)->封装查询数据的方法(crud文件夹）
    categories=await news.get_categories(db,skip,limit)
    return {
        "code":200,
        "message":"获取新闻分类成功",
        "data":categories
    }

@router.get("/list")
async def get_news_list(
        category_id:int=Query(gt=0,alias="categoryId"),
        page:int=Query(default=1,ge=1),
        page_size:int=Query(default=10,ge=1,alias="pageSize",le=100),
        db:AsyncSession=Depends(get_db)
):
    # Redis 命中时直接返回 list、total、hasMore，不再额外查询数据库。
    data=await news.get_news_page(db,category_id,page,page_size)
    return {
        "code":200,
        "message":"获取新闻列表成功",
        "data":data
    }
@router.get("/detail")
async def get_news_detail(news_id: int=Query(alias="id"), db:AsyncSession=Depends(get_db)):
    #获取新闻详情+浏览量加1+相关新闻
    news_detail=await news.get_news_detail(db,news_id)
    if not news_detail:
        raise HTTPException(status_code=404,detail="新闻不存在")
    views_res=await news.increase_news_views(db,news_detail.id)
    if not views_res:
        raise HTTPException(status_code=404,detail="更新新闻浏览量失败")

    related_news= await news.get_related_news(db,news_detail.id,news_detail.category_id)
    return{
        "code": 200,
        "message": "success",
        "data":
            {
                "id":news_detail.id,
                "title":news_detail.title,
                "content":news_detail.content,
                "image":news_detail.image,
                "author":news_detail.author,
                "publishTime":news_detail.publish_time,
                "categoryId":news_detail.category_id,
                "views":news_detail.views,
                "relatedNews":related_news
            }
    }
