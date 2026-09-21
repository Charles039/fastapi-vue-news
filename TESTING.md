# 自动化测试说明

项目的测试环境与开发数据库隔离：后端使用 SQLite 内存数据库，Redis 默认使用 `fakeredis`，不会连接或修改 SQL Server 中的数据。

## 后端

首次准备测试环境：

```powershell
python -m venv .venv-test
.\.venv-test\Scripts\python.exe -m pip install -r requirements-dev.txt
```

运行全部后端测试和覆盖率检查：

```powershell
.\.venv-test\Scripts\python.exe -m pytest
```

`pytest.ini` 将覆盖率门槛设为 70%，并明确排除 `main1.py`。真实 Redis 集成测试默认跳过；确认本机 Redis 测试实例可用后可运行：

```powershell
$env:RUN_REDIS_INTEGRATION = "1"
$env:REDIS_HOST = "127.0.0.1"
$env:REDIS_PORT = "6379"
.\.venv-test\Scripts\python.exe -m pytest -m redis_integration
```

后端测试还会从空 SQLite 数据库执行 `alembic upgrade head`，验证全部业务表（包括通知表）、`is_admin` 字段、索引、唯一约束和 8 个默认新闻分类，并验证可降级到 `base`。测试也会模拟现有数据库从 `0003_seed_news_categories` 接管后升级，确保原有用户、新闻、收藏、历史和分类数据不被重建。

## 前端

```powershell
Set-Location xwzx-news
npm ci
npm run test:coverage
npm run build
```

Vitest 覆盖用户认证/管理员状态、登录与管理员路由守卫、管理员新闻 Store，以及消息通知的分页、未读、已读、删除、清空、公告发布和错误响应。语句、分支、函数、行覆盖率门槛均为 70%。

## GitHub Actions

`.github/workflows/tests.yml` 会在每次 push 和 pull request 时并行执行后端与前端任务。CI 使用临时 SQLite 数据库和模拟 Redis，不依赖 SQL Server、Redis 服务或任何密钥。数据库迁移和管理员初始化说明见 `MIGRATIONS.md`。
