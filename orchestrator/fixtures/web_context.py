"""
OpenMautoTest Web测试上下文

提供Web端测试的pytest fixtures和上下文管理
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional

import pytest
import pytest_asyncio

from common.logger import get_logger
from common.reporter import get_allure_reporter, get_screenshot_manager
from configs.browser import get_browser_config
from configs.settings import get_settings
from drivers.web import BaseWebDriver, WebDriverError
from orchestrator.recorder import get_recorder


class WebTestContext:
    """Web测试上下文"""
    
    def __init__(self, driver: BaseWebDriver, test_name: str = "unknown"):
        """初始化Web测试上下文
        
        Args:
            driver: Web驱动器实例
            test_name: 测试名称
        """
        self.driver = driver
        self.test_name = test_name
        self.logger = get_logger("web_context")
        self.settings = get_settings()
        self.recorder = get_recorder()
        self.allure_reporter = get_allure_reporter()
        self.screenshot_manager = get_screenshot_manager()
        
        # 测试数据
        self.test_data: Dict[str, Any] = {}
        self.screenshots: list[Path] = []
        self.performance_metrics: Dict[str, Any] = {}
        
        # 测试记录
        self.test_record_id: Optional[int] = None
        self.step_counter = 0
        
        self.logger.info(f"Initialized Web test context: {test_name}")
    
    async def start_test_recording(self, test_info: Dict[str, Any]) -> None:
        """开始测试记录
        
        Args:
            test_info: 测试信息
        """
        try:
            # 准备测试记录数据
            record_data = {
                'test_case_name': self.test_name,
                'status': 'running',
                'browser_type': self.driver.browser_type,
                'platform': 'web',
                'test_data': test_info,
                **test_info
            }
            
            # 创建测试记录
            self.test_record_id = self.recorder.record_test_case_run(record_data)
            self.logger.info(f"Started test recording: {self.test_record_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to start test recording: {e}")
    
    async def end_test_recording(self, test_result: str, error_info: Optional[Dict[str, Any]] = None) -> None:
        """结束测试记录
        
        Args:
            test_result: 测试结果 (passed/failed/skipped)
            error_info: 错误信息
        """
        try:
            if self.test_record_id is None:
                return
            
            # 获取性能指标
            self.performance_metrics = await self.driver.get_performance_metrics()
            
            # 准备更新数据
            update_data = {
                'status': test_result,
                'screenshots': [str(p) for p in self.screenshots],
                'page_load_time': self.performance_metrics.get('page_load_time'),
                'network_time': self.performance_metrics.get('network_time')
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
    
    async def record_step(
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
    
    async def take_screenshot(self, name: Optional[str] = None) -> Path:
        """截图
        
        Args:
            name: 截图名称
        
        Returns:
            截图文件路径
        """
        try:
            if name is None:
                name = f"{self.test_name}_step_{self.step_counter}"
            
            # 使用驱动器截图
            screenshot_path = await self.driver.take_screenshot(f"{name}.png")
            
            # 读取截图数据并通过截图管理器保存（这样可以附加到Allure）
            try:
                with open(screenshot_path, "rb") as f:
                    screenshot_data = f.read()
                
                # 通过截图管理器保存（会自动附加到Allure）
                managed_screenshot_path = self.screenshot_manager.save_screenshot(
                    screenshot_data,
                    name,
                    attach_to_allure=True,
                    timestamp=False  # 驱动器已经添加了时间戳
                )
                
                self.screenshots.append(managed_screenshot_path)
                self.logger.info(f"Screenshot taken and attached to Allure: {managed_screenshot_path}")
                return managed_screenshot_path
                
            except Exception as e:
                # 如果Allure集成失败，仍返回原始截图
                self.logger.warning(f"Failed to integrate screenshot with Allure: {e}")
                self.screenshots.append(screenshot_path)
                return screenshot_path
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            raise WebDriverError(f"Screenshot failed: {e}")
    
    async def navigate_and_record(self, url: str, step_name: str = "Navigate") -> None:
        """导航并记录
        
        Args:
            url: 目标URL
            step_name: 步骤名称
        """
        try:
            await self.driver.navigate_to(url)
            await self.record_step(
                step_name=step_name,
                step_description=f"Navigate to {url}",
                status="passed",
                input_data={"url": url}
            )
        except Exception as e:
            await self.record_step(
                step_name=step_name,
                step_description=f"Navigate to {url}",
                status="failed",
                error_info={"message": str(e)}
            )
            raise
    
    async def click_and_record(
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
            await self.driver.click_element(selector, timeout)
            await self.record_step(
                step_name=step_name,
                step_description=f"Click element: {selector}",
                status="passed",
                input_data={"selector": selector, "timeout": timeout}
            )
        except Exception as e:
            await self.record_step(
                step_name=step_name,
                step_description=f"Click element: {selector}",
                status="failed",
                error_info={"message": str(e)},
                input_data={"selector": selector, "timeout": timeout}
            )
            raise
    
    async def fill_and_record(
        self,
        selector: str,
        text: str,
        step_name: str = "Fill Input",
        timeout: Optional[int] = None
    ) -> None:
        """填充输入框并记录
        
        Args:
            selector: 输入框选择器
            text: 输入文本
            step_name: 步骤名称
            timeout: 超时时间
        """
        try:
            await self.driver.fill_input(selector, text, timeout)
            await self.record_step(
                step_name=step_name,
                step_description=f"Fill input: {selector}",
                status="passed",
                input_data={"selector": selector, "text": text, "timeout": timeout}
            )
        except Exception as e:
            await self.record_step(
                step_name=step_name,
                step_description=f"Fill input: {selector}",
                status="failed",
                error_info={"message": str(e)},
                input_data={"selector": selector, "text": text, "timeout": timeout}
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

@pytest_asyncio.fixture
async def web_driver() -> AsyncGenerator[BaseWebDriver, None]:
    """Web驱动器fixture
    
    Yields:
        Web驱动器实例
    """
    browser_settings = get_browser_config()
    
    driver = BaseWebDriver(
        headless=browser_settings.HEADLESS,
        browser_type=browser_settings.BROWSER_TYPE
    )
    
    try:
        await driver.start()
        yield driver
    finally:
        await driver.stop()


@pytest_asyncio.fixture
async def web_context(web_driver: BaseWebDriver, request) -> AsyncGenerator[WebTestContext, None]:
    """Web测试上下文fixture
    
    Args:
        web_driver: Web驱动器实例
        request: pytest请求对象
    
    Yields:
        Web测试上下文实例
    """
    test_name = request.node.name
    context = WebTestContext(web_driver, test_name)
    
    # 开始测试记录
    # 确保有run_id，如果没有则生成一个
    import uuid
    run_id = getattr(request.config, 'run_id', None)
    if run_id is None:
        run_id = str(uuid.uuid4())
        request.config.run_id = run_id
    
    test_info = {
        'run_id': run_id,
        'environment': get_settings().ENVIRONMENT,
        'project_name': 'OpenMautoTest'
    }
    
    await context.start_test_recording(test_info)
    
    try:
        yield context
        
        # 测试成功完成
        await context.end_test_recording('passed')
        
    except Exception as e:
        # 测试失败
        error_info = {
            'message': str(e),
            'type': type(e).__name__
        }
        await context.end_test_recording('failed', error_info)
        
        # 失败时截图
        try:
            await context.take_screenshot('failure')
        except Exception:
            pass
        
        raise


@pytest.fixture
def web_test_data() -> Dict[str, Any]:
    """Web测试数据fixture
    
    Returns:
        测试数据字典
    """
    return {
        'base_url': get_settings().BASE_URL or 'https://example.com',
        'timeout': get_browser_config().DEFAULT_TIMEOUT,
        'test_user': {
            'username': 'test_user',
            'password': 'test_password'
        }
    }


# Pytest hooks

def pytest_configure(config):
    """pytest配置钩子"""
    # 设置运行ID
    import uuid
    config.run_id = str(uuid.uuid4())


def pytest_runtest_setup(item):
    """测试设置钩子"""
    logger = get_logger("pytest_web")
    logger.info(f"Starting Web test: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """测试清理钩子"""
    logger = get_logger("pytest_web")
    logger.info(f"Finished Web test: {item.name}")


if __name__ == "__main__":
    # 测试Web上下文
    async def test_web_context():
        print("Testing Web Context...")
        
        try:
            async with BaseWebDriver(headless=True) as driver:
                context = WebTestContext(driver, "test_context")
                
                # 开始测试记录
                await context.start_test_recording({'environment': 'test'})
                
                # 导航并记录
                await context.navigate_and_record("https://example.com")
                
                # 截图
                screenshot_path = await context.take_screenshot("test")
                print(f"Screenshot: {screenshot_path}")
                
                # 结束测试记录
                await context.end_test_recording('passed')
                
                print("Web context test completed successfully")
        
        except Exception as e:
            print(f"Web context test failed: {e}")
    
    # 运行测试
    asyncio.run(test_web_context())
