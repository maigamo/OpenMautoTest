-- 创建多个数据库的初始化脚本

-- 创建metabase数据库 (用于Metabase配置存储)
SELECT 'CREATE DATABASE metabase'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metabase');

-- 如果openmautotest数据库不存在则创建
SELECT 'CREATE DATABASE openmautotest'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'openmautotest');

-- 创建用户和授权 (如果需要)
-- CREATE USER metabase_user WITH PASSWORD 'metabase_password';
-- GRANT ALL PRIVILEGES ON DATABASE metabase TO metabase_user;
-- GRANT CONNECT, SELECT ON DATABASE openmautotest TO metabase_user;
