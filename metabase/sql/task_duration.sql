-- 单次任务总耗时(趋势图)
-- 显示每次测试运行的总耗时趋势

WITH run_durations AS (
    SELECT 
        run_id,
        project_name,
        environment,
        flow_name,
        MIN(start_time) as run_start_time,
        MAX(end_time) as run_end_time,
        COUNT(*) as total_test_cases,
        COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed_cases,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_cases,
        SUM(duration) as total_duration_seconds,
        AVG(duration) as avg_case_duration,
        MAX(duration) as max_case_duration,
        MIN(duration) as min_case_duration
    FROM test_case_runs 
    WHERE start_time >= CURRENT_DATE - INTERVAL '60 days'
        AND start_time IS NOT NULL
        AND end_time IS NOT NULL
        AND duration IS NOT NULL
        AND run_id IS NOT NULL
    GROUP BY run_id, project_name, environment, flow_name
)
SELECT 
    DATE(run_start_time) as execution_date,
    run_start_time,
    run_id,
    project_name,
    environment,
    flow_name,
    total_test_cases,
    passed_cases,
    failed_cases,
    ROUND(passed_cases * 100.0 / total_test_cases, 2) as pass_rate,
    ROUND(total_duration_seconds, 2) as total_duration_seconds,
    ROUND(total_duration_seconds / 60.0, 2) as total_duration_minutes,
    ROUND(avg_case_duration, 2) as avg_case_duration_seconds,
    ROUND(max_case_duration, 2) as max_case_duration_seconds,
    ROUND(min_case_duration, 2) as min_case_duration_seconds,
    CASE 
        WHEN run_end_time IS NOT NULL AND run_start_time IS NOT NULL THEN
            ROUND(EXTRACT(EPOCH FROM (run_end_time - run_start_time)), 2)
        ELSE total_duration_seconds
    END as actual_run_duration_seconds
FROM run_durations
WHERE total_test_cases > 0
ORDER BY run_start_time DESC;
