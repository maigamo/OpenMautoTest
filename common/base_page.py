"""
OpenMautoTest 页面对象基类

提供通用的页面操作方法、元素等待、截图等基础功能
"""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from common.logger import get_logger
from common.utils.time_utils import Timer, wait_for_condition
from configs.settings import get_settings


class BaseElement:
    """基础元素类"""
    
    def __init__(self, locator: Union[str, Dict], description: str = ""):
        self.locator = locator
        self.description = description or str(locator)
    
    def __str__(self):
        return f"Element({self.description})"
    
    def __repr__(self):
        return f"BaseElement(locator={self.locator}, description='{self.description}')"


class BasePage(ABC):
    """页面对象基类"""
    
    def __init__(self, driver: Any, page_name: str = ""):
        self.driver = driver
        self.page_name = page_name or self.__class__.__name__
        self.settings = get_settings()
        self.logger = get_logger(f"page.{self.page_name}")
        self.screenshot_counter = 0
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """检查页面是否已加载
        
        Returns:
            页面是否已加载
        """
        pass
    
    @abstractmethod
    def get_current_url(self) -> str:
        """获取当前页面URL
        
        Returns:
            当前页面URL
        """
        pass
    
    @abstractmethod
    def get_page_title(self) -> str:
        """获取页面标题
        
        Returns:
            页面标题
        """
        pass
    
    @abstractmethod
    def take_screenshot(self, filename: Optional[str] = None) -> Path:
        """截图
        
        Args:
            filename: 截图文件名，如果为None则自动生成
        
        Returns:
            截图文件路径
        """
        pass
    
    @abstractmethod
    def wait_for_element(
        self,
        element: BaseElement,
        timeout: float = 10,
        condition: str = "visible"
    ) -> Any:
        """等待元素出现
        
        Args:
            element: 元素对象
            timeout: 超时时间（秒）
            condition: 等待条件 (visible, present, clickable, etc.)
        
        Returns:
            找到的元素
        """
        pass
    
    @abstractmethod
    def find_element(self, element: BaseElement) -> Any:
        """查找元素
        
        Args:
            element: 元素对象
        
        Returns:
            找到的元素
        """
        pass
    
    @abstractmethod
    def find_elements(self, element: BaseElement) -> List[Any]:
        """查找多个元素
        
        Args:
            element: 元素对象
        
        Returns:
            找到的元素列表
        """
        pass
    
    @abstractmethod
    def click(self, element: BaseElement) -> None:
        """点击元素
        
        Args:
            element: 要点击的元素
        """
        pass
    
    @abstractmethod
    def input_text(self, element: BaseElement, text: str) -> None:
        """输入文本
        
        Args:
            element: 输入框元素
            text: 要输入的文本
        """
        pass
    
    @abstractmethod
    def get_text(self, element: BaseElement) -> str:
        """获取元素文本
        
        Args:
            element: 元素对象
        
        Returns:
            元素文本
        """
        pass
    
    @abstractmethod
    def get_attribute(self, element: BaseElement, attribute: str) -> str:
        """获取元素属性
        
        Args:
            element: 元素对象
            attribute: 属性名
        
        Returns:
            属性值
        """
        pass
    
    @abstractmethod
    def scroll_to_element(self, element: BaseElement) -> None:
        """滚动到元素
        
        Args:
            element: 目标元素
        """
        pass
    
    @abstractmethod
    def refresh_page(self) -> None:
        """刷新页面"""
        pass
    
    def wait_for_page_load(self, timeout: float = 30) -> bool:
        """等待页面加载完成
        
        Args:
            timeout: 超时时间（秒）
        
        Returns:
            页面是否加载完成
        """
        try:
            wait_for_condition(
                self.is_loaded,
                timeout=timeout,
                interval=0.5,
                error_message=f"Page {self.page_name} not loaded within {timeout}s"
            )
            self.logger.info(f"Page {self.page_name} loaded successfully")
            return True
        except TimeoutError as e:
            self.logger.error(f"Page load timeout: {e}")
            return False
    
    def wait_and_click(
        self,
        element: BaseElement,
        timeout: float = 10,
        screenshot_on_error: bool = True
    ) -> bool:
        """等待并点击元素
        
        Args:
            element: 要点击的元素
            timeout: 超时时间（秒）
            screenshot_on_error: 错误时是否截图
        
        Returns:
            是否成功点击
        """
        try:
            self.wait_for_element(element, timeout, "clickable")
            self.click(element)
            self.logger.info(f"Successfully clicked {element}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to click {element}: {e}")
            if screenshot_on_error:
                self.take_screenshot(f"error_click_{element.description}")
            return False
    
    def wait_and_input(
        self,
        element: BaseElement,
        text: str,
        timeout: float = 10,
        clear_first: bool = True,
        screenshot_on_error: bool = True
    ) -> bool:
        """等待并输入文本
        
        Args:
            element: 输入框元素
            text: 要输入的文本
            timeout: 超时时间（秒）
            clear_first: 是否先清空输入框
            screenshot_on_error: 错误时是否截图
        
        Returns:
            是否成功输入
        """
        try:
            self.wait_for_element(element, timeout, "visible")
            if clear_first:
                self.clear_input(element)
            self.input_text(element, text)
            self.logger.info(f"Successfully input text to {element}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to input text to {element}: {e}")
            if screenshot_on_error:
                self.take_screenshot(f"error_input_{element.description}")
            return False
    
    def clear_input(self, element: BaseElement) -> None:
        """清空输入框
        
        Args:
            element: 输入框元素
        """
        # 子类可以重写此方法实现具体的清空逻辑
        pass
    
    def is_element_present(self, element: BaseElement) -> bool:
        """检查元素是否存在
        
        Args:
            element: 元素对象
        
        Returns:
            元素是否存在
        """
        try:
            self.find_element(element)
            return True
        except Exception:
            return False
    
    def is_element_visible(self, element: BaseElement) -> bool:
        """检查元素是否可见
        
        Args:
            element: 元素对象
        
        Returns:
            元素是否可见
        """
        try:
            elem = self.find_element(element)
            return self._is_element_visible(elem)
        except Exception:
            return False
    
    def _is_element_visible(self, element: Any) -> bool:
        """检查具体元素是否可见（子类实现）
        
        Args:
            element: 具体的元素对象
        
        Returns:
            元素是否可见
        """
        # 子类需要实现具体的可见性检查逻辑
        return True
    
    def wait_for_text(
        self,
        element: BaseElement,
        expected_text: str,
        timeout: float = 10,
        exact_match: bool = True
    ) -> bool:
        """等待元素文本
        
        Args:
            element: 元素对象
            expected_text: 期望的文本
            timeout: 超时时间（秒）
            exact_match: 是否精确匹配
        
        Returns:
            文本是否匹配
        """
        def check_text():
            try:
                actual_text = self.get_text(element)
                if exact_match:
                    return actual_text == expected_text
                else:
                    return expected_text in actual_text
            except Exception:
                return False
        
        try:
            wait_for_condition(
                check_text,
                timeout=timeout,
                interval=0.5,
                error_message=f"Text '{expected_text}' not found in {element} within {timeout}s"
            )
            return True
        except TimeoutError:
            return False
    
    def perform_action_with_retry(
        self,
        action: callable,
        max_retries: int = 3,
        delay: float = 1.0,
        screenshot_on_error: bool = True
    ) -> Any:
        """带重试的执行操作
        
        Args:
            action: 要执行的操作函数
            max_retries: 最大重试次数
            delay: 重试延迟（秒）
            screenshot_on_error: 错误时是否截图
        
        Returns:
            操作结果
        
        Raises:
            最后一次执行的异常
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return action()
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Action failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                
                if attempt < max_retries:
                    if screenshot_on_error:
                        self.take_screenshot(f"retry_{attempt + 1}")
                    time.sleep(delay)
                else:
                    if screenshot_on_error:
                        self.take_screenshot("final_error")
        
        raise last_exception
    
    def measure_page_load_time(self) -> float:
        """测量页面加载时间
        
        Returns:
            页面加载时间（秒）
        """
        with Timer() as timer:
            self.wait_for_page_load()
        
        load_time = timer.elapsed_time()
        self.logger.info(f"Page {self.page_name} load time: {load_time:.2f}s")
        return load_time
    
    def get_screenshot_path(self, filename: Optional[str] = None) -> Path:
        """获取截图文件路径
        
        Args:
            filename: 文件名
        
        Returns:
            截图文件路径
        """
        if filename is None:
            self.screenshot_counter += 1
            timestamp = int(time.time() * 1000)
            filename = f"{self.page_name}_{self.screenshot_counter}_{timestamp}.png"
        
        # 确保文件名安全
        from common.utils.string_utils import sanitize_filename
        safe_filename = sanitize_filename(filename)
        
        screenshot_dir = self.settings.get_screenshots_dir()
        return screenshot_dir / safe_filename
    
    def assert_element_present(self, element: BaseElement, message: str = "") -> None:
        """断言元素存在
        
        Args:
            element: 元素对象
            message: 断言失败消息
        
        Raises:
            AssertionError: 元素不存在时抛出
        """
        if not self.is_element_present(element):
            error_msg = message or f"Element {element} is not present"
            self.take_screenshot("assert_element_present_failed")
            raise AssertionError(error_msg)
        
        self.logger.info(f"Assertion passed: Element {element} is present")
    
    def assert_element_visible(self, element: BaseElement, message: str = "") -> None:
        """断言元素可见
        
        Args:
            element: 元素对象
            message: 断言失败消息
        
        Raises:
            AssertionError: 元素不可见时抛出
        """
        if not self.is_element_visible(element):
            error_msg = message or f"Element {element} is not visible"
            self.take_screenshot("assert_element_visible_failed")
            raise AssertionError(error_msg)
        
        self.logger.info(f"Assertion passed: Element {element} is visible")
    
    def assert_text_equals(
        self,
        element: BaseElement,
        expected_text: str,
        message: str = ""
    ) -> None:
        """断言文本相等
        
        Args:
            element: 元素对象
            expected_text: 期望的文本
            message: 断言失败消息
        
        Raises:
            AssertionError: 文本不相等时抛出
        """
        actual_text = self.get_text(element)
        if actual_text != expected_text:
            error_msg = message or f"Text mismatch: expected '{expected_text}', got '{actual_text}'"
            self.take_screenshot("assert_text_equals_failed")
            raise AssertionError(error_msg)
        
        self.logger.info(f"Assertion passed: Text equals '{expected_text}'")
    
    def assert_text_contains(
        self,
        element: BaseElement,
        expected_text: str,
        message: str = ""
    ) -> None:
        """断言文本包含
        
        Args:
            element: 元素对象
            expected_text: 期望包含的文本
            message: 断言失败消息
        
        Raises:
            AssertionError: 文本不包含时抛出
        """
        actual_text = self.get_text(element)
        if expected_text not in actual_text:
            error_msg = message or f"Text '{expected_text}' not found in '{actual_text}'"
            self.take_screenshot("assert_text_contains_failed")
            raise AssertionError(error_msg)
        
        self.logger.info(f"Assertion passed: Text contains '{expected_text}'")
    
    def log_step(self, step_description: str) -> None:
        """记录测试步骤
        
        Args:
            step_description: 步骤描述
        """
        self.logger.info(f"Step: {step_description}")
    
    def log_action(self, action: str, element: Optional[BaseElement] = None) -> None:
        """记录操作
        
        Args:
            action: 操作描述
            element: 相关元素
        """
        if element:
            self.logger.info(f"Action: {action} on {element}")
        else:
            self.logger.info(f"Action: {action}")


class PageFactory:
    """页面工厂类"""
    
    def __init__(self):
        self._pages: Dict[str, type] = {}
    
    def register_page(self, name: str, page_class: type) -> None:
        """注册页面类
        
        Args:
            name: 页面名称
            page_class: 页面类
        """
        self._pages[name] = page_class
    
    def create_page(self, name: str, driver: Any, **kwargs) -> BasePage:
        """创建页面实例
        
        Args:
            name: 页面名称
            driver: 驱动器实例
            **kwargs: 其他参数
        
        Returns:
            页面实例
        
        Raises:
            ValueError: 页面未注册时抛出
        """
        if name not in self._pages:
            raise ValueError(f"Page '{name}' not registered")
        
        page_class = self._pages[name]
        return page_class(driver, **kwargs)
    
    def get_registered_pages(self) -> List[str]:
        """获取已注册的页面列表
        
        Returns:
            页面名称列表
        """
        return list(self._pages.keys())


# 全局页面工厂实例
page_factory = PageFactory()


if __name__ == "__main__":
    # 测试页面基类（需要具体的驱动器实现）
    print("Testing base page functionality...")
    
    # 测试元素类
    element = BaseElement("//button[@id='submit']", "Submit Button")
    print(f"Element: {element}")
    print(f"Element repr: {repr(element)}")
    
    # 测试页面工厂
    factory = PageFactory()
    print(f"Registered pages: {factory.get_registered_pages()}")
    
    print("Base page tests completed.")
