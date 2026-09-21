/*
  只读导出脚本：从 news 数据库的八个分类中，各选取最新发布的 10 条新闻。

  使用方法：
  1. 在 SSMS 中连接本地 SQL Server 并打开此文件。
  2. 执行查询。
  3. 结果只有一行一列；复制 demo_json 单元格的完整内容。
  4. 用复制的 JSON 覆盖项目 data/demo_news.json。

  本脚本只执行 SELECT，不会修改数据库。
*/

USE [news];
GO

SET NOCOUNT ON;

DECLARE @demo_json NVARCHAR(MAX);

;WITH ranked_news AS (
    SELECT
        category.name AS category,
        news.title,
        news.description,
        news.content,
        news.image,
        news.author,
        news.views,
        news.publish_time,
        ROW_NUMBER() OVER (
            PARTITION BY news.category_id
            ORDER BY news.publish_time DESC, news.id DESC
        ) AS row_number
    FROM dbo.news AS news
    INNER JOIN dbo.news_category AS category
        ON category.id = news.category_id
    WHERE category.name IN (
        N'头条', N'社会', N'国内', N'国际',
        N'娱乐', N'体育', N'科技', N'财经'
    )
)
SELECT @demo_json = (
    SELECT
        1 AS [version],
        JSON_QUERY((
            SELECT
                category,
                title,
                description,
                content,
                image,
                author,
                views,
                CONVERT(VARCHAR(33), publish_time, 126) AS publishTime
            FROM ranked_news
            WHERE row_number <= 10
            ORDER BY category, publish_time DESC, title
            FOR JSON PATH, INCLUDE_NULL_VALUES
        )) AS news
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
);

SELECT @demo_json AS demo_json;
GO
