-- 历史自动化执行总数(KPI)
-- 显示每日自动化测试执行的总数趋势

SELECT 
    DATE(start_time) as execution_date,
    COUNT(DISTINCT run_id) as total_executions,
    COUNT(*) as total_test_cases,
    COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed_cases,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_cases,
    COUNT(CASE WHEN status = 'skipped' THEN 1 END) as skipped_cases,
    ROUND(
        COUNT(CASE WHEN status = 'passed' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as pass_rate_percent
FROM test_case_runs 
WHERE start_time >= CURRENT_DATE - INTERVAL '30 days'
    AND start_time IS NOT NULL
GROUP BY DATE(start_time)
ORDER BY execution_date DESC;
