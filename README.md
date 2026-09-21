# FastAPI + Vue 新闻系统

这是一个前后端分离的新闻管理实践项目。后端使用 FastAPI、SQLAlchemy Async、SQL Server、Alembic 和 Redis，前端使用 Vue 3、Vite、Pinia 与 Vant。

项目支持用户注册登录、新闻分类与浏览、收藏、浏览历史、消息通知，以及管理员新闻管理和公告发布。Redis 用于新闻响应缓存、主动失效和防缓存击穿；Redis 不可用时，后端会降级为直接查询 SQL Server。

如果想要直接体验项目 请下载Releases最新版压缩包 解压打开.exe文件
## 主要功能

- 用户注册、登录和 JWT 身份认证
- 八个新闻分类：头条、社会、国内、国际、娱乐、体育、科技、财经
- 新闻列表、详情、相关推荐和浏览量
- 新闻收藏与浏览历史
- 用户消息通知、未读数量和通知删除
- 管理员新增、局部修改、删除新闻
- 管理员向所有已注册用户发布公告
- 新闻修改或删除时向相关收藏用户发送通知
- Redis 完整响应缓存、主动失效和防缓存击穿
- Alembic 数据库版本管理
- pytest、Vitest 和 GitHub Actions 自动化测试

## 项目结构

```text
fastapi-vue-news/
├─ alembic/              # 数据库迁移脚本
├─ cache/                # Redis 缓存逻辑
├─ config/               # 数据库和 Redis 配置
├─ crud/                 # 数据访问与业务逻辑
├─ data/                 # 公开演示新闻
├─ models/               # SQLAlchemy 模型
├─ routers/              # FastAPI 路由
├─ schemas/              # Pydantic 请求与响应模型
├─ scripts/              # 数据库检查和初始化命令
├─ tests/                # 后端测试
├─ xwzx-news/            # Vue 前端
├─ main.py               # FastAPI 应用入口
├─ requirements.txt      # 后端运行依赖
└─ requirements-dev.txt  # 后端测试依赖
```

## 一、准备运行环境

推荐环境：

- Git
- Python 3.12
- Node.js 22.13 或更高版本
- SQL Server 2019/2022
- SQL Server Management Studio（SSMS）
- Microsoft ODBC Driver 17 for SQL Server
- Redis（可选，可以使用 Docker 启动）

可以先检查本机版本：

```powershell
git --version
python --version
node --version
npm --version
```

## 二、克隆仓库

```powershell
git clone https://github.com/Charles039/fastapi-vue-news.git
cd fastapi-vue-news
```

后续没有特别说明的后端命令，都在项目根目录执行。

## 三、安装后端依赖

创建并激活独立的 Python 虚拟环境：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

如果 PowerShell 阻止激活脚本，可以只对当前终端临时放开限制：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

终端提示符前出现 `(.venv)`，表示虚拟环境已经激活。

## 四、创建 SQL Server 空数据库

1. 启动 SQL Server。
2. 使用 SSMS 连接 SQL Server。
3. 新建查询并执行：

```sql
IF DB_ID(N'news') IS NULL
BEGIN
    CREATE DATABASE [news];
END;
```

只需创建空的 `news` 数据库，不要手工创建业务表。Alembic 会负责创建数据表、字段、索引和初始化分类。

## 五、配置数据库连接

本项目默认使用本机 SQL Server、`1433` 端口、`news` 数据库和 Windows 身份认证。

在已经激活虚拟环境的 PowerShell 窗口中执行：

```powershell
$env:DATABASE_URL = "mssql+aioodbc://localhost:1433/news?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&trusted_connection=yes"
```

该环境变量只对当前 PowerShell 窗口有效。数据库迁移、初始化数据和启动后端时，请继续使用同一个窗口。

如果 SQL Server 地址、端口、ODBC 驱动或认证方式不同，需要修改连接地址。不要把真实数据库密码提交到 GitHub。

项目提供了 [`.env.example`](.env.example) 作为配置参考，但当前迁移和初始化命令不会自动读取根目录 `.env`，因此首次运行时仍建议在终端设置 `DATABASE_URL`。

## 六、创建数据库结构

运行全部数据库迁移：

```powershell
alembic upgrade head
```

如果终端找不到 `alembic`，使用虚拟环境中的程序：

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

不要使用 `python -m alembic`，因为当前 Alembic 包不能通过这种方式直接执行。

迁移成功后会创建全部业务表、`alembic_version` 表及八个默认新闻分类。更多数据库迁移说明见 [MIGRATIONS.md](MIGRATIONS.md)。

## 七、导入演示新闻

仓库中的 `data/demo_news.json` 只包含演示新闻，不包含真实用户、Token、收藏、浏览历史或通知。

执行：

```powershell
python -m scripts.seed_demo_news
```

命令会按照分类名称导入新闻。同一分类下标题相同的新闻会跳过，因此可以安全地重复执行。

这一步是可选的，但如果希望首次启动后立即看到新闻内容，建议执行。

## 八、创建管理员账号

执行：

```powershell
python -m scripts.create_admin
```

根据终端提示输入管理员用户名和至少 8 位的密码。输入密码时终端不会显示字符，这是正常现象。

如果输入的用户名已经存在，命令会将该用户提升为管理员，并保留原密码；如果用户名不存在，则创建新的管理员账号。

管理员账号用于进入前端“我的 → 新闻管理”，管理新闻和发布公告。普通用户也可以直接在前端注册，这一步不是普通用户使用系统的必要条件。

## 九、启动 Redis（可选）

Redis 用于缓存新闻分类和分页响应，并提供缓存主动失效与防缓存击穿锁。

如果未启动 Redis：

- 后端仍然能够启动；
- 用户、新闻、收藏、历史、通知和管理功能仍可使用；
- 新闻请求会直接查询 SQL Server；
- 控制台可能显示 Redis 连接失败信息；
- 请求速度可能变慢，数据库压力也会增加。

如果已经安装 Docker，可以运行：

```powershell
docker run -d --name fastapi-vue-news-redis -p 6379:6379 redis:7-alpine
```

容器创建后，下次只需执行：

```powershell
docker start fastapi-vue-news-redis
```

项目默认连接：

```text
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

远程 Redis 或带密码的 Redis 可以通过 `REDIS_HOST`、`REDIS_PORT`、`REDIS_DB` 和 `REDIS_PASSWORD` 环境变量配置。

## 十、启动后端

确认以下条件已经满足：

- SQL Server 正在运行；
- 已创建 `news` 数据库；
- 已完成 Alembic 迁移；
- 当前终端已激活 `.venv`；
- 当前终端已设置正确的 `DATABASE_URL`。

启动 FastAPI：

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

启动后可以访问：

- 后端首页：<http://127.0.0.1:8000/>
- Swagger API 文档：<http://127.0.0.1:8000/docs>

后端首页返回以下内容即表示启动成功：

```json
{"message": "Hello World"}
```

## 十一、安装并启动前端

保持后端终端运行，另外打开一个 PowerShell 窗口：

```powershell
cd fastapi-vue-news\xwzx-news
npm ci
npm run dev
```

根据终端提示访问前端，默认地址为：

```text
http://localhost:5173
```

前端默认请求 `http://127.0.0.1:8000`，按照上述默认端口运行时不需要额外配置。

如果后端部署在其他地址，可以在 `xwzx-news` 目录创建 `.env`：

```text
VITE_API_BASE_URL=http://你的后端地址:端口
```

修改前端环境变量后需要重新执行 `npm run dev`。

## 十二、以后如何重新启动

数据库迁移、演示新闻导入和管理员创建通常只需要执行一次。

每次启动后端：

```powershell
cd fastapi-vue-news
.\.venv\Scripts\Activate.ps1
$env:DATABASE_URL = "mssql+aioodbc://localhost:1433/news?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&trusted_connection=yes"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

每次启动前端，在另一个终端执行：

```powershell
cd fastapi-vue-news\xwzx-news
npm run dev
```

如果使用 Redis，还需要确保 Redis 服务或 Docker 容器正在运行。

## 十三、运行自动化测试

### 后端测试

安装测试依赖：

```powershell
pip install -r requirements-dev.txt
```

运行后端测试和覆盖率检查：

```powershell
pytest
```

普通测试使用 SQLite 内存数据库和 `fakeredis`，不会访问本机 SQL Server，也不要求启动真实 Redis。详细说明见 [TESTING.md](TESTING.md)。

### 前端测试

```powershell
cd xwzx-news
npm ci
npm run test:coverage
```

## 十四、Windows 零依赖演示版

项目支持构建面向招聘者的 Windows 10/11 64 位便携演示版。招聘者不需要安装 Python、Node.js、SQL Server、Redis 或 Docker，完整解压 ZIP 后双击 `FastApiVueNews.exe` 即可运行。

演示版与开发环境相互隔离：

- 本地开发默认继续使用 SQL Server、Redis 和 Vite；
- 演示版使用 EXE 旁边的 `news.db` SQLite 数据库；
- Vue 静态资源由 FastAPI 同源提供；
- Redis 替换为进程内缓存；
- 启动时自动选择可用端口并打开默认浏览器；
- 关闭命令行窗口或按 `Ctrl+C` 即可停止服务；
- 注册、收藏、历史和管理修改会保存在便携数据库中。

预置演示管理员：

```text
用户名：abc
密码：12345678
```

这些凭据只用于公开的本机演示版，请勿用于真实环境。

### 本机构建演示 ZIP

先安装发布依赖和前端依赖：

```powershell
pip install -r requirements-release.txt
cd xwzx-news
npm ci
cd ..
```

执行构建脚本：

```powershell
.\scripts\build_windows_demo.ps1
```

构建结果：

```text
demo-dist/FastApiVueNews-Windows-x64.zip
```

构建过程会生成干净的 SQLite 数据库，执行全部 Alembic 迁移，导入演示新闻并创建演示管理员，然后通过 PyInstaller 打包后端和前端资源。

### 通过 GitHub Actions 发布

推送以 `v` 开头的版本标签，例如：

```powershell
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions 会依次执行：

1. 后端 pytest 和覆盖率门槛；
2. 前端 Vitest 和覆盖率门槛；
3. SQLite 演示数据库初始化；
4. Vue 演示模式构建；
5. PyInstaller Windows 打包；
6. 打包后 EXE 冒烟测试；
7. 创建 GitHub Release 并上传 ZIP。

任意测试或构建步骤失败都会阻止 Release 发布。GitHub 自动提供的 `Source code (zip)` 只是源码；招聘者应下载 Release 附件 `FastApiVueNews-Windows-x64.zip`。

## 常见问题

### 1. 出现 `No module named 'aioodbc'`

说明当前 Python 环境没有安装项目依赖，或者使用了错误的 Python 解释器。重新激活 `.venv` 并安装依赖：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 出现 SQL Server 连接失败

依次检查：

- SQL Server 服务是否启动；
- `news` 数据库是否存在；
- SQL Server 是否启用了 TCP/IP；
- 实际端口是否为 `1433`；
- ODBC Driver 17 是否安装；
- 当前用户是否有数据库权限；
- `DATABASE_URL` 是否在当前终端中设置。

### 3. 控制台显示 Redis 连接失败

Redis 是可选依赖。不需要缓存时可以忽略；需要完整缓存功能时启动 Redis 服务或 Docker 容器。

### 4. `alembic` 不是可识别的命令

确认虚拟环境已激活，或者执行：

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

### 5. 前端能打开，但请求后端失败

检查：

- FastAPI 是否正在 `127.0.0.1:8000` 运行；
- <http://127.0.0.1:8000/docs> 是否可以访问；
- 前端 `VITE_API_BASE_URL` 是否正确；
- 修改环境变量后是否重启了 Vite。

### 6. 端口已被占用

可以换一个后端端口，例如：

```powershell
python -m uvicorn main:app --reload --port 8001
```

同时在 `xwzx-news/.env` 中配置：

```text
VITE_API_BASE_URL=http://127.0.0.1:8001
```

### 7. 演示版提示数据库或前端资源不存在

请确认已经完整解压 Release ZIP，并且没有只复制 `FastApiVueNews.exe`。演示版需要同目录中的 `news.db` 和 `_internal` 运行资源。

### 8. 演示版的数据保存在哪里

`news.db` 位于 `FastApiVueNews.exe` 旁边。删除解压目录或覆盖数据库会丢失演示期间产生的数据。请将程序解压到普通可写目录，不要放入 `Program Files`，也不要直接在压缩包预览窗口中运行。

## 数据与安全说明

- 仓库不会上传本地 `.env`、SQL Server 数据文件或数据库备份。
- 演示数据不包含真实用户信息。
- 请勿把数据库密码、Token 或其他密钥写入源码并提交到 GitHub。
- 全新环境应使用 Alembic 创建数据库结构，不要复制开发者本地数据库。
- 如果需要接管已有数据库，请先阅读 [MIGRATIONS.md](MIGRATIONS.md) 中的“接管现有数据库”部分。
