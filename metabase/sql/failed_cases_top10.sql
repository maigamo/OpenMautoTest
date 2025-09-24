-- 失败用例TOP10(横向条形图)
-- 显示最常失败的测试用例，用于识别需要优化的测试

WITH failure_stats AS (
    SELECT 
        test_case_name,
        project_name,
        flow_name,
        environment,
        COUNT(*) as total_executions,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failure_count,
        COUNT(CASE WHEN status = 'passed' THEN 1 END) as success_count,
        COUNT(CASE WHEN status = 'skipped' THEN 1 END) as skipped_count,
        ROUND(
            COUNT(CASE WHEN status = 'failed' THEN 1 END) * 100.0 / COUNT(*), 
            2
        ) as failure_rate,
        MAX(start_time) as last_execution,
        -- 获取最近的失败原因
        (
            SELECT failure_reason 
            FROM test_case_runs tcr2 
            WHERE tcr2.test_case_name = tcr.test_case_name 
                AND tcr2.status = 'failed' 
                AND tcr2.failure_reason IS NOT NULL
            ORDER BY tcr2.start_time DESC 
            LIMIT 1
        ) as latest_failure_reason,
        AVG(duration) as avg_duration_seconds,
        AVG(retry_attempt) as avg_retry_attempts
    FROM test_case_runs tcr
    WHERE start_time >= CURRENT_DATE - INTERVAL '30 days'
        AND start_time IS NOT NULL
        AND test_case_name IS NOT NULL
        AND test_case_name != ''
    GROUP BY test_case_name, project_name, flow_name, environment
    HAVING COUNT(*) >= 3  -- 至少执行过3次
        AND COUNT(CASE WHEN status = 'failed' THEN 1 END) > 0  -- 有失败记录
),
ranked_failures AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (ORDER BY failure_count DESC, failure_rate DESC) as rank
    FROM failure_stats
)
SELECT 
    rank,
    test_case_name,
    project_name,
    flow_name,
    environment,
    total_executions,
    failure_count,
    success_count,
    skipped_count,
    failure_rate,
    last_execution,
    latest_failure_reason,
    ROUND(avg_duration_seconds, 2) as avg_duration_seconds,
    ROUND(avg_retry_attempts, 1) as avg_retry_attempts,
    -- 计算稳定性得分 (越高越稳定)
    ROUND(100 - failure_rate, 2) as stability_score,
    -- 影响度评分 (失败次数 * 失败率)
    ROUND(failure_count * failure_rate / 100.0, 2) as impact_score
FROM ranked_failures
WHERE rank <= 10
ORDER BY rank;

-- 补充查询：按项目分组的失败用例统计
-- SELECT 
--     project_name,
--     COUNT(DISTINCT test_case_name) as unique_failing_tests,
--     SUM(failure_count) as total_failures,
--     ROUND(AVG(failure_rate), 2) as avg_failure_rate,
--     MAX(last_execution) as most_recent_failure
-- FROM ranked_failures
-- WHERE rank <= 20
-- GROUP BY project_name
-- ORDER BY total_failures DESC;
