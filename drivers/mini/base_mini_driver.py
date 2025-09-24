"""
OpenMautoTest 小程序基础驱动器

基于minium实现的微信小程序自动化测试驱动器
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import minium
    MINIUM_AVAILABLE = True
except ImportError:
    # 创建一个假的minium模块用于类型注解
    class _FakeMinium:
        class App:
            pass
        class Page:
            pass
        class Element:
            pass
        class Minium:
            pass
    
    minium = _FakeMinium()
    MINIUM_AVAILABLE = False

from common.base_page import BasePage
from common.logger import get_logger
from common.utils.file_utils import ensure_dir
from common.utils.time_utils import Timer
from configs.wechat import get_wechat_mini_config
from configs.settings import get_settings


class MiniDriverError(Exception):
    """小程序驱动器异常"""
    pass


class BaseMiniDriver:
    """小程序基础驱动器"""
    
    def __init__(self, project_path: Optional[str] = None):
        """初始化小程序驱动器
        
        Args:
            project_path: 小程序项目路径，None时使用配置
        """
        self.settings = get_settings()
        self.wechat_settings = get_wechat_mini_config()
        self.logger = get_logger("mini_driver")
        
        # 小程序配置
        self.project_path = project_path or self.wechat_settings.PROJECT_PATH
        self.app_id = self.wechat_settings.APP_ID
        
        # minium实例
        self._mini: Optional[minium.Minium] = None
        self._app: Optional[minium.App] = None
        
        # 截图目录
        self.screenshot_dir = ensure_dir(self.settings.get_output_dir() / "screenshots" / "mini")
        
        # 性能监控
        self.performance_metrics = {}
        
        self.logger.info(f"Initialized MiniDriver: {self.app_id}")
    
    def start(self) -> None:
        """启动小程序"""
        if not MINIUM_AVAILABLE:
            raise MiniDriverError("minium package is not installed. Please install it first.")
        
        try:
            # minium配置
            config = {
                "project_path": self.project_path,
                "dev_tool_path": self.wechat_settings.IDE_PATH,
                "port": self.wechat_settings.IDE_PORT,
                "close_ide": self.wechat_settings.AUTO_CLOSE_IDE,
                "test_port": self.wechat_settings.TEST_PORT,
                "assert_capture": self.wechat_settings.ASSERT_CAPTURE,
                "use_push": self.wechat_settings.USE_PUSH,
                "push_mini_timeout": self.wechat_settings.PUSH_TIMEOUT,
                "remote_connect_timeout": self.wechat_settings.CONNECT_TIMEOUT
            }
            
            # 启动minium
            self._mini = minium.Minium(config)
            
            # 启动小程序
            self._app = self._mini.start_app(
                app_id=self.app_id,
                path=self.wechat_settings.START_PAGE
            )
            
            # 设备配置
            if self.wechat_settings.DEVICE_ORIENTATION:
                self._app.screen_shot(
                    filename="device_check.png",
                    path=str(self.screenshot_dir)
                )
            
            self.logger.info("Mini program started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start mini program: {e}")
            self.stop()
            raise MiniDriverError(f"Mini program startup failed: {e}")
    
    def stop(self) -> None:
        """停止小程序"""
        try:
            if self._app:
                try:
                    self._app.close()
                except Exception as e:
                    self.logger.warning(f"Error closing app: {e}")
                self._app = None
            
            if self._mini:
                try:
                    self._mini.shutdown()
                except Exception as e:
                    self.logger.warning(f"Error shutting down minium: {e}")
                self._mini = None
            
            self.logger.info("Mini program stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping mini program: {e}")
    
    @property
    def app(self) -> minium.App:
        """获取小程序应用对象
        
        Returns:
            小程序应用对象
        
        Raises:
            MiniDriverError: 小程序未启动时抛出
        """
        if self._app is None:
            raise MiniDriverError("Mini program not started. Call start() first.")
        return self._app
    
    @property
    def mini(self) -> minium.Minium:
        """获取minium实例
        
        Returns:
            minium实例
        
        Raises:
            MiniDriverError: minium未初始化时抛出
        """
        if self._mini is None:
            raise MiniDriverError("Minium not initialized. Call start() first.")
        return self._mini
    
    def navigate_to(self, path: str, query: Optional[Dict[str, Any]] = None) -> None:
        """导航到指定页面
        
        Args:
            path: 页面路径
            query: 页面参数
        """
        try:
            with Timer() as timer:
                self.app.navigate_to(path, query or {})
                
                # 等待页面加载
                time.sleep(1)  # 给页面一些加载时间
            
            # 记录页面加载时间
            self.performance_metrics['page_load_time'] = timer.elapsed_time()
            self.logger.info(f"Navigated to {path} in {timer.elapsed_time():.2f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to {path}: {e}")
            raise MiniDriverError(f"Navigation failed: {e}")
    
    def redirect_to(self, path: str, query: Optional[Dict[str, Any]] = None) -> None:
        """重定向到指定页面
        
        Args:
            path: 页面路径
            query: 页面参数
        """
        try:
            self.app.redirect_to(path, query or {})
            time.sleep(1)  # 等待页面加载
            self.logger.info(f"Redirected to {path}")
            
        except Exception as e:
            self.logger.error(f"Failed to redirect to {path}: {e}")
            raise MiniDriverError(f"Redirect failed: {e}")
    
    def switch_tab(self, path: str) -> None:
        """切换到指定标签页
        
        Args:
            path: 标签页路径
        """
        try:
            self.app.switch_tab(path)
            time.sleep(0.5)  # 等待切换完成
            self.logger.info(f"Switched to tab: {path}")
            
        except Exception as e:
            self.logger.error(f"Failed to switch to tab {path}: {e}")
            raise MiniDriverError(f"Tab switch failed: {e}")
    
    def get_current_page(self) -> minium.Page:
        """获取当前页面对象
        
        Returns:
            当前页面对象
        """
        try:
            page = self.app.get_current_page()
            self.logger.info(f"Current page: {page.path}")
            return page
            
        except Exception as e:
            self.logger.error(f"Failed to get current page: {e}")
            raise MiniDriverError(f"Get current page failed: {e}")
    
    def wait_for_element(
        self,
        selector: str,
        timeout: Optional[int] = None,
        page: Optional[minium.Page] = None
    ) -> minium.Element:
        """等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）
            page: 页面对象，None时使用当前页面
        
        Returns:
            元素对象
        """
        try:
            target_page = page or self.get_current_page()
            timeout_sec = timeout or self.wechat_settings.DEFAULT_TIMEOUT
            
            element = target_page.get_element(selector, timeout=timeout_sec)
            if element is None:
                raise MiniDriverError(f"Element not found: {selector}")
            
            self.logger.info(f"Found element: {selector}")
            return element
            
        except Exception as e:
            self.logger.error(f"Failed to wait for element {selector}: {e}")
            raise MiniDriverError(f"Element wait failed: {e}")
    
    def click_element(
        self,
        selector: str,
        timeout: Optional[int] = None,
        page: Optional[minium.Page] = None
    ) -> None:
        """点击元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）
            page: 页面对象，None时使用当前页面
        """
        try:
            element = self.wait_for_element(selector, timeout, page)
            element.tap()
            time.sleep(0.5)  # 等待点击响应
            self.logger.info(f"Clicked element: {selector}")
            
        except Exception as e:
            self.logger.error(f"Failed to click element {selector}: {e}")
            raise MiniDriverError(f"Click failed: {e}")
    
    def input_text(
        self,
        selector: str,
        text: str,
        timeout: Optional[int] = None,
        page: Optional[minium.Page] = None,
        clear: bool = True
    ) -> None:
        """输入文本
        
        Args:
            selector: 输入框选择器
            text: 要输入的文本
            timeout: 超时时间（秒）
            page: 页面对象，None时使用当前页面
            clear: 是否先清空输入框
        """
        try:
            element = self.wait_for_element(selector, timeout, page)
            
            if clear:
                element.clear()
                time.sleep(0.2)
            
            element.input(text)
            time.sleep(0.5)  # 等待输入完成
            self.logger.info(f"Input text to {selector}: {text}")
            
        except Exception as e:
            self.logger.error(f"Failed to input text to {selector}: {e}")
            raise MiniDriverError(f"Input text failed: {e}")
    
    def get_element_text(
        self,
        selector: str,
        timeout: Optional[int] = None,
        page: Optional[minium.Page] = None
    ) -> str:
        """获取元素文本
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）
            page: 页面对象，None时使用当前页面
        
        Returns:
            元素文本内容
        """
        try:
            element = self.wait_for_element(selector, timeout, page)
            text = element.inner_text
            self.logger.info(f"Got text from {selector}: {text}")
            return text or ""
            
        except Exception as e:
            self.logger.error(f"Failed to get text from {selector}: {e}")
            raise MiniDriverError(f"Get text failed: {e}")
    
    def get_element_attribute(
        self,
        selector: str,
        attribute: str,
        timeout: Optional[int] = None,
        page: Optional[minium.Page] = None
    ) -> Optional[str]:
        """获取元素属性
        
        Args:
            selector: 元素选择器
            attribute: 属性名
            timeout: 超时时间（秒）
            page: 页面对象，None时使用当前页面
        
        Returns:
            属性值
        """
        try:
            element = self.wait_for_element(selector, timeout, page)
            value = element.attribute(attribute)
            self.logger.info(f"Got attribute {attribute} from {selector}: {value}")
            return value
            
        except Exception as e:
            self.logger.error(f"Failed to get attribute {attribute} from {selector}: {e}")
            raise MiniDriverError(f"Get attribute failed: {e}")
    
    def take_screenshot(self, filename: Optional[str] = None) -> Path:
        """截图
        
        Args:
            filename: 截图文件名，None时自动生成
        
        Returns:
            截图文件路径
        """
        try:
            if filename is None:
                timestamp = int(time.time() * 1000)
                filename = f"mini_screenshot_{timestamp}.png"
            
            screenshot_path = self.screenshot_dir / filename
            
            self.app.screen_shot(
                filename=filename,
                path=str(self.screenshot_dir)
            )
            
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            raise MiniDriverError(f"Screenshot failed: {e}")
    
    def execute_script(self, script: str, sync: bool = True) -> Any:
        """执行JavaScript代码
        
        Args:
            script: JavaScript代码
            sync: 是否同步执行
        
        Returns:
            脚本执行结果
        """
        try:
            if sync:
                result = self.app.evaluate(script)
            else:
                result = self.app.evaluate_async(script)
            
            self.logger.info(f"Executed script: {script[:50]}...")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute script: {e}")
            raise MiniDriverError(f"Script execution failed: {e}")
    
    def wait_for_page_ready(self, timeout: Optional[int] = None) -> None:
        """等待页面就绪
        
        Args:
            timeout: 超时时间（秒）
        """
        try:
            timeout_sec = timeout or self.wechat_settings.DEFAULT_TIMEOUT
            
            # 等待页面加载完成
            start_time = time.time()
            while time.time() - start_time < timeout_sec:
                try:
                    current_page = self.get_current_page()
                    if current_page:
                        break
                except Exception:
                    pass
                time.sleep(0.5)
            else:
                raise MiniDriverError("Page ready timeout")
            
            self.logger.info("Page is ready")
            
        except Exception as e:
            self.logger.error(f"Error waiting for page ready: {e}")
            raise MiniDriverError(f"Page ready wait failed: {e}")
    
    def scroll_to(self, x: int = 0, y: int = 0) -> None:
        """滚动页面
        
        Args:
            x: 水平滚动位置
            y: 垂直滚动位置
        """
        try:
            current_page = self.get_current_page()
            current_page.scroll_to(x, y)
            time.sleep(0.5)  # 等待滚动完成
            self.logger.info(f"Scrolled to ({x}, {y})")
            
        except Exception as e:
            self.logger.error(f"Failed to scroll to ({x}, {y}): {e}")
            raise MiniDriverError(f"Scroll failed: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息
        
        Returns:
            系统信息字典
        """
        try:
            system_info = self.app.call_wx_method("getSystemInfoSync")
            self.logger.info(f"System info: {system_info}")
            return system_info or {}
            
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标
        
        Returns:
            性能指标字典
        """
        try:
            # 获取基础性能信息
            system_info = self.get_system_info()
            
            metrics = {
                'device_info': {
                    'brand': system_info.get('brand', 'unknown'),
                    'model': system_info.get('model', 'unknown'),
                    'system': system_info.get('system', 'unknown'),
                    'version': system_info.get('version', 'unknown')
                },
                **self.performance_metrics
            }
            
            self.logger.info(f"Performance metrics: {metrics}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return self.performance_metrics.copy()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop()


class MiniPage(BasePage):
    """小程序页面基类"""
    
    def __init__(self, driver: BaseMiniDriver, path: Optional[str] = None):
        """初始化小程序页面
        
        Args:
            driver: 小程序驱动器实例
            path: 页面路径
        """
        super().__init__()
        self.driver = driver
        self.path = path
        self.logger = get_logger(f"mini_page_{self.__class__.__name__.lower()}")
    
    @property
    def page(self) -> minium.Page:
        """获取当前页面对象"""
        return self.driver.get_current_page()
    
    def open(self, path: Optional[str] = None, query: Optional[Dict[str, Any]] = None) -> None:
        """打开页面
        
        Args:
            path: 页面路径，None时使用初始化时的路径
            query: 页面参数
        """
        target_path = path or self.path
        if not target_path:
            raise MiniDriverError("No path specified for page")
        
        self.driver.navigate_to(target_path, query)
        self.wait_for_page_load()
    
    def wait_for_page_load(self) -> None:
        """等待页面加载完成"""
        self.driver.wait_for_page_ready()
    
    def is_element_present(self, selector: str) -> bool:
        """检查元素是否存在
        
        Args:
            selector: 元素选择器
        
        Returns:
            元素是否存在
        """
        try:
            self.driver.wait_for_element(selector, timeout=1)
            return True
        except MiniDriverError:
            return False
    
    def wait_for_element_visible(self, selector: str, timeout: Optional[int] = None) -> minium.Element:
        """等待元素可见
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）
        
        Returns:
            元素对象
        """
        return self.driver.wait_for_element(selector, timeout)


if __name__ == "__main__":
    # 测试小程序驱动器
    def test_mini_driver():
        print("Testing Mini Driver...")
        
        try:
            with BaseMiniDriver() as driver:
                # 等待小程序启动
                driver.wait_for_page_ready()
                
                # 获取当前页面
                current_page = driver.get_current_page()
                print(f"Current page: {current_page.path}")
                
                # 截图
                screenshot_path = driver.take_screenshot("test_mini_screenshot.png")
                print(f"Screenshot saved: {screenshot_path}")
                
                # 获取性能指标
                metrics = driver.get_performance_metrics()
                print(f"Performance metrics: {metrics}")
        
        except Exception as e:
            print(f"Mini driver test failed: {e}")
    
    # 运行测试
    test_mini_driver()
    print("Mini driver test completed.")
