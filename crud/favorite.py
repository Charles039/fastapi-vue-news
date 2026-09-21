from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,delete,func
from models.favorite import Favorite
from models.news import News


#检查收藏状态：当前用户是否收藏了这个新闻
async def is_news_favorite(db:AsyncSession,user_id:int,news_id:int):
    query=select(Favorite).where(Favorite.user_id==user_id,Favorite.news_id==news_id)
    result=await db.execute(query)
    #是否有收藏记录
    return result.scalar_one_or_none() is not None

async def add_news_favorite(db:AsyncSession,user_id:int,news_id:int):
    favorite=Favorite(user_id=user_id,news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite

async def remove_news_favorite(db:AsyncSession,user_id:int,news_id:int):
   stmt= delete(Favorite).where(Favorite.user_id==user_id,Favorite.news_id==news_id)
   res=await db.execute(stmt)
   await db.commit()
   return res.rowcount>0

#获取收藏列表：获取的是某个用户的收藏列表加分页功能
async def get_favorite_list(
   db:AsyncSession,
   user_id:int,
   page:int=1,
   page_size:int=10
):
    #总量+收藏的新闻列表
    count_query=select(func.count()).where(Favorite.user_id==user_id)
    count_result=await db.execute(count_query)
    total=count_result.scalar_one()
    offset=(page-1)*page_size
    #获取收藏列表 - 联表查询join
    #select(查询主体模型类,(可选)起别名).join(联合查询的模型类，联合查询的条件)
    query=(select(News,Favorite.created_at.label("favorite_time"),Favorite.id.label("favorite_id")).
           join(Favorite,Favorite.news_id==News.id)
           .where(Favorite.user_id==user_id)
           .order_by(Favorite.created_at.desc())
           .offset(offset).limit(page_size))
    res=await db.execute(query)
    rows=res.all()
    return rows,total
#清空收藏列表：当前用户的收藏列表
async def remove_all_favorites(db:AsyncSession,user_id:int):
    stmt=delete(Favorite).where(Favorite.user_id==user_id)
    result=await db.execute(stmt)
    await db.commit()
    #返回删除数量
    return result.rowcount or 0
