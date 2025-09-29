"""
OpenMautoTest Playwright动态代理模块

提供对Playwright API的动态代理功能，简化Web自动化操作
"""

from typing import Any, Optional
from playwright.async_api import Page, Locator, ElementHandle

from common.logger import get_logger


class WebDriverError(Exception):
    """Web驱动器异常"""
    pass


class PlaywrightProxy:
    """Playwright动态代理类
    
    这个类实现了对Playwright Page API的动态代理，允许直接调用Playwright的方法
    而不需要显式地通过page对象访问。
    """
    
    def __init__(self, page: Optional[Page] = None):
        """初始化代理
        
        Args:
            page: Playwright Page对象
        """
        self._page = page
        self.logger = get_logger("playwright_proxy")
    
    def set_page(self, page: Page) -> None:
        """设置Page对象
        
        Args:
            page: Playwright Page对象
        """
        self._page = page
        self.logger.debug("Page object updated")
    
    def __getattr__(self, name: str) -> Any:
        """动态代理，转发调用给Playwright对象
        
        这个方法实现了对Playwright Page API的动态代理，允许直接调用Playwright的方法
        而不需要显式地通过self._page访问。
        
        代理优先级：
        1. 首先检查Page对象是否存在
        2. 检查是否为Page对象的方法或属性
        3. 检查是否为常用的Locator方法
        4. 如果都不是，抛出AttributeError异常
        
        Args:
            name: 要调用的方法或属性名
            
        Returns:
            Playwright对象的方法或属性
            
        Raises:
            WebDriverError: 当Page对象未初始化时
            AttributeError: 当方法或属性不存在时
            
        Examples:
            # 直接调用Playwright Page API
            await proxy.goto("https://example.com")  # 等价于 await page.goto(...)
            await proxy.click("button")             # 等价于 await page.click(...)
            await proxy.fill("input", "text")       # 等价于 await page.fill(...)
            
            # 调用Locator方法
            locator = proxy.locator("button")       # 等价于 page.locator(...)
            await locator.click()
            
            # 访问属性
            url = proxy.url                         # 等价于 page.url
        """
        # 检查Page对象是否已初始化
        if self._page is None:
            raise WebDriverError(f"Page not initialized. Cannot access '{name}' before setting page object.")
        
        # 优先检查Page对象的方法和属性
        if hasattr(self._page, name):
            attr = getattr(self._page, name)
            self.logger.debug(f"Proxying Page.{name}")
            return attr
        
        # 检查常用的Locator方法（为了更好的用户体验）
        locator_methods = [
            'locator', 'query_selector', 'query_selector_all',
            'wait_for_selector', 'is_visible', 'is_hidden', 'is_enabled', 'is_disabled'
        ]
        
        if name in locator_methods and hasattr(self._page, name):
            attr = getattr(self._page, name)
            self.logger.debug(f"Proxying Locator method: {name}")
            return attr
        
        # 如果方法未找到，提供有用的错误信息
        available_methods = [method for method in dir(self._page) if not method.startswith('_')]
        similar_methods = [method for method in available_methods if name.lower() in method.lower()]
        
        error_msg = f"'PlaywrightProxy' object has no attribute '{name}'"
        
        if similar_methods:
            error_msg += f". Did you mean one of: {', '.join(similar_methods[:3])}?"
        else:
            error_msg += f". Available methods include: {', '.join(available_methods[:5])}..."
        
        raise AttributeError(error_msg)


class PlaywrightOperations:
    """Playwright常用操作封装类
    
    提供对Playwright常用操作的封装，包括元素定位、截图、PDF生成等功能
    """
    
    def __init__(self, page: Optional[Page] = None):
        """初始化操作类
        
        Args:
            page: Playwright Page对象
        """
        self._page = page
        self.logger = get_logger("playwright_operations")
    
    def __call__(self, *args, **kwargs):
        """防止对象被错误地当作函数调用
        
        Raises:
            TypeError: 当尝试调用对象时抛出错误
        """
        raise TypeError(
            f"'{self.__class__.__name__}' object is not callable. "
            f"Did you mean to call a method on this object? "
            f"Available methods include: get_by_role, get_by_text, screenshot, etc."
        )
    
    def set_page(self, page: Page) -> None:
        """设置Page对象
        
        Args:
            page: Playwright Page对象
        """
        self._page = page
        self.logger.debug("Page object updated")
    
    async def get_by_role(self, role: str, **kwargs) -> Locator:
        """通过角色获取元素定位器
        
        Args:
            role: ARIA角色 (button, link, textbox, etc.)
            **kwargs: 其他参数 (name, exact, disabled, etc.)
        
        Returns:
            Playwright Locator对象
            
        Examples:
            button = await ops.get_by_role("button", name="Submit")
            link = await ops.get_by_role("link", name="Home")
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        locator = self._page.get_by_role(role, **kwargs)
        self.logger.debug(f"Located element by role: {role}, kwargs: {kwargs}")
        return locator
    
    async def get_by_text(self, text: str, **kwargs) -> Locator:
        """通过文本内容获取元素定位器
        
        Args:
            text: 文本内容
            **kwargs: 其他参数 (exact等)
        
        Returns:
            Playwright Locator对象
            
        Examples:
            element = await ops.get_by_text("Click me")
            element = await ops.get_by_text("Submit", exact=True)
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        locator = self._page.get_by_text(text, **kwargs)
        self.logger.debug(f"Located element by text: {text}, kwargs: {kwargs}")
        return locator
    
    async def get_by_label(self, text: str, **kwargs) -> Locator:
        """通过标签文本获取元素定位器
        
        Args:
            text: 标签文本
            **kwargs: 其他参数 (exact等)
        
        Returns:
            Playwright Locator对象
            
        Examples:
            input_field = await ops.get_by_label("Username")
            checkbox = await ops.get_by_label("Remember me")
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        locator = self._page.get_by_label(text, **kwargs)
        self.logger.debug(f"Located element by label: {text}, kwargs: {kwargs}")
        return locator
    
    async def get_by_placeholder(self, text: str, **kwargs) -> Locator:
        """通过占位符文本获取元素定位器
        
        Args:
            text: 占位符文本
            **kwargs: 其他参数 (exact等)
        
        Returns:
            Playwright Locator对象
            
        Examples:
            input_field = await ops.get_by_placeholder("Enter your email")
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        locator = self._page.get_by_placeholder(text, **kwargs)
        self.logger.debug(f"Located element by placeholder: {text}, kwargs: {kwargs}")
        return locator
    
    async def get_by_test_id(self, test_id: str) -> Locator:
        """通过测试ID获取元素定位器
        
        Args:
            test_id: 测试ID (data-testid属性值)
        
        Returns:
            Playwright Locator对象
            
        Examples:
            button = await ops.get_by_test_id("submit-button")
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        locator = self._page.get_by_test_id(test_id)
        self.logger.debug(f"Located element by test id: {test_id}")
        return locator
    
    async def get_by_title(self, text: str, **kwargs) -> Locator:
        """通过title属性获取元素定位器
        
        Args:
            text: title属性值
            **kwargs: 其他参数 (exact等)
        
        Returns:
            Playwright Locator对象
            
        Examples:
            tooltip = await ops.get_by_title("Help information")
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        locator = self._page.get_by_title(text, **kwargs)
        self.logger.debug(f"Located element by title: {text}, kwargs: {kwargs}")
        return locator
    
    async def screenshot(self, path: Optional[str] = None, **kwargs) -> bytes:
        """截取页面截图
        
        Args:
            path: 保存路径，为None时返回截图字节数据
            **kwargs: 其他参数 (full_page, clip, type, quality等)
        
        Returns:
            截图字节数据
            
        Examples:
            # 保存到文件
            await ops.screenshot("screenshot.png")
            
            # 全页截图
            await ops.screenshot("full_page.png", full_page=True)
            
            # 获取字节数据
            screenshot_bytes = await ops.screenshot()
            
            # 截取指定区域
            await ops.screenshot("clip.png", clip={"x": 0, "y": 0, "width": 800, "height": 600})
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        try:
            # 设置默认参数
            screenshot_kwargs = {
                'path': path,
                'type': 'png',
                **kwargs
            }
            
            screenshot_bytes = await self._page.screenshot(**screenshot_kwargs)
            
            if path:
                self.logger.info(f"Screenshot saved to: {path}")
            else:
                self.logger.info("Screenshot captured as bytes")
            
            return screenshot_bytes
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            raise WebDriverError(f"Screenshot failed: {e}")
    
    async def pdf(self, path: Optional[str] = None, **kwargs) -> bytes:
        """生成页面PDF
        
        Args:
            path: 保存路径，为None时返回PDF字节数据
            **kwargs: 其他参数 (format, landscape, margin等)
        
        Returns:
            PDF字节数据
            
        Examples:
            # 保存到文件
            await ops.pdf("page.pdf")
            
            # 横向PDF
            await ops.pdf("landscape.pdf", landscape=True)
            
            # 自定义页边距
            await ops.pdf("margin.pdf", margin={"top": "1cm", "bottom": "1cm"})
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        try:
            # 设置默认参数
            pdf_kwargs = {
                'path': path,
                'format': 'A4',
                **kwargs
            }
            
            pdf_bytes = await self._page.pdf(**pdf_kwargs)
            
            if path:
                self.logger.info(f"PDF saved to: {path}")
            else:
                self.logger.info("PDF generated as bytes")
            
            return pdf_bytes
            
        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {e}")
            raise WebDriverError(f"PDF generation failed: {e}")
    
    async def evaluate(self, expression: str, *args) -> Any:
        """执行JavaScript表达式
        
        Args:
            expression: JavaScript表达式或函数
            *args: 传递给JavaScript函数的参数
        
        Returns:
            JavaScript执行结果
            
        Examples:
            # 获取页面标题
            title = await ops.evaluate("document.title")
            
            # 执行函数
            result = await ops.evaluate("(x, y) => x + y", 1, 2)
            
            # 获取元素属性
            value = await ops.evaluate("element => element.value", element)
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        try:
            result = await self._page.evaluate(expression, *args)
            self.logger.debug(f"Evaluated JavaScript: {expression[:100]}...")
            return result
            
        except Exception as e:
            self.logger.error(f"JavaScript evaluation failed: {e}")
            raise WebDriverError(f"JavaScript evaluation failed: {e}")
    
    async def add_script_tag(self, **kwargs) -> ElementHandle:
        """添加script标签到页面
        
        Args:
            **kwargs: script标签参数 (url, path, content, type等)
        
        Returns:
            script元素句柄
            
        Examples:
            # 添加外部脚本
            await ops.add_script_tag(url="https://code.jquery.com/jquery-3.6.0.min.js")
            
            # 添加本地脚本文件
            await ops.add_script_tag(path="./scripts/utils.js")
            
            # 添加内联脚本
            await ops.add_script_tag(content="console.log('Hello from script!')")
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        try:
            script_handle = await self._page.add_script_tag(**kwargs)
            self.logger.info(f"Added script tag with kwargs: {kwargs}")
            return script_handle
            
        except Exception as e:
            self.logger.error(f"Failed to add script tag: {e}")
            raise WebDriverError(f"Add script tag failed: {e}")
    
    async def add_style_tag(self, **kwargs) -> ElementHandle:
        """添加style标签到页面
        
        Args:
            **kwargs: style标签参数 (url, path, content等)
        
        Returns:
            style元素句柄
            
        Examples:
            # 添加外部样式
            await ops.add_style_tag(url="https://cdn.jsdelivr.net/npm/bootstrap@5.1.0/dist/css/bootstrap.min.css")
            
            # 添加本地样式文件
            await ops.add_style_tag(path="./styles/custom.css")
            
            # 添加内联样式
            await ops.add_style_tag(content="body { background-color: #f0f0f0; }")
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        try:
            style_handle = await self._page.add_style_tag(**kwargs)
            self.logger.info(f"Added style tag with kwargs: {kwargs}")
            return style_handle
            
        except Exception as e:
            self.logger.error(f"Failed to add style tag: {e}")
            raise WebDriverError(f"Add style tag failed: {e}")
    
    async def set_viewport_size(self, width: int, height: int) -> None:
        """设置视口大小
        
        Args:
            width: 视口宽度
            height: 视口高度
            
        Examples:
            await ops.set_viewport_size(1920, 1080)
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        try:
            await self._page.set_viewport_size({"width": width, "height": height})
            self.logger.info(f"Set viewport size to {width}x{height}")
            
        except Exception as e:
            self.logger.error(f"Failed to set viewport size: {e}")
            raise WebDriverError(f"Set viewport size failed: {e}")
    
    async def emulate_media(self, media: Optional[str] = None, color_scheme: Optional[str] = None) -> None:
        """模拟媒体类型和颜色方案
        
        Args:
            media: 媒体类型 ('screen', 'print', None)
            color_scheme: 颜色方案 ('light', 'dark', 'no-preference', None)
            
        Examples:
            # 模拟打印媒体
            await ops.emulate_media(media="print")
            
            # 模拟深色模式
            await ops.emulate_media(color_scheme="dark")
            
            # 同时设置媒体类型和颜色方案
            await ops.emulate_media(media="screen", color_scheme="light")
        """
        if self._page is None:
            raise WebDriverError("Page not initialized")
        
        try:
            await self._page.emulate_media(media=media, color_scheme=color_scheme)
            self.logger.info(f"Emulated media: {media}, color_scheme: {color_scheme}")
            
        except Exception as e:
            self.logger.error(f"Failed to emulate media: {e}")
            raise WebDriverError(f"Emulate media failed: {e}")
