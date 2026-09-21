/*
  SQL Server 本地开发环境应急迁移：创建通知表并登记 Alembic 0004。
  适用于 Python ODBC/TLS 暂时无法连接、但 SSMS 可以连接的现有 news 数据库。
  脚本可重复执行，不会删除或修改现有业务数据。
*/

USE [news];
GO

SET XACT_ABORT ON;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.[user]', N'U') IS NULL
        THROW 51000, N'缺少 dbo.user 表，已取消迁移。', 1;

    IF OBJECT_ID(N'dbo.notification', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.notification (
            id INTEGER IDENTITY(1, 1) NOT NULL,
            user_id INTEGER NOT NULL,
            [type] VARCHAR(30) NOT NULL,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            news_id INTEGER NULL,
            news_title VARCHAR(255) NULL,
            dedupe_key VARCHAR(100) NOT NULL,
            is_read BIT NOT NULL
                CONSTRAINT DF_notification_is_read DEFAULT (0),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            CONSTRAINT pk_notification PRIMARY KEY (id),
            CONSTRAINT fk_notification_user_id_user
                FOREIGN KEY (user_id) REFERENCES dbo.[user] (id),
            CONSTRAINT uq_notification_user_dedupe
                UNIQUE (user_id, dedupe_key)
        );
    END;

    IF EXISTS (
        SELECT required.name
        FROM (VALUES
            (N'id'), (N'user_id'), (N'type'), (N'title'), (N'content'),
            (N'news_id'), (N'news_title'), (N'dedupe_key'), (N'is_read'),
            (N'created_at'), (N'updated_at')
        ) AS required(name)
        WHERE NOT EXISTS (
            SELECT 1
            FROM sys.columns AS actual
            WHERE actual.object_id = OBJECT_ID(N'dbo.notification')
              AND actual.name = required.name
        )
    )
        THROW 51001, N'已有 notification 表结构不完整，已取消迁移。', 1;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.notification')
          AND name = N'idx_notification_news'
    )
        CREATE INDEX idx_notification_news
            ON dbo.notification (news_id);

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.notification')
          AND name = N'idx_notification_user_time'
    )
        CREATE INDEX idx_notification_user_time
            ON dbo.notification (user_id, updated_at);

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'dbo.notification')
          AND name = N'idx_notification_user_unread'
    )
        CREATE INDEX idx_notification_user_unread
            ON dbo.notification (user_id, is_read);

    IF OBJECT_ID(N'dbo.alembic_version', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        );
    END;

    IF EXISTS (
        SELECT 1 FROM dbo.alembic_version
        WHERE version_num NOT IN (
            '0003_seed_news_categories',
            '0004_create_notification'
        )
    )
        THROW 51002, N'Alembic 当前版本不是 0003/0004，请勿手工覆盖。', 1;

    DELETE FROM dbo.alembic_version;
    INSERT INTO dbo.alembic_version (version_num)
    VALUES ('0004_create_notification');

    COMMIT TRANSACTION;

    SELECT
        N'通知表迁移成功' AS result,
        version_num AS alembic_version
    FROM dbo.alembic_version;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
