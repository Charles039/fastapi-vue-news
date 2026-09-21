# 数据库版本管理

项目使用 Alembic 管理数据库结构。Alembic 连接地址与应用共用 `DATABASE_URL`；迁移命令不会创建 SQL Server 数据库本身，请先在 SQL Server 中创建一个空数据库。

## 全新数据库

安装依赖并配置目标数据库：

```powershell
python -m pip install -r requirements.txt
$env:DATABASE_URL = "mssql+aioodbc://localhost:1433/news?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&trusted_connection=yes"
alembic upgrade head
```

升级完成后会创建全部业务表、`alembic_version` 版本表，并补充以下分类：头条、社会、国内、国际、娱乐、体育、科技、财经。

创建第一个管理员：

```powershell
python -m scripts.create_admin
```

命令会交互式读取用户名和隐藏密码。新密码至少 8 位并需要二次确认；如果用户名已经存在，只提升管理员权限，不修改原密码。

## 初始化演示新闻

公开仓库的演示数据位于 `data/demo_news.json`，只包含新闻，不包含用户、Token、收藏、历史或通知。首次准备演示环境时，在完成数据库迁移后执行：

```powershell
python -m scripts.seed_demo_news
```

命令根据分类名称导入新闻；同一分类下标题相同的新闻会跳过，因此可以重复执行。维护演示数据时，在 SSMS 中执行只读脚本 `scripts/export_demo_news.sql`，把查询返回的一格完整 JSON 覆盖到 `data/demo_news.json`。导出规则为八个分类各取最新 10 条，不足 10 条则全部导出。

## 接管现有数据库

现有数据库已经有业务表和数据，不能直接执行初始建表迁移。先运行只读检查：

```powershell
python -m scripts.check_existing_database
```

缺少关键表或字段时，检查会失败；索引、唯一约束或默认分类不完整时只显示警告，不会修改数据库。处理或确认警告后，登记已有结构并创建通知表：

```powershell
alembic stamp 0003_seed_news_categories
alembic upgrade head
```

`stamp` 只创建或更新 `alembic_version`，不会重新创建业务表；随后的 `upgrade head` 会创建通知表。不要直接 `stamp head`，否则会跳过通知表创建，也不要在未通过结构检查的现有数据库上执行这些命令。

如果本机 Python ODBC 因 TLS 配置暂时无法连接、但 SSMS 可以正常连接 `news`，可在备份后通过 SSMS 执行 `scripts/manual_upgrade_0004_notification.sql`。该应急脚本只创建通知表及其索引，并把 Alembic 版本登记为 `0004_create_notification`；遇到未知版本或不完整的同名表时会回滚并报错。

## 日常开发

修改 ORM 模型后生成迁移草稿：

```powershell
alembic revision --autogenerate -m "describe change"
```

自动生成的脚本必须人工检查后再执行：

```powershell
alembic upgrade head
alembic current
alembic history
```

回退一个版本：

```powershell
alembic downgrade -1
```

迁移可能删除字段或表，生产数据上执行降级前必须备份。分类种子迁移的降级不会删除分类业务数据。
