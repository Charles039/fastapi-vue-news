#缓存redis配置，使用异步方式
#REDIS存储数据：将KEY缓存为VALUE数据
#方法：setex 参数key:str,expire:int(秒),value:str 设置缓存并指定过期时间
#get key:str 获取缓存值，若缓存不存在，返回None
#delete key:str 删除指定的缓存键
#exists key:str 检查缓存键是否存在，返回布尔值
#安装Redis服务端->配置Redis客户端->封装缓存操作->设置缓存策略（旁路策略：先查缓存，有数据则返回。没有数据则查询数据库）
import json
import os
import uuid
from typing import Any

import redis.asyncio as redis
REDIS_HOST=os.getenv("REDIS_HOST", "localhost")#主机地址
REDIS_PORT=int(os.getenv("REDIS_PORT", "6379"))  #端口地址
REDIS_DB=int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD=os.getenv("REDIS_PASSWORD")
REDIS_CONNECT_TIMEOUT=float(os.getenv("REDIS_CONNECT_TIMEOUT", "1"))
REDIS_SOCKET_TIMEOUT=float(os.getenv("REDIS_SOCKET_TIMEOUT", "1"))
#创建Redis连接对象
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
    socket_timeout=REDIS_SOCKET_TIMEOUT,
    decode_responses=True #是否将字节数据解码为字符串
)

#读取：字符串
async def get_cache(key:str):
    try:
        return await redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败:{e}")
        return None
#读取：列表或字典（可以序列化）
async def get_json_cache(key:str):
    try:
        data=await redis_client.get(key)
        if data:
            return json.loads(data) #序列化
        return None
    except Exception as e:
        print(f"获取JSON缓存失败:{e}")
        return None
#设置缓存 setex(key,expire,value)
async def set_cache(key:str,value:Any,expire:int=3600):
    try:
        if isinstance(value,(dict,list)):
            #转字符串再存
            value=json.dumps(value,ensure_ascii=False)#中文正常保存
        await redis_client.set(key,value,ex=expire)
        return True
    except Exception as e:
        print(f"设置缓存失败:{e}")
        return False

# 原子递增：用于切换缓存版本。Redis 不可用时返回 None，业务继续走数据库。
async def increment_cache(key: str):
    try:
        return await redis_client.incr(key)
    except Exception as e:
        print(f"递增缓存失败:{e}")
        return None

# 分布式互斥锁：SET key value NX EX expire
async def acquire_lock(key: str, expire: int = 10):
    token = str(uuid.uuid4())
    try:
        acquired = await redis_client.set(key, token, nx=True, ex=expire)
        # 字符串表示成功，False 表示锁正被占用，None 表示 Redis 故障。
        return token if acquired else False
    except Exception as e:
        print(f"获取缓存锁失败:{e}")
        return None

# 只允许锁的持有者释放锁，避免误删其他请求重新获得的锁。
async def release_lock(key: str, token: str):
    script = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('del', KEYS[1])
    end
    return 0
    """
    try:
        return bool(await redis_client.eval(script, 1, key, token))
    except Exception as e:
        print(f"释放缓存锁失败:{e}")
        return False
