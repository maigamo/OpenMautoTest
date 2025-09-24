-- 历次自动化执行的测试用例数(趋势图)
-- 显示测试用例通过率的历史趋势

SELECT 
    DATE(start_time) as test_date,
    run_id,
    project_name,
    environment,
    COUNT(*) as total_cases,
    COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed_cases,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_cases,
    COUNT(CASE WHEN status = 'skipped' THEN 1 END) as skipped_cases,
    ROUND(
        COUNT(CASE WHEN status = 'passed' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as pass_rate,
    ROUND(AVG(duration), 2) as avg_duration_seconds,
    MIN(start_time) as run_start_time,
    MAX(end_time) as run_end_time
FROM test_case_runs 
WHERE start_time >= CURRENT_DATE - INTERVAL '90 days'
    AND start_time IS NOT NULL
    AND run_id IS NOT NULL
GROUP BY DATE(start_time), run_id, project_name, environment
HAVING COUNT(*) > 0
ORDER BY test_date DESC, run_start_time DESC;
