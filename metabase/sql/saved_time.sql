-- 节省人时累计曲线(面积图)
-- 计算自动化测试节省的人工时间

WITH automation_stats AS (
    SELECT 
        DATE(start_time) as test_date,
        COUNT(*) as total_automated_tests,
        COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed_tests,
        SUM(duration) as total_execution_time_seconds,
        COUNT(DISTINCT run_id) as total_runs,
        -- 假设每个自动化测试用例如果手工执行需要5分钟
        COUNT(*) * 5 * 60 as estimated_manual_time_seconds,
        -- 实际自动化执行时间
        SUM(duration) as actual_automation_time_seconds
    FROM test_case_runs 
    WHERE start_time >= CURRENT_DATE - INTERVAL '90 days'
        AND start_time IS NOT NULL
        AND duration IS NOT NULL
    GROUP BY DATE(start_time)
),
daily_savings AS (
    SELECT 
        test_date,
        total_automated_tests,
        passed_tests,
        total_runs,
        ROUND(total_execution_time_seconds / 60.0, 2) as actual_time_minutes,
        ROUND(estimated_manual_time_seconds / 60.0, 2) as estimated_manual_minutes,
        ROUND((estimated_manual_time_seconds - actual_automation_time_seconds) / 60.0, 2) as saved_time_minutes,
        ROUND((estimated_manual_time_seconds - actual_automation_time_seconds) / 3600.0, 2) as saved_time_hours,
        ROUND(
            CASE 
                WHEN estimated_manual_time_seconds > 0 THEN
                    (estimated_manual_time_seconds - actual_automation_time_seconds) * 100.0 / estimated_manual_time_seconds
                ELSE 0 
            END, 2
        ) as time_savings_percentage
    FROM automation_stats
    WHERE estimated_manual_time_seconds > 0
)
SELECT 
    test_date,
    total_automated_tests,
    passed_tests,
    total_runs,
    actual_time_minutes,
    estimated_manual_minutes,
    saved_time_minutes,
    saved_time_hours,
    time_savings_percentage,
    -- 累计节省时间
    SUM(saved_time_minutes) OVER (ORDER BY test_date) as cumulative_saved_minutes,
    SUM(saved_time_hours) OVER (ORDER BY test_date) as cumulative_saved_hours,
    ROUND(SUM(saved_time_hours) OVER (ORDER BY test_date) / 8.0, 1) as cumulative_saved_workdays,
    -- 计算ROI (假设一个测试工程师每小时成本100元)
    ROUND(SUM(saved_time_hours) OVER (ORDER BY test_date) * 100, 2) as cumulative_cost_savings_yuan
FROM daily_savings
ORDER BY test_date;
