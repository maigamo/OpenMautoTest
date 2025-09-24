"""
OpenMautoTest 小程序测试上下文

提供小程序测试的pytest fixtures和上下文管理
"""

from pathlib import Path
from typing import Dict, Any, Optional, Generator

import pytest

from common.logger import get_logger
from configs.wechat import get_wechat_mini_config
from configs.settings import get_settings
from drivers.mini import BaseMiniDriver, MiniDriverError
from orchestrator.recorder import get_recorder


class MiniTestContext:
    """小程序测试上下文"""
    
    def __init__(self, driver: BaseMiniDriver, test_name: str = "unknown"):
        """初始化小程序测试上下文
        
        Args:
            driver: 小程序驱动器实例
            test_name: 测试名称
        """
        self.driver = driver
        self.test_name = test_name
        self.logger = get_logger("mini_context")
        self.settings = get_settings()
        self.recorder = get_recorder()
        
        # 测试数据
        self.test_data: Dict[str, Any] = {}
        self.screenshots: list[Path] = []
        self.performance_metrics: Dict[str, Any] = {}
        
        # 测试记录
        self.test_record_id: Optional[int] = None
        self.step_counter = 0
        
        self.logger.info(f"Initialized Mini test context: {test_name}")
    
    def start_test_recording(self, test_info: Dict[str, Any]) -> None:
        """开始测试记录
        
        Args:
            test_info: 测试信息
        """
        try:
            # 准备测试记录数据
            record_data = {
                'test_case_name': self.test_name,
                'status': 'running',
                'browser_type': 'wechat_mini',
                'platform': 'mini_program',
                'test_data': test_info,
                **test_info
            }
            
            # 创建测试记录
            self.test_record_id = self.recorder.record_test_case_run(record_data)
            self.logger.info(f"Started test recording: {self.test_record_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to start test recording: {e}")
    
    def end_test_recording(self, test_result: str, error_info: Optional[Dict[str, Any]] = None) -> None:
        """结束测试记录
        
        Args:
            test_result: 测试结果 (passed/failed/skipped)
            error_info: 错误信息
        """
        try:
            if self.test_record_id is None:
                return
            
            # 获取性能指标
            self.performance_metrics = self.driver.get_performance_metrics()
            
            # 准备更新数据
            update_data = {
                'status': test_result,
                'screenshots': [str(p) for p in self.screenshots],
                'page_load_time': self.performance_metrics.get('page_load_time'),
                'platform': f"mini_program_{self.performance_metrics.get('device_info', {}).get('system', 'unknown')}"
            }
            
            if error_info:
                update_data.update({
                    'failure_reason': error_info.get('message', 'Unknown error'),
                    'error_details': error_info
                })
            
            # 更新测试记录
            success = self.recorder.db_recorder.update_test_case_run(self.test_record_id, update_data)
            if success:
                self.logger.info(f"Ended test recording: {self.test_record_id} -> {test_result}")
            else:
                self.logger.warning(f"Failed to update test record: {self.test_record_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to end test recording: {e}")
    
    def record_step(
        self,
        step_name: str,
        step_description: str = "",
        status: str = "passed",
        error_info: Optional[Dict[str, Any]] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录测试步骤
        
        Args:
            step_name: 步骤名称
            step_description: 步骤描述
            status: 步骤状态
            error_info: 错误信息
            input_data: 输入数据
            output_data: 输出数据
        """
        try:
            if self.test_record_id is None:
                return
            
            self.step_counter += 1
            
            # 准备步骤数据
            step_data = {
                'step_name': step_name,
                'step_description': step_description,
                'step_order': self.step_counter,
                'status': status,
                'input_data': input_data,
                'output_data': output_data
            }
            
            if error_info:
                step_data.update({
                    'error_message': error_info.get('message', 'Unknown error'),
                    'error_details': error_info
                })
            
            # 记录步骤
            step_id = self.recorder.record_test_step(self.test_record_id, step_data)
            self.logger.info(f"Recorded step {self.step_counter}: {step_name} -> {status}")
            
        except Exception as e:
            self.logger.error(f"Failed to record step {step_name}: {e}")
    
    def take_screenshot(self, name: Optional[str] = None) -> Path:
        """截图
        
        Args:
            name: 截图名称
        
        Returns:
            截图文件路径
        """
        try:
            if name is None:
                name = f"{self.test_name}_step_{self.step_counter}"
            
            screenshot_path = self.driver.take_screenshot(f"{name}.png")
            self.screenshots.append(screenshot_path)
            self.logger.info(f"Screenshot taken: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            raise MiniDriverError(f"Screenshot failed: {e}")
    
    def navigate_and_record(
        self,
        path: str,
        query: Optional[Dict[str, Any]] = None,
        step_name: str = "Navigate"
    ) -> None:
        """导航并记录
        
        Args:
            path: 页面路径
            query: 页面参数
            step_name: 步骤名称
        """
        try:
            self.driver.navigate_to(path, query)
            self.record_step(
                step_name=step_name,
                step_description=f"Navigate to {path}",
                status="passed",
                input_data={"path": path, "query": query}
            )
        except Exception as e:
            self.record_step(
                step_name=step_name,
                step_description=f"Navigate to {path}",
                status="failed",
                error_info={"message": str(e)}
            )
            raise
    
    def click_and_record(
        self,
        selector: str,
        step_name: str = "Click",
        timeout: Optional[int] = None
    ) -> None:
        """点击并记录
        
        Args:
            selector: 元素选择器
            step_name: 步骤名称
            timeout: 超时时间
        """
        try:
            self.driver.click_element(selector, timeout)
            self.record_step(
                step_name=step_name,
                step_description=f"Click element: {selector}",
                status="passed",
                input_data={"selector": selector, "timeout": timeout}
            )
        except Exception as e:
            self.record_step(
                step_name=step_name,
                step_description=f"Click element: {selector}",
                status="failed",
                error_info={"message": str(e)},
                input_data={"selector": selector, "timeout": timeout}
            )
            raise
    
    def input_and_record(
        self,
        selector: str,
        text: str,
        step_name: str = "Input Text",
        timeout: Optional[int] = None
    ) -> None:
        """输入文本并记录
        
        Args:
            selector: 输入框选择器
            text: 输入文本
            step_name: 步骤名称
            timeout: 超时时间
        """
        try:
            self.driver.input_text(selector, text, timeout)
            self.record_step(
                step_name=step_name,
                step_description=f"Input text to: {selector}",
                status="passed",
                input_data={"selector": selector, "text": text, "timeout": timeout}
            )
        except Exception as e:
            self.record_step(
                step_name=step_name,
                step_description=f"Input text to: {selector}",
                status="failed",
                error_info={"message": str(e)},
                input_data={"selector": selector, "text": text, "timeout": timeout}
            )
            raise
    
    def switch_tab_and_record(
        self,
        path: str,
        step_name: str = "Switch Tab"
    ) -> None:
        """切换标签页并记录
        
        Args:
            path: 标签页路径
            step_name: 步骤名称
        """
        try:
            self.driver.switch_tab(path)
            self.record_step(
                step_name=step_name,
                step_description=f"Switch to tab: {path}",
                status="passed",
                input_data={"path": path}
            )
        except Exception as e:
            self.record_step(
                step_name=step_name,
                step_description=f"Switch to tab: {path}",
                status="failed",
                error_info={"message": str(e)},
                input_data={"path": path}
            )
            raise
    
    def get_test_data(self, key: str, default: Any = None) -> Any:
        """获取测试数据
        
        Args:
            key: 数据键
            default: 默认值
        
        Returns:
            测试数据值
        """
        return self.test_data.get(key, default)
    
    def set_test_data(self, key: str, value: Any) -> None:
        """设置测试数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        self.test_data[key] = value
        self.logger.debug(f"Set test data: {key} = {value}")


# Pytest Fixtures

@pytest.fixture
def mini_driver() -> Generator[BaseMiniDriver, None, None]:
    """小程序驱动器fixture
    
    Yields:
        小程序驱动器实例
    """
    wechat_settings = get_wechat_mini_config()
    
    driver = BaseMiniDriver(project_path=wechat_settings.PROJECT_PATH)
    
    try:
        driver.start()
        yield driver
    finally:
        driver.stop()


@pytest.fixture
def mini_context(mini_driver: BaseMiniDriver, request) -> Generator[MiniTestContext, None, None]:
    """小程序测试上下文fixture
    
    Args:
        mini_driver: 小程序驱动器实例
        request: pytest请求对象
    
    Yields:
        小程序测试上下文实例
    """
    test_name = request.node.name
    context = MiniTestContext(mini_driver, test_name)
    
    # 开始测试记录
    test_info = {
        'run_id': getattr(request.config, 'run_id', 'unknown'),
        'environment': get_settings().ENVIRONMENT,
        'project_name': 'OpenMautoTest'
    }
    
    context.start_test_recording(test_info)
    
    try:
        yield context
        
        # 测试成功完成
        context.end_test_recording('passed')
        
    except Exception as e:
        # 测试失败
        error_info = {
            'message': str(e),
            'type': type(e).__name__
        }
        context.end_test_recording('failed', error_info)
        
        # 失败时截图
        try:
            context.take_screenshot('failure')
        except Exception:
            pass
        
        raise


@pytest.fixture
def mini_test_data() -> Dict[str, Any]:
    """小程序测试数据fixture
    
    Returns:
        测试数据字典
    """
    wechat_settings = get_wechat_mini_config()
    
    return {
        'app_id': wechat_settings.APP_ID,
        'start_page': wechat_settings.START_PAGE,
        'timeout': wechat_settings.DEFAULT_TIMEOUT,
        'test_user': {
            'username': 'test_user',
            'password': 'test_password'
        }
    }


# Pytest hooks

def pytest_runtest_setup(item):
    """测试设置钩子"""
    # 检查是否是小程序测试
    if hasattr(item, 'fixturenames') and 'mini_context' in item.fixturenames:
        logger = get_logger("pytest_mini")
        logger.info(f"Starting Mini program test: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """测试清理钩子"""
    # 检查是否是小程序测试
    if hasattr(item, 'fixturenames') and 'mini_context' in item.fixturenames:
        logger = get_logger("pytest_mini")
        logger.info(f"Finished Mini program test: {item.name}")


if __name__ == "__main__":
    # 测试小程序上下文
    def test_mini_context():
        print("Testing Mini Context...")
        
        try:
            with BaseMiniDriver() as driver:
                context = MiniTestContext(driver, "test_context")
                
                # 开始测试记录
                context.start_test_recording({'environment': 'test'})
                
                # 等待页面就绪
                driver.wait_for_page_ready()
                
                # 截图
                screenshot_path = context.take_screenshot("test")
                print(f"Screenshot: {screenshot_path}")
                
                # 结束测试记录
                context.end_test_recording('passed')
                
                print("Mini context test completed successfully")
        
        except Exception as e:
            print(f"Mini context test failed: {e}")
    
    # 运行测试
    test_mini_context()
