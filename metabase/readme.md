# OpenMautoTest Metabase 数据可视化

本目录包含OpenMautoTest项目的Metabase数据可视化配置，提供测试质量核心指标的监控面板。

## 功能特性

### 6个核心指标

1. **历史自动化执行总数** - 显示每日自动化测试执行的总数趋势
2. **历次自动化执行的测试用例数** - 显示测试用例数量的历史趋势图
3. **测试用例成功率** - 显示测试用例通过率的分布（趋势图/饼图）
4. **单次任务总耗时** - 显示每次测试运行的总耗时趋势图
5. **节省人时累计曲线** - 显示自动化测试节省的人工时间累计面积图
6. **失败用例TOP10** - 显示最常失败的测试用例横向条形图

### 支持的功能

- 实时数据刷新
- 多环境数据过滤
- 历史趋势分析
- 交互式图表
- 数据导出
- 自定义时间范围

## 目录结构

```
metabase/
├── Dockerfile-meta           # Metabase定制镜像
├── setup-metabase.sh        # 自动化配置脚本
├── nginx.conf               # Nginx反向代理配置
├── init/                    # 初始化配置
│   └── automationOS_dashboard.json  # 仪表盘配置
├── init-db/                 # 数据库初始化脚本
│   └── 01-create-databases.sql
├── sql/                     # SQL查询文件
│   ├── daily_trend.sql      # 历史执行总数查询
│   ├── pass_rate.sql        # 测试用例数趋势查询
│   ├── avg_duration.sql     # 测试成功率查询
│   ├── task_duration.sql    # 任务耗时查询
│   ├── saved_time.sql       # 节省时间查询
│   └── failed_cases_top10.sql  # 失败用例TOP10查询
└── readme.md               # 本文档
```

## 快速开始

### 1. 使用Docker Compose启动

```bash
# 启动Metabase和相关服务
docker-compose -f docker-compose.meta.yml up -d

# 查看服务状态
docker-compose -f docker-compose.meta.yml ps

# 查看日志
docker-compose -f docker-compose.meta.yml logs -f metabase
```

### 2. 手动配置Metabase

如果自动配置失败，可以手动配置：

```bash
# 运行配置脚本
docker-compose -f docker-compose.meta.yml --profile setup up metabase-setup

# 或者手动执行
docker exec -it openmautotest-metabase /app/setup-metabase.sh
```

### 3. 访问Metabase

启动完成后，访问 http://localhost:3000

默认管理员账户：
- 邮箱：admin@openmautotest.com
- 密码：admin123

## 配置说明

### 环境变量

主要环境变量配置：

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| MB_ADMIN_EMAIL | 管理员邮箱 | admin@openmautotest.com |
| MB_ADMIN_PASSWORD | 管理员密码 | admin123 |
| POSTGRES_DB | OpenMautoTest数据库名 | openmautotest |
| POSTGRES_USER | 数据库用户名 | postgres |
| POSTGRES_PASSWORD | 数据库密码 | postgres |
| MB_ENCRYPTION_SECRET_KEY | 加密密钥 | 需要修改 |

### 数据库连接

Metabase会自动连接到以下数据源：

1. **OpenMautoTest数据库**：包含测试执行数据
2. **Metabase配置数据库**：存储Metabase的配置信息

### 服务端口

| 服务 | 端口 | 描述 |
|------|------|------|
| Metabase | 3000 | Web界面 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存（可选） |
| Nginx | 80 | 反向代理（可选） |

## SQL查询详解

### 1. daily_trend.sql - 历史自动化执行总数

```sql
-- 显示每日自动化测试执行的总数趋势
SELECT 
    DATE(start_time) as execution_date,
    COUNT(DISTINCT run_id) as total_executions,
    COUNT(*) as total_test_cases,
    -- 更多统计信息...
FROM test_case_runs 
WHERE start_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(start_time)
ORDER BY execution_date DESC;
```

### 2. pass_rate.sql - 测试用例数趋势

显示测试用例通过率的历史趋势，支持按项目和环境分组。

### 3. avg_duration.sql - 测试成功率

提供测试用例成功率的多维度分析，包括按日期和按项目的分布。

### 4. task_duration.sql - 单次任务总耗时

计算每次测试运行的总耗时，包括实际运行时间和用例累计时间。

### 5. saved_time.sql - 节省人时累计

基于假设的手工测试时间，计算自动化测试节省的人工时间和成本。

### 6. failed_cases_top10.sql - 失败用例TOP10

识别最常失败的测试用例，包括失败率、影响度评分等指标。

## 仪表盘使用指南

### 访问仪表盘

1. 登录Metabase
2. 导航到"OpenMautoTest 质量核心看板"
3. 使用过滤器选择时间范围和环境

### 图表交互

- **点击图表元素**：查看详细数据
- **拖拽选择**：缩放时间范围
- **悬停显示**：查看具体数值
- **导出数据**：支持CSV、Excel格式

### 自定义视图

- 调整时间范围过滤器
- 选择特定测试环境
- 按项目名称过滤
- 设置自动刷新频率

## 数据刷新配置

### 自动刷新

Metabase配置了自动数据同步：

- **元数据同步**：每小时执行一次
- **字段值缓存**：每小时更新一次
- **仪表盘刷新**：可设置为5分钟、15分钟或1小时

### 手动刷新

```bash
# 触发数据库同步
curl -X POST http://localhost:3000/api/database/1/sync_schema

# 清除查询缓存
curl -X POST http://localhost:3000/api/cache/clear
```

## 性能优化

### 数据库优化

1. **索引优化**：
```sql
-- 为常用查询字段创建索引
CREATE INDEX idx_test_case_runs_start_time ON test_case_runs(start_time);
CREATE INDEX idx_test_case_runs_run_id ON test_case_runs(run_id);
CREATE INDEX idx_test_case_runs_status ON test_case_runs(status);
```

2. **分区表**（大数据量时）：
```sql
-- 按月分区test_case_runs表
CREATE TABLE test_case_runs_y2025m09 PARTITION OF test_case_runs
FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
```

### 查询优化

1. 限制查询时间范围
2. 使用聚合查询减少数据传输
3. 启用查询结果缓存
4. 合理设置刷新频率

## 故障排除

### 常见问题

1. **Metabase无法启动**
   - 检查数据库连接
   - 验证端口是否被占用
   - 查看容器日志

2. **数据不显示**
   - 确认数据库中有测试数据
   - 检查表结构是否正确
   - 验证SQL查询语法

3. **仪表盘加载慢**
   - 优化SQL查询
   - 增加数据库索引
   - 调整缓存设置

### 调试命令

```bash
# 查看Metabase日志
docker-compose -f docker-compose.meta.yml logs metabase

# 进入数据库检查数据
docker-compose -f docker-compose.meta.yml exec postgres psql -U postgres -d openmautotest

# 测试数据库连接
docker-compose -f docker-compose.meta.yml exec metabase curl -f http://localhost:3000/api/health

# 重启服务
docker-compose -f docker-compose.meta.yml restart metabase
```

## 扩展功能

### 添加新的查询

1. 在`sql/`目录创建新的SQL文件
2. 更新`setup-metabase.sh`脚本
3. 重新运行配置脚本

### 自定义仪表盘

1. 在Metabase界面创建新仪表盘
2. 导出仪表盘配置
3. 更新`init/`目录下的配置文件

### 集成告警

```bash
# 配置Slack通知
curl -X POST http://localhost:3000/api/alert \
  -H "Content-Type: application/json" \
  -d '{
    "alert_condition": "rows",
    "alert_first_only": false,
    "alert_above_goal": true,
    "card": {"id": 1},
    "channels": [{"channel_type": "slack", "details": {"webhook": "YOUR_WEBHOOK_URL"}}]
  }'
```

## 安全配置

### 生产环境建议

1. **修改默认密码**
2. **使用HTTPS**
3. **配置访问控制**
4. **定期备份配置**
5. **启用审计日志**

### 用户权限管理

```bash
# 创建只读用户组
curl -X POST http://localhost:3000/api/permissions/group \
  -H "Content-Type: application/json" \
  -d '{"name": "OpenMautoTest Viewers"}'
```

## 维护指南

### 定期维护任务

1. **清理旧数据**：定期清理超过保留期的测试数据
2. **备份配置**：定期备份Metabase配置和仪表盘
3. **更新依赖**：保持Metabase和数据库版本更新
4. **监控性能**：监控查询性能和资源使用

### 升级流程

1. 备份现有配置和数据
2. 测试新版本兼容性
3. 执行滚动更新
4. 验证功能正常

## 支持和反馈

如需帮助或有改进建议：

1. 查看Metabase官方文档
2. 检查项目Issue列表
3. 联系开发团队
4. 提交Pull Request

---

更多详细信息请参考Metabase官方文档和OpenMautoTest项目文档。
