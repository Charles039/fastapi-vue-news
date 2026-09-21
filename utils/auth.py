from fastapi import HTTPException,status

from fastapi import Header,Depends
from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine
from config.db_conf import get_db
from crud import users
#整合 根据 Token 查询用户。返回用户
async def get_current_user(authorization:str=Header(alias="Authorization"),db:AsyncSession=Depends(get_db)):


    #TOKEN: Bearer xxx  格式要求Authorization: Bearer <token_string>
    #token=authorization.split(" ")[1]
    token=authorization.replace("Bearer","").strip()
    user=await users.get_user_by_token(db,token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="无效的令牌或已经过期的令牌")
    return user


async def get_current_admin(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user
