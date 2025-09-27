"""
OpenMautoTest Web端基础驱动器

基于Playwright实现的Web端自动化测试驱动器
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import (
    async_playwright, Browser, BrowserContext, Page, Playwright,
    ElementHandle, Locator, TimeoutError as PlaywrightTimeoutError
)

from common.base_page import BasePage
from common.logger import get_logger
from common.utils.file_utils import ensure_dir
from common.utils.time_utils import Timer
from configs.browser import get_browser_config
from configs.settings import get_settings
from .playwright_proxy import PlaywrightProxy, PlaywrightOperations


class WebDriverError(Exception):
    """Web驱动器异常"""
    pass


class BaseWebDriver:
    """Web端基础驱动器"""
    
    def __init__(self, headless: bool = None, browser_type: str = None):
        """初始化Web驱动器
        
        Args:
            headless: 是否无头模式，None时使用配置
            browser_type: 浏览器类型，None时使用配置
        """
        self.settings = get_settings()
        self.browser_settings = get_browser_config()
        self.logger = get_logger("web_driver")
        
        # 浏览器配置
        self.browser_type = browser_type or self.browser_settings.BROWSER_TYPE
        # self.headless = headless if headless is not None else self.browser_settings.HEADLESS
        self.headless = False    # 调试代码，以非无头模式运行浏览器驱动（开发过程保留）
        
        # 浏览器实例
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        # 截图目录
        self.screenshot_dir = ensure_dir(self.settings.get_output_dir() / "screenshots")
        
        # 性能监控
        self.performance_metrics = {}
        
        # 初始化Playwright代理和操作类
        self._proxy = PlaywrightProxy()
        self._operations = PlaywrightOperations()
        
        self.logger.info(f"Initialized WebDriver: {self.browser_type}, headless={self.headless}")
    
    async def start(self) -> None:
        """启动浏览器"""
        try:
            self._playwright = await async_playwright().start()
            
            # 选择浏览器
            if self.browser_type.lower() == 'chromium':
                browser_launcher = self._playwright.chromium
            elif self.browser_type.lower() == 'firefox':
                browser_launcher = self._playwright.firefox
            elif self.browser_type.lower() == 'webkit':
                browser_launcher = self._playwright.webkit
            else:
                raise WebDriverError(f"Unsupported browser type: {self.browser_type}")
            
            # 启动浏览器
            launch_options = {
                'headless': self.headless,
                'args': self.browser_settings.BROWSER_ARGS,
                'slow_mo': self.browser_settings.SLOW_MO if self.settings.is_development() else 0
            }
            
            # 添加调试选项
            if self.browser_settings.DEBUG_MODE:
                launch_options.update({
                    'devtools': True,
                    'slow_mo': 1000
                })
            
            self._browser = await browser_launcher.launch(**launch_options)
            
            # 创建浏览器上下文
            context_options = {
                'viewport': {
                    'width': self.browser_settings.WINDOW_WIDTH,
                    'height': self.browser_settings.WINDOW_HEIGHT
                },
                'ignore_https_errors': True,
                'record_video_dir': str(self.settings.get_output_dir() / "videos") if self.browser_settings.RECORD_VIDEO else None
            }
            
            # 移动设备模拟
            if self.browser_settings.MOBILE_DEVICE:
                device = self._playwright.devices.get(self.browser_settings.MOBILE_DEVICE)
                if device:
                    context_options.update(device)
            
            self._context = await self._browser.new_context(**context_options)
            
            # 设置默认超时
            self._context.set_default_timeout(self.browser_settings.DEFAULT_TIMEOUT * 1000)
            
            # 创建页面
            self._page = await self._context.new_page()
            
            # 设置代理对象的Page引用
            self._proxy.set_page(self._page)
            self._operations.set_page(self._page)
            
            # 监听控制台消息
            self._page.on("console", self._handle_console_message)
            
            # 监听页面错误
            self._page.on("pageerror", self._handle_page_error)
            
            self.logger.info("Browser started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}")
            await self.stop()
            raise WebDriverError(f"Browser startup failed: {e}")
    
    async def stop(self) -> None:
        """停止浏览器"""
        try:
            if self._page:
                await self._page.close()
                self._page = None
            
            if self._context:
                await self._context.close()
                self._context = None
            
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            
            self.logger.info("Browser stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping browser: {e}")
    
    def _handle_console_message(self, msg):
        """处理控制台消息"""
        level = msg.type
        text = msg.text
        
        if level == "error":
            self.logger.error(f"Console error: {text}")
        elif level == "warning":
            self.logger.warning(f"Console warning: {text}")
        elif self.settings.is_development():
            self.logger.debug(f"Console {level}: {text}")
    
    def _handle_page_error(self, error):
        """处理页面错误"""
        self.logger.error(f"Page error: {error}")
    
    @property
    def page(self) -> Page:
        """获取当前页面对象
        
        Returns:
            当前页面对象
        
        Raises:
            WebDriverError: 浏览器未启动时抛出
        """
        if self._page is None:
            raise WebDriverError("Browser not started. Call start() first.")
        return self._page
    
    @property
    def context(self) -> BrowserContext:
        """获取当前浏览器上下文
        
        Returns:
            当前浏览器上下文
        
        Raises:
            WebDriverError: 浏览器未启动时抛出
        """
        if self._context is None:
            raise WebDriverError("Browser not started. Call start() first.")
        return self._context
    
    async def navigate_to(self, url: str, wait_until: str = "load") -> None:
        """导航到指定URL
        
        Args:
            url: 目标URL
            wait_until: 等待条件 (load, domcontentloaded, networkidle)
        """
        try:
            with Timer() as timer:
                await self.page.goto(url, wait_until=wait_until)
            
            # 记录页面加载时间
            self.performance_metrics['page_load_time'] = timer.elapsed_time()
            self.logger.info(f"Navigated to {url} in {timer.elapsed_time():.2f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {e}")
            raise WebDriverError(f"Navigation failed: {e}")
    
    async def wait_for_element(
        self,
        selector: str,
        timeout: Optional[int] = None,
        state: str = "visible"
    ) -> Locator:
        """等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            state: 等待状态 (visible, hidden, attached, detached)
        
        Returns:
            元素定位器
        """
        try:
            timeout_ms = timeout or self.browser_settings.DEFAULT_TIMEOUT * 1000
            locator = self.page.locator(selector)
            await locator.wait_for(state=state, timeout=timeout_ms)
            return locator
            
        except PlaywrightTimeoutError as e:
            self.logger.error(f"Element not found: {selector} (timeout: {timeout_ms}ms)")
            raise WebDriverError(f"Element wait timeout: {selector}")
        except Exception as e:
            self.logger.error(f"Error waiting for element {selector}: {e}")
            raise WebDriverError(f"Element wait error: {e}")
    
    async def click_element(
        self,
        selector: str,
        timeout: Optional[int] = None,
        force: bool = False
    ) -> None:
        """点击元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            force: 是否强制点击
        """
        try:
            locator = await self.wait_for_element(selector, timeout)
            await locator.click(force=force)
            self.logger.info(f"Clicked element: {selector}")
            
        except Exception as e:
            self.logger.error(f"Failed to click element {selector}: {e}")
            raise WebDriverError(f"Click failed: {e}")
    
    async def fill_input(
        self,
        selector: str,
        text: str,
        timeout: Optional[int] = None,
        clear: bool = True
    ) -> None:
        """填充输入框
        
        Args:
            selector: 输入框选择器
            text: 要填充的文本
            timeout: 超时时间（毫秒）
            clear: 是否先清空输入框
        """
        try:
            locator = await self.wait_for_element(selector, timeout)
            
            if clear:
                await locator.clear()
            
            await locator.fill(text)
            self.logger.info(f"Filled input {selector} with: {text}")
            
        except Exception as e:
            self.logger.error(f"Failed to fill input {selector}: {e}")
            raise WebDriverError(f"Fill input failed: {e}")
    
    async def get_text(
        self,
        selector: str,
        timeout: Optional[int] = None
    ) -> str:
        """获取元素文本
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
        
        Returns:
            元素文本内容
        """
        try:
            locator = await self.wait_for_element(selector, timeout)
            text = await locator.text_content()
            self.logger.info(f"Got text from {selector}: {text}")
            return text or ""
            
        except Exception as e:
            self.logger.error(f"Failed to get text from {selector}: {e}")
            raise WebDriverError(f"Get text failed: {e}")
    
    async def get_attribute(
        self,
        selector: str,
        attribute: str,
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """获取元素属性
        
        Args:
            selector: 元素选择器
            attribute: 属性名
            timeout: 超时时间（毫秒）
        
        Returns:
            属性值
        """
        try:
            locator = await self.wait_for_element(selector, timeout)
            value = await locator.get_attribute(attribute)
            self.logger.info(f"Got attribute {attribute} from {selector}: {value}")
            return value
            
        except Exception as e:
            self.logger.error(f"Failed to get attribute {attribute} from {selector}: {e}")
            raise WebDriverError(f"Get attribute failed: {e}")
    
    async def take_screenshot(
        self,
        filename: Optional[str] = None,
        full_page: bool = True
    ) -> Path:
        """截图
        
        Args:
            filename: 截图文件名，None时自动生成
            full_page: 是否全页截图
        
        Returns:
            截图文件路径
        """
        try:
            if filename is None:
                timestamp = int(time.time() * 1000)
                filename = f"screenshot_{timestamp}.png"
            
            screenshot_path = self.screenshot_dir / filename
            
            await self.page.screenshot(
                path=str(screenshot_path),
                full_page=full_page
            )
            
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            raise WebDriverError(f"Screenshot failed: {e}")
    
    async def execute_javascript(self, script: str, *args) -> Any:
        """执行JavaScript代码
        
        Args:
            script: JavaScript代码
            *args: 传递给脚本的参数
        
        Returns:
            脚本执行结果
        """
        try:
            result = await self.page.evaluate(script, *args)
            self.logger.info(f"Executed JavaScript: {script[:50]}...")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute JavaScript: {e}")
            raise WebDriverError(f"JavaScript execution failed: {e}")
    
    async def wait_for_network_idle(self, timeout: Optional[int] = None) -> None:
        """等待网络空闲
        
        Args:
            timeout: 超时时间（毫秒）
        """
        try:
            timeout_ms = timeout or self.browser_settings.DEFAULT_TIMEOUT * 1000
            await self.page.wait_for_load_state("networkidle", timeout=timeout_ms)
            self.logger.info("Network is idle")
            
        except PlaywrightTimeoutError:
            self.logger.warning("Network idle timeout")
        except Exception as e:
            self.logger.error(f"Error waiting for network idle: {e}")
    
    async def scroll_to_element(self, selector: str, timeout: Optional[int] = None) -> None:
        """滚动到元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
        """
        try:
            locator = await self.wait_for_element(selector, timeout)
            await locator.scroll_into_view_if_needed()
            self.logger.info(f"Scrolled to element: {selector}")
            
        except Exception as e:
            self.logger.error(f"Failed to scroll to element {selector}: {e}")
            raise WebDriverError(f"Scroll failed: {e}")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标
        
        Returns:
            性能指标字典
        """
        try:
            # 获取性能时间线
            performance_timing = await self.page.evaluate("""
                () => {
                    const timing = performance.timing;
                    return {
                        navigationStart: timing.navigationStart,
                        domContentLoadedEventEnd: timing.domContentLoadedEventEnd,
                        loadEventEnd: timing.loadEventEnd,
                        domComplete: timing.domComplete
                    };
                }
            """)
            
            # 计算各个阶段的耗时
            nav_start = performance_timing['navigationStart']
            dom_ready = performance_timing['domContentLoadedEventEnd'] - nav_start
            page_load = performance_timing['loadEventEnd'] - nav_start
            dom_complete = performance_timing['domComplete'] - nav_start
            
            metrics = {
                'dom_ready_time': dom_ready,
                'page_load_time': page_load,
                'dom_complete_time': dom_complete,
                **self.performance_metrics
            }
            
            self.logger.info(f"Performance metrics: {metrics}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return self.performance_metrics.copy()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.stop()
    
    # ===================
    # Playwright操作代理属性
    # ===================
    
    @property
    def playwright_ops(self) -> PlaywrightOperations:
        """获取Playwright操作对象
        
        提供对常用Playwright操作的封装访问
        
        Returns:
            PlaywrightOperations实例
            
        Examples:
            # 使用封装的操作方法
            await driver.playwright_ops.screenshot("test.png")
            button = await driver.playwright_ops.get_by_role("button", name="Submit")
            await driver.playwright_ops.evaluate("document.title")
        """
        return self._operations
    
    # ===================
    # 便捷方法（常用操作的直接访问）
    # ===================
    
    async def screenshot(self, path: Optional[str] = None, **kwargs) -> bytes:
        """截取页面截图（便捷方法）
        
        Args:
            path: 保存路径，为None时自动生成
            **kwargs: 其他参数
        
        Returns:
            截图字节数据
        """
        if path is None:
            timestamp = int(time.time() * 1000)
            path = str(self.screenshot_dir / f"screenshot_{timestamp}.png")
        
        return await self._operations.screenshot(path, **kwargs)
    
    async def get_by_role(self, role: str, **kwargs) -> Locator:
        """通过角色获取元素定位器（便捷方法）"""
        return await self._operations.get_by_role(role, **kwargs)
    
    async def get_by_text(self, text: str, **kwargs) -> Locator:
        """通过文本内容获取元素定位器（便捷方法）"""
        return await self._operations.get_by_text(text, **kwargs)
    
    async def get_by_test_id(self, test_id: str) -> Locator:
        """通过测试ID获取元素定位器（便捷方法）"""
        return await self._operations.get_by_test_id(test_id)
    
    # ===================
    # 动态代理实现
    # ===================
    
    def __getattr__(self, name: str) -> Any:
        """动态代理，转发调用给Playwright对象
        
        这个方法实现了对Playwright Page API的动态代理，允许直接调用Playwright的方法
        而不需要显式地通过self._page访问。
        
        代理优先级：
        1. 首先检查是否为PlaywrightOperations的方法
        2. 然后使用PlaywrightProxy进行代理
        3. 如果都不是，抛出AttributeError异常
        
        Args:
            name: 要调用的方法或属性名
            
        Returns:
            Playwright对象的方法或属性
            
        Raises:
            WebDriverError: 当Page对象未初始化时
            AttributeError: 当方法或属性不存在时
            
        Examples:
            # 直接调用Playwright Page API
            await driver.goto("https://example.com")  # 等价于 await driver._page.goto(...)
            await driver.click("button")             # 等价于 await driver._page.click(...)
            await driver.fill("input", "text")       # 等价于 await driver._page.fill(...)
            
            # 调用Locator方法
            locator = driver.locator("button")       # 等价于 driver._page.locator(...)
            await locator.click()
            
            # 访问属性
            url = driver.url                         # 等价于 driver._page.url
        """
        # 首先检查是否为PlaywrightOperations的方法
        if hasattr(self._operations, name):
            return getattr(self._operations, name)
        
        # 然后使用PlaywrightProxy进行代理
        try:
            return getattr(self._proxy, name)
        except AttributeError:
            # 提供更友好的错误信息
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'. "
                               f"Make sure the page is initialized by calling start() method first.")


class WebPage(BasePage):
    """Web页面基类"""
    
    def __init__(self, driver: BaseWebDriver, url: Optional[str] = None):
        """初始化Web页面
        
        Args:
            driver: Web驱动器实例
            url: 页面URL
        """
        super().__init__()
        self.driver = driver
        self.url = url
        self.logger = get_logger(f"web_page_{self.__class__.__name__.lower()}")
    
    @property
    def page(self) -> Page:
        """获取Playwright页面对象"""
        return self.driver.page
    
    async def open(self, url: Optional[str] = None) -> None:
        """打开页面
        
        Args:
            url: 页面URL，None时使用初始化时的URL
        """
        target_url = url or self.url
        if not target_url:
            raise WebDriverError("No URL specified for page")
        
        await self.driver.navigate_to(target_url)
        await self.wait_for_page_load()
    
    async def wait_for_page_load(self) -> None:
        """等待页面加载完成"""
        await self.driver.wait_for_network_idle()
    
    async def is_element_present(self, selector: str) -> bool:
        """检查元素是否存在
        
        Args:
            selector: 元素选择器
        
        Returns:
            元素是否存在
        """
        try:
            await self.driver.wait_for_element(selector, timeout=1000)
            return True
        except WebDriverError:
            return False
    
    async def wait_for_element_visible(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """等待元素可见
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
        
        Returns:
            元素定位器
        """
        return await self.driver.wait_for_element(selector, timeout, "visible")
    
    async def wait_for_element_hidden(self, selector: str, timeout: Optional[int] = None) -> None:
        """等待元素隐藏
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
        """
        await self.driver.wait_for_element(selector, timeout, "hidden")


if __name__ == "__main__":
    # 测试Web驱动器
    async def test_web_driver():
        print("Testing Web Driver...")
        
        async with BaseWebDriver(headless=True) as driver:
            # 导航到测试页面
            await driver.navigate_to("https://example.com")
            
            # 获取页面标题
            title = await driver.page.title()
            print(f"Page title: {title}")
            
            # 截图
            screenshot_path = await driver.take_screenshot("test_screenshot.png")
            print(f"Screenshot saved: {screenshot_path}")
            
            # 获取性能指标
            metrics = await driver.get_performance_metrics()
            print(f"Performance metrics: {metrics}")
    
    # 运行测试
    asyncio.run(test_web_driver())
    print("Web driver test completed.")
