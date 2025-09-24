"""
OpenMautoTest 流程级别的pytest配置

提供流程测试的fixtures和配置
"""

import uuid
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Generator, Optional

from common.logger import get_logger
from configs.settings import get_settings
from orchestrator.recorder import get_recorder


logger = get_logger("flows_conftest")


# 流程级别的fixtures

@pytest.fixture(scope="session")
def flow_session_id() -> str:
    """生成流程会话ID
    
    Returns:
        会话ID字符串
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Generated flow session ID: {session_id}")
    return session_id


@pytest.fixture(scope="session")
def flow_test_environment() -> Dict[str, Any]:
    """流程测试环境信息
    
    Returns:
        环境信息字典
    """
    settings = get_settings()
    
    env_info = {
        "environment": settings.ENVIRONMENT,
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "test_start_time": datetime.now(),
        "output_dir": Path("output").resolve(),
        "log_level": settings.LOG_LEVEL
    }
    
    logger.info(f"Flow test environment: {env_info['environment']}")
    return env_info


@pytest.fixture(scope="function")
def flow_test_context(request, flow_session_id, flow_test_environment) -> Dict[str, Any]:
    """流程测试上下文
    
    Args:
        request: pytest请求对象
        flow_session_id: 流程会话ID
        flow_test_environment: 流程测试环境
    
    Returns:
        测试上下文字典
    """
    test_id = str(uuid.uuid4())
    test_name = request.node.name
    
    context = {
        "test_id": test_id,
        "test_name": test_name,
        "session_id": flow_session_id,
        "module_name": request.module.__name__,
        "class_name": getattr(request.cls, "__name__", None),
        "start_time": datetime.now(),
        "environment": flow_test_environment,
        "markers": [mark.name for mark in request.node.iter_markers()],
        "parameters": getattr(request, "param", {})
    }
    
    logger.info(f"Created flow test context for: {test_name} [{test_id}]")
    return context


@pytest.fixture(scope="function")
def flow_data_recorder(flow_test_context):
    """流程数据记录器
    
    Args:
        flow_test_context: 流程测试上下文
    
    Yields:
        数据记录器实例
    """
    recorder = get_recorder()
    test_context = flow_test_context
    
    # 记录测试开始
    test_record = {
        "run_id": test_context["session_id"],
        "test_case_name": test_context["test_name"],
        "project_name": test_context["environment"]["project_name"],
        "environment": test_context["environment"]["environment"],
        "platform": "flow_test",
        "status": "running",
        "start_time": test_context["start_time"],
        "test_data": {
            "test_id": test_context["test_id"],
            "module": test_context["module_name"],
            "class": test_context["class_name"],
            "markers": test_context["markers"]
        }
    }
    
    try:
        record_id = recorder.record_test_case_run(test_record)
        test_context["record_id"] = record_id
        
        yield recorder
        
        # 测试成功完成
        if record_id:
            end_time = datetime.now()
            duration = (end_time - test_context["start_time"]).total_seconds()
            
            update_data = {
                "status": "passed",
                "end_time": end_time,
                "duration": duration
            }
            
            recorder.db_recorder.update_test_case_run(record_id, update_data)
            logger.info(f"Flow test completed successfully: {test_context['test_name']}")
    
    except Exception as e:
        # 测试失败
        record_id = test_context.get("record_id")
        if record_id:
            end_time = datetime.now()
            duration = (end_time - test_context["start_time"]).total_seconds()
            
            update_data = {
                "status": "failed",
                "end_time": end_time,
                "duration": duration,
                "failure_reason": str(e),
                "error_details": {
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                }
            }
            
            recorder.db_recorder.update_test_case_run(record_id, update_data)
            logger.error(f"Flow test failed: {test_context['test_name']} - {e}")
        
        raise


@pytest.fixture(scope="function")
def flow_performance_tracker() -> Dict[str, Any]:
    """流程性能跟踪器
    
    Returns:
        性能跟踪器字典
    """
    tracker = {
        "start_time": datetime.now(),
        "checkpoints": [],
        "metrics": {}
    }
    
    def add_checkpoint(name: str, data: Optional[Dict[str, Any]] = None):
        """添加性能检查点"""
        checkpoint = {
            "name": name,
            "timestamp": datetime.now(),
            "data": data or {}
        }
        tracker["checkpoints"].append(checkpoint)
        logger.debug(f"Performance checkpoint: {name}")
    
    def get_duration(from_checkpoint: str = None, to_checkpoint: str = None) -> float:
        """获取时间段"""
        if from_checkpoint is None:
            start_time = tracker["start_time"]
        else:
            start_checkpoint = next(
                (cp for cp in tracker["checkpoints"] if cp["name"] == from_checkpoint),
                None
            )
            start_time = start_checkpoint["timestamp"] if start_checkpoint else tracker["start_time"]
        
        if to_checkpoint is None:
            end_time = datetime.now()
        else:
            end_checkpoint = next(
                (cp for cp in tracker["checkpoints"] if cp["name"] == to_checkpoint),
                None
            )
            end_time = end_checkpoint["timestamp"] if end_checkpoint else datetime.now()
        
        return (end_time - start_time).total_seconds()
    
    def set_metric(name: str, value: Any):
        """设置性能指标"""
        tracker["metrics"][name] = value
        logger.debug(f"Performance metric: {name} = {value}")
    
    # 添加方法到tracker
    tracker["add_checkpoint"] = add_checkpoint
    tracker["get_duration"] = get_duration
    tracker["set_metric"] = set_metric
    
    return tracker


# 流程测试标记

def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "web_flow: 标记Web端流程测试"
    )
    config.addinivalue_line(
        "markers", "mini_flow: 标记小程序端流程测试"
    )
    config.addinivalue_line(
        "markers", "cross_platform: 标记跨平台流程测试"
    )
    config.addinivalue_line(
        "markers", "smoke: 标记冒烟测试"
    )
    config.addinivalue_line(
        "markers", "regression: 标记回归测试"
    )
    config.addinivalue_line(
        "markers", "performance: 标记性能测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试项收集"""
    # 为不同类型的测试添加标记
    for item in items:
        # 根据测试名称自动添加标记
        if "web" in item.name.lower():
            item.add_marker(pytest.mark.web_flow)
        
        if "mini" in item.name.lower():
            item.add_marker(pytest.mark.mini_flow)
        
        if "cross_platform" in item.name.lower():
            item.add_marker(pytest.mark.cross_platform)
        
        if "error" in item.name.lower() or "retry" in item.name.lower():
            item.add_marker(pytest.mark.slow)
        
        # 根据文件路径添加标记
        if "login_and_buy" in str(item.fspath):
            item.add_marker(pytest.mark.regression)


def pytest_runtest_setup(item):
    """测试设置钩子"""
    logger.info(f"Setting up flow test: {item.name}")
    
    # 检查测试标记
    markers = [mark.name for mark in item.iter_markers()]
    if markers:
        logger.debug(f"Test markers: {markers}")
    
    # 检查跳过条件
    if item.get_closest_marker("skip"):
        pytest.skip("Test marked for skipping")
    
    # 检查平台特定的跳过条件
    if item.get_closest_marker("web_flow"):
        # 检查Web测试环境
        try:
            from configs.browser import get_browser_config
            browser_config = get_browser_config()
            logger.debug(f"Web test environment ready: {browser_config.BROWSER_TYPE}")
        except Exception as e:
            pytest.skip(f"Web test environment not available: {e}")
    
    if item.get_closest_marker("mini_flow"):
        # 检查小程序测试环境
        try:
            from configs.wechat import get_wechat_mini_config
            mini_config = get_wechat_mini_config()
            logger.debug(f"Mini program test environment ready: {mini_config.APP_ID}")
        except Exception as e:
            pytest.skip(f"Mini program test environment not available: {e}")


def pytest_runtest_teardown(item, nextitem):
    """测试清理钩子"""
    logger.info(f"Tearing down flow test: {item.name}")
    
    # 清理测试资源
    try:
        # 清理临时文件
        temp_dir = Path("output/temp")
        if temp_dir.exists():
            import shutil
            for file in temp_dir.glob("*"):
                if file.is_file() and file.stat().st_mtime < (datetime.now().timestamp() - 3600):
                    file.unlink()
    except Exception as e:
        logger.warning(f"Failed to cleanup temp files: {e}")


def pytest_runtest_makereport(item, call):
    """生成测试报告钩子"""
    if call.when == "call":
        # 测试执行阶段
        outcome = "passed" if call.excinfo is None else "failed"
        duration = call.duration
        
        logger.info(f"Flow test result: {item.name} -> {outcome} ({duration:.2f}s)")
        
        # 记录到性能跟踪器
        if hasattr(item, "funcargs") and "flow_performance_tracker" in item.funcargs:
            tracker = item.funcargs["flow_performance_tracker"]
            tracker["set_metric"]("test_outcome", outcome)
            tracker["set_metric"]("test_duration", duration)


def pytest_sessionstart(session):
    """会话开始钩子"""
    logger.info("Starting flow test session")
    
    # 确保输出目录存在
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    (output_dir / "screenshots").mkdir(exist_ok=True)
    (output_dir / "logs").mkdir(exist_ok=True)
    (output_dir / "records").mkdir(exist_ok=True)
    (output_dir / "allure-results").mkdir(exist_ok=True)


def pytest_sessionfinish(session, exitstatus):
    """会话结束钩子"""
    logger.info(f"Flow test session finished with exit status: {exitstatus}")
    
    # 生成会话摘要
    if hasattr(session, "testscollected"):
        total_tests = session.testscollected
        passed_tests = len([item for item in session.items if not hasattr(item, "rep_call") or item.rep_call.passed])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Session summary: {total_tests} total, {passed_tests} passed, {failed_tests} failed")


# 参数化测试支持

@pytest.fixture(scope="function")
def test_environments():
    """测试环境参数化数据"""
    return [
        {"name": "dev", "base_url": "https://dev.example.com"},
        {"name": "test", "base_url": "https://test.example.com"},
        {"name": "staging", "base_url": "https://staging.example.com"}
    ]


@pytest.fixture(scope="function")
def test_users():
    """测试用户参数化数据"""
    return [
        {"username": "test_user_1", "password": "password123", "role": "user"},
        {"username": "test_admin", "password": "admin123", "role": "admin"},
        {"username": "test_guest", "password": "guest123", "role": "guest"}
    ]


@pytest.fixture(scope="function")
def test_products():
    """测试商品参数化数据"""
    return [
        {"name": "测试商品A", "price": "99.99", "category": "electronics"},
        {"name": "测试商品B", "price": "199.99", "category": "clothing"},
        {"name": "测试商品C", "price": "299.99", "category": "books"}
    ]


# 自定义断言辅助函数

def assert_flow_success(flow_result: Dict[str, Any], min_completed_steps: int = 1):
    """断言流程执行成功
    
    Args:
        flow_result: 流程执行结果
        min_completed_steps: 最少完成步骤数
    """
    assert flow_result["status"] == "passed", f"Flow failed: {flow_result.get('error', 'Unknown error')}"
    assert flow_result["completed_steps"] >= min_completed_steps, f"Too few steps completed: {flow_result['completed_steps']}"
    assert flow_result["failed_steps"] == 0, f"Some steps failed: {flow_result['failed_steps']}"


def assert_step_success(flow_result: Dict[str, Any], step_name: str):
    """断言特定步骤执行成功
    
    Args:
        flow_result: 流程执行结果
        step_name: 步骤名称
    """
    step = next((s for s in flow_result["steps"] if s["name"] == step_name), None)
    assert step is not None, f"Step '{step_name}' not found in flow result"
    assert step["status"] == "passed", f"Step '{step_name}' failed: {step.get('error_message', 'Unknown error')}"


def assert_shared_data_exists(flow_result: Dict[str, Any], key: str, expected_value: Any = None):
    """断言共享数据存在
    
    Args:
        flow_result: 流程执行结果
        key: 数据键
        expected_value: 期望值（可选）
    """
    shared_data = flow_result.get("shared_data", {})
    assert key in shared_data, f"Shared data key '{key}' not found"
    
    if expected_value is not None:
        actual_value = shared_data[key]
        assert actual_value == expected_value, f"Shared data '{key}': expected {expected_value}, got {actual_value}"


if __name__ == "__main__":
    print("Flow conftest.py loaded successfully")
    print("Available fixtures:")
    print("  - flow_session_id: 生成流程会话ID")
    print("  - flow_test_environment: 流程测试环境信息")
    print("  - flow_test_context: 流程测试上下文")
    print("  - flow_data_recorder: 流程数据记录器")
    print("  - flow_performance_tracker: 流程性能跟踪器")
    print("  - test_environments: 测试环境参数化数据")
    print("  - test_users: 测试用户参数化数据")
    print("  - test_products: 测试商品参数化数据")
