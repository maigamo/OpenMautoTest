-- 测试用例成功率(趋势图/饼图)
-- 显示测试用例成功率的分布和趋势

-- 按日期的成功率趋势
SELECT 
    DATE(start_time) as test_date,
    COUNT(*) as total_tests,
    COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed_tests,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tests,
    COUNT(CASE WHEN status = 'skipped' THEN 1 END) as skipped_tests,
    ROUND(
        COUNT(CASE WHEN status = 'passed' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as success_rate,
    ROUND(AVG(duration), 2) as avg_duration_seconds
FROM test_case_runs 
WHERE start_time >= CURRENT_DATE - INTERVAL '30 days'
    AND start_time IS NOT NULL
    AND duration IS NOT NULL
GROUP BY DATE(start_time)
ORDER BY test_date DESC

UNION ALL

-- 按项目的成功率分布
SELECT 
    'Project: ' || COALESCE(project_name, 'Unknown') as test_date,
    COUNT(*) as total_tests,
    COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed_tests,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tests,
    COUNT(CASE WHEN status = 'skipped' THEN 1 END) as skipped_tests,
    ROUND(
        COUNT(CASE WHEN status = 'passed' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as success_rate,
    ROUND(AVG(duration), 2) as avg_duration_seconds
FROM test_case_runs 
WHERE start_time >= CURRENT_DATE - INTERVAL '7 days'
    AND start_time IS NOT NULL
    AND duration IS NOT NULL
GROUP BY project_name
ORDER BY success_rate DESC;
