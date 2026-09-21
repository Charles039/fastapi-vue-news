import asyncio
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from config.db_conf import AsyncSessionLocal
from models.users import User
from utils.security import get_hash_password


async def create_or_promote_admin() -> int:
    username = input("管理员用户名: ").strip()
    if not username:
        print("用户名不能为空。")
        return 1

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user is not None:
            if user.is_admin:
                print(f"用户 {username} 已经是管理员，无需修改。")
                return 0
            user.is_admin = True
            await session.commit()
            print(f"已将现有用户 {username} 提升为管理员，原密码保持不变。")
            return 0

        password = getpass("管理员密码（至少 8 位）: ")
        confirmation = getpass("再次输入密码: ")
        if len(password) < 8:
            print("密码长度不能少于 8 位。")
            return 1
        if password != confirmation:
            print("两次输入的密码不一致。")
            return 1

        session.add(
            User(
                username=username,
                password=get_hash_password(password),
                is_admin=True,
            )
        )
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            print("创建失败：用户名已存在，请重新运行命令。")
            return 1

        print(f"管理员 {username} 创建成功。")
        return 0


def main() -> None:
    raise SystemExit(asyncio.run(create_or_promote_admin()))


if __name__ == "__main__":
    main()

