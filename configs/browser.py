"""
OpenMautoTest 浏览器配置管理模块

提供浏览器相关的配置管理，包括Playwright和Selenium配置
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from .settings import get_settings


@dataclass
class BrowserConfig:
    """浏览器基础配置类"""
    
    BROWSER_TYPE: str = "chromium"  # chromium, firefox, webkit
    HEADLESS: bool = True
    DEFAULT_TIMEOUT: int = 30000  # 毫秒
    SLOW_MO: int = 0  # 毫秒
    VIEWPORT_WIDTH: int = 1920
    VIEWPORT_HEIGHT: int = 1080
    
    # 保持向后兼容
    @property
    def browser_type(self) -> str:
        return self.BROWSER_TYPE
    
    @property
    def headless(self) -> bool:
        return self.HEADLESS
    
    @property
    def timeout(self) -> int:
        return self.DEFAULT_TIMEOUT
    
    @property
    def viewport_width(self) -> int:
        return self.VIEWPORT_WIDTH
    
    @property
    def viewport_height(self) -> int:
        return self.VIEWPORT_HEIGHT
    
    # 浏览器启动参数
    args: Optional[List[str]] = None
    
    # 下载设置
    downloads_path: Optional[str] = None
    accept_downloads: bool = True
    
    # 录制设置
    record_video: bool = False
    record_har: bool = False
    
    # 代理设置
    proxy_server: Optional[str] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    
    # 用户代理
    user_agent: Optional[str] = None
    
    # 地理位置
    geolocation: Optional[Dict[str, float]] = None
    permissions: Optional[List[str]] = None
    
    # 设备模拟
    device_name: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.args is None:
            self.args = []
        
        # 根据浏览器类型设置默认参数
        if self.browser_type == "chromium":
            self.args.extend([
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-default-apps",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--no-first-run",
                "--no-default-browser-check",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ])
        
        # 设置下载路径
        if self.downloads_path is None:
            settings = get_settings()
            self.downloads_path = str(settings.get_output_dir() / "downloads")


@dataclass 
class PlaywrightConfig(BrowserConfig):
    """Playwright 特定配置"""
    
    # Playwright 特有配置
    ignore_https_errors: bool = True
    java_script_enabled: bool = True
    bypass_csp: bool = False
    
    # 网络设置
    offline: bool = False
    
    # 截图设置
    screenshot_mode: str = "only-on-failure"  # always, never, only-on-failure
    screenshot_path: Optional[str] = None
    
    # 视频录制
    video_dir: Optional[str] = None
    video_size: Optional[Dict[str, int]] = None
    RECORD_VIDEO: bool = False  # 添加缺失的属性
    
    # HAR 记录
    har_path: Optional[str] = None
    
    # 追踪设置
    trace_dir: Optional[str] = None
    
    # 调试模式
    DEBUG_MODE: bool = False  # 添加缺失的属性
    
    # 窗口尺寸 (兼容性属性)
    WINDOW_WIDTH: int = 1920  # 添加缺失的属性
    WINDOW_HEIGHT: int = 1080  # 添加缺失的属性
    
    # 移动设备模拟
    MOBILE_DEVICE: Optional[str] = None  # 添加缺失的属性
    
    # 浏览器启动参数 (兼容性属性)
    BROWSER_ARGS: Optional[List[str]] = None  # 添加缺失的属性
    
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        
        settings = get_settings()
        
        if self.screenshot_path is None:
            self.screenshot_path = str(settings.get_screenshots_dir())
        
        if self.video_dir is None:
            self.video_dir = str(settings.get_output_dir() / "videos")
        
        if self.trace_dir is None:
            self.trace_dir = str(settings.get_output_dir() / "traces")
        
        if self.video_size is None:
            self.video_size = {"width": self.viewport_width, "height": self.viewport_height}
        
        # 初始化兼容性属性
        if self.BROWSER_ARGS is None:
            self.BROWSER_ARGS = self.args.copy() if self.args else []
        
        # 确保窗口尺寸与视口尺寸一致
        if self.WINDOW_WIDTH != self.VIEWPORT_WIDTH:
            self.WINDOW_WIDTH = self.VIEWPORT_WIDTH
        if self.WINDOW_HEIGHT != self.VIEWPORT_HEIGHT:
            self.WINDOW_HEIGHT = self.VIEWPORT_HEIGHT


@dataclass
class SeleniumConfig(BrowserConfig):
    """Selenium 特定配置"""
    
    # Selenium 特有配置
    implicit_wait: int = 10  # 秒
    page_load_timeout: int = 30  # 秒
    script_timeout: int = 30  # 秒
    
    # WebDriver 路径
    driver_path: Optional[str] = None
    
    # 窗口设置
    maximize_window: bool = True
    
    # 日志级别
    log_level: str = "INFO"
    
    # 实验性选项
    experimental_options: Optional[Dict] = None
    
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        
        if self.experimental_options is None:
            self.experimental_options = {}
        
        # 设置下载选项
        if self.browser_type == "chromium":
            self.experimental_options.update({
                "prefs": {
                    "download.default_directory": self.downloads_path,
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": True
                }
            })


class BrowserConfigManager:
    """浏览器配置管理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self._playwright_config: Optional[PlaywrightConfig] = None
        self._selenium_config: Optional[SeleniumConfig] = None
    
    def get_playwright_config(self, **overrides) -> PlaywrightConfig:
        """获取Playwright配置"""
        if self._playwright_config is None:
            self._playwright_config = PlaywrightConfig(
                BROWSER_TYPE=self.settings.BROWSER_TYPE,
                HEADLESS=self.settings.BROWSER_HEADLESS,
                DEFAULT_TIMEOUT=self.settings.BROWSER_TIMEOUT,
                SLOW_MO=self.settings.BROWSER_SLOW_MO
            )
        
        # 应用覆盖参数
        if overrides:
            config_dict = self._playwright_config.__dict__.copy()
            config_dict.update(overrides)
            return PlaywrightConfig(**config_dict)
        
        return self._playwright_config
    
    def get_selenium_config(self, **overrides) -> SeleniumConfig:
        """获取Selenium配置"""
        if self._selenium_config is None:
            self._selenium_config = SeleniumConfig(
                BROWSER_TYPE=self.settings.BROWSER_TYPE,
                HEADLESS=self.settings.BROWSER_HEADLESS,
                DEFAULT_TIMEOUT=self.settings.BROWSER_TIMEOUT,
                slow_mo=self.settings.BROWSER_SLOW_MO
            )
        
        # 应用覆盖参数
        if overrides:
            config_dict = self._selenium_config.__dict__.copy()
            config_dict.update(overrides)
            return SeleniumConfig(**config_dict)
        
        return self._selenium_config
    
    def get_mobile_config(self, device_name: str = "iPhone 12") -> PlaywrightConfig:
        """获取移动设备配置"""
        mobile_devices = {
            "iPhone 12": {
                "viewport_width": 390,
                "viewport_height": 844,
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
            },
            "iPad": {
                "viewport_width": 1024,
                "viewport_height": 768,
                "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
            },
            "Android": {
                "viewport_width": 412,
                "viewport_height": 732,
                "user_agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
            }
        }
        
        device_config = mobile_devices.get(device_name, mobile_devices["iPhone 12"])
        
        return self.get_playwright_config(
            device_name=device_name,
            **device_config
        )
    
    def get_debug_config(self) -> PlaywrightConfig:
        """获取调试配置"""
        return self.get_playwright_config(
            headless=False,
            slow_mo=1000,
            timeout=0,  # 无超时
            record_video=True,
            screenshot_mode="always"
        )
    
    def get_ci_config(self) -> PlaywrightConfig:
        """获取CI环境配置"""
        return self.get_playwright_config(
            headless=True,
            timeout=60000,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        )


# 全局配置管理器实例
browser_config_manager = BrowserConfigManager()


def get_browser_config(framework: str = "playwright", **overrides) -> Union[PlaywrightConfig, SeleniumConfig]:
    """获取浏览器配置
    
    Args:
        framework: 框架类型 ('playwright' 或 'selenium')
        **overrides: 配置覆盖参数
    
    Returns:
        浏览器配置对象
    """
    if framework.lower() == "playwright":
        return browser_config_manager.get_playwright_config(**overrides)
    elif framework.lower() == "selenium":
        return browser_config_manager.get_selenium_config(**overrides)
    else:
        raise ValueError(f"Unsupported framework: {framework}")


def get_mobile_config(device_name: str = "iPhone 12") -> PlaywrightConfig:
    """获取移动设备配置"""
    return browser_config_manager.get_mobile_config(device_name)


def get_debug_config() -> PlaywrightConfig:
    """获取调试配置"""
    return browser_config_manager.get_debug_config()


def get_ci_config() -> PlaywrightConfig:
    """获取CI环境配置"""
    return browser_config_manager.get_ci_config()


if __name__ == "__main__":
    # 测试配置
    print("Testing browser configurations...")
    
    # Playwright 配置
    pw_config = get_browser_config("playwright")
    print(f"Playwright Config: {pw_config.browser_type}, headless={pw_config.headless}")
    
    # Selenium 配置
    sel_config = get_browser_config("selenium")
    print(f"Selenium Config: {sel_config.browser_type}, headless={sel_config.headless}")
    
    # 移动设备配置
    mobile_config = get_mobile_config("iPhone 12")
    print(f"Mobile Config: {mobile_config.viewport_width}x{mobile_config.viewport_height}")
    
    # 调试配置
    debug_config = get_debug_config()
    print(f"Debug Config: headless={debug_config.headless}, slow_mo={debug_config.slow_mo}")
    
    print("Browser configuration tests completed.")
