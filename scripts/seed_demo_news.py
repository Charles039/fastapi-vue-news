import argparse
import asyncio
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from cache.news_cache import invalidate_news_category
from config.db_conf import AsyncSessionLocal
from models.news import Category, News


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "demo_news.json"
DEFAULT_CATEGORIES = {
    "头条", "社会", "国内", "国际", "娱乐", "体育", "科技", "财经"
}


class DemoNewsItem(BaseModel):
    category: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    content: str = Field(min_length=1)
    image: str | None = Field(default=None, max_length=255)
    author: str | None = Field(default=None, max_length=50)
    views: int = Field(default=0, ge=0)
    publish_time: datetime = Field(alias="publishTime")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("category", "title")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("内容不能为空")
        return stripped


class DemoNewsDocument(BaseModel):
    version: int = Field(default=1, ge=1)
    news: list[DemoNewsItem]


@dataclass(frozen=True)
class SeedResult:
    inserted: int
    skipped: int


def load_demo_document(path: Path) -> DemoNewsDocument:
    try:
        content = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"无法读取演示数据文件: {path}") from exc

    try:
        payload = json.loads(content)
        return DemoNewsDocument.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"演示数据格式不正确: {exc}") from exc


async def seed_demo_news(path: Path = DEFAULT_DATA_PATH) -> SeedResult:
    document = load_demo_document(path)
    if not document.news:
        raise ValueError(
            "演示新闻为空。请先在 SSMS 执行 scripts/export_demo_news.sql，"
            "再用查询结果覆盖 data/demo_news.json。"
        )

    category_counts = Counter(item.category for item in document.news)
    unknown_categories = sorted(category_counts.keys() - DEFAULT_CATEGORIES)
    if unknown_categories:
        raise ValueError("演示数据包含未知分类: " + "、".join(unknown_categories))
    oversized_categories = sorted(
        name for name, count in category_counts.items() if count > 10
    )
    if oversized_categories:
        raise ValueError(
            "以下分类超过每类 10 条的限制: " + "、".join(oversized_categories)
        )

    requested_category_names = {item.category for item in document.news}
    async with AsyncSessionLocal() as session:
        category_result = await session.execute(
            select(Category).where(Category.name.in_(requested_category_names))
        )
        categories = {item.name: item for item in category_result.scalars().all()}
        missing_categories = sorted(requested_category_names - categories.keys())
        if missing_categories:
            raise ValueError(
                "数据库缺少新闻分类: " + "、".join(missing_categories)
                + "。请先执行 alembic upgrade head。"
            )

        candidate_keys = {(categories[item.category].id, item.title) for item in document.news}
        existing_keys: set[tuple[int, str]] = set()
        if candidate_keys:
            candidate_category_ids = {category_id for category_id, _ in candidate_keys}
            candidate_titles = {title for _, title in candidate_keys}
            existing_result = await session.execute(
                select(News.category_id, News.title).where(
                    News.category_id.in_(candidate_category_ids),
                    News.title.in_(candidate_titles),
                )
            )
            # SQL Server 不支持多列 tuple IN；先缩小候选范围，再在 Python 中精确过滤。
            existing_keys = {
                key for key in existing_result.all() if key in candidate_keys
            }

        inserted_category_ids: set[int] = set()
        seen_keys = set(existing_keys)
        skipped = 0
        for item in document.news:
            category_id = categories[item.category].id
            key = (category_id, item.title)
            if key in seen_keys:
                skipped += 1
                continue

            session.add(
                News(
                    title=item.title,
                    description=item.description,
                    content=item.content,
                    image=item.image,
                    author=item.author,
                    category_id=category_id,
                    views=item.views,
                    publish_time=item.publish_time,
                )
            )
            seen_keys.add(key)
            inserted_category_ids.add(category_id)

        inserted = len(seen_keys - existing_keys)
        await session.commit()

    # 数据已提交后切换列表缓存版本；Redis 不可用时沿用项目既有降级策略。
    for category_id in inserted_category_ids:
        await invalidate_news_category(category_id)

    return SeedResult(inserted=inserted, skipped=skipped)


async def async_main(path: Path) -> int:
    try:
        result = await seed_demo_news(path)
    except (ValueError, SQLAlchemyError) as exc:
        print(f"演示新闻初始化失败: {exc}")
        return 1

    print(
        f"演示新闻初始化完成：新增 {result.inserted} 条，"
        f"跳过 {result.skipped} 条重复新闻。"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导入公开仓库的演示新闻数据")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help=f"演示数据 JSON 路径（默认: {DEFAULT_DATA_PATH}）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raise SystemExit(asyncio.run(async_main(args.file.resolve())))


if __name__ == "__main__":
    main()
