from typing import Optional

from pydantic import BaseModel,Field,ConfigDict

#FastAPI 之所以要求用 Pydantic 模型类来接收请求体，本质上是将类型系统的力量从编译时扩展到了运行时。
#从技术实现上看，FastAPI 通过解析函数的类型注解来决定参数来源。当它检测到一个参数是 Pydantic BaseModel 的子类，且没有通过 Query、Path
# 等显式声明时，就会自动将这个参数识别为请求体数据。
#从功能层面看，Pydantic 提供了三个关键能力：第一是运行时数据验证，自动校验类型、长度、范围等；第二是自动序列化/反序列化，处理 JSON 与
# Python 对象的转换；第三是自动生成 OpenAPI Schema，为 API 文档提供数据模型描述。
#从设计哲学看，这体现了 FastAPI 推崇的'声明式编程'理念——开发者只需要用类型注解声明'数据长什么样'和'校验规则是什么'，框架会自动处理所有
# 底层的验证、转换和文档生成工作。相比传统需要手动编写大量 if/else 验证逻辑的方式，代码更简洁、更安全、更易维护。
#如果不用 Pydantic，虽然可以通过 Body 参数接收字典，但会失去类型安全、自动验证和文档生成等关键特性，在大型项目中会显著增加开发和维护成本。
#定义模型类
class UserRequest(BaseModel):
    username:str
    password:str

#user_info对应的类：基础类（其它选择性填写内容）+info类（id、用户名）
class UserInfoBase(BaseModel):
    nickname:Optional[str]=Field(None,max_length=50,description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
class UserInfoResponse(UserInfoBase):
    id:int
    username:str
    is_admin:bool=Field(alias="isAdmin")
    model_config = ConfigDict(
        from_attributes=True,  # 允许从ORM对象属性 中取值
        populate_by_name=True
    )

#data数据类型
class UserAuthResponse(BaseModel):
    token:str
    user_info:UserInfoResponse=Field(alias="userInfo")#alias表示别名,输出时用别名输出
    #模型类配置
    model_config=ConfigDict(
        populate_by_name=True,#别名alias/字段名兼容
        from_attributes=True  #允许从ORM对象属性 中取值
    )

#更新用户信息的模型类
class UserUpdateRequest(BaseModel):
    nickname:str=None
    avatar:str=None
    gender:str=None
    bio:str=None
    phone:str=None

class UserChangePasswordRequest(BaseModel):
    old_password:str=Field(alias="oldPassword",description="旧密码")
    new_password:str=Field(min_length=6,alias="newPassword",description="新密码")
