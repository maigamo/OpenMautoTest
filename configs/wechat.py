"""
OpenMautoTest 微信小程序配置管理模块

提供微信小程序自动化相关的配置管理
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from .settings import get_settings


@dataclass
class WechatMiniConfig:
    """微信小程序配置类"""
    
    # 基础配置
    app_id: str = ""
    project_path: str = ""
    
    # 开发者工具配置
    ide_port: int = 9420
    ide_host: str = "localhost"
    ide_timeout: int = 30000  # 毫秒
    
    # 自动化配置
    auto_authorize: bool = True  # 自动授权
    auto_login: bool = True  # 自动登录
    
    # 网络配置
    mock_network: bool = False  # 模拟网络环境
    network_type: str = "wifi"  # wifi, 2g, 3g, 4g, none
    
    # 调试配置
    debug_mode: bool = False
    enable_debug_log: bool = True
    
    # 截图配置
    auto_screenshot: bool = True
    screenshot_on_failure: bool = True
    screenshot_path: Optional[str] = None
    
    # 录制配置
    record_video: bool = False
    video_path: Optional[str] = None
    
    # 性能配置
    page_load_timeout: int = 10000  # 页面加载超时
    element_timeout: int = 5000  # 元素查找超时
    action_timeout: int = 3000  # 操作超时
    
    # 设备模拟
    device_type: str = "iPhone X"  # 设备类型
    system_version: str = "iOS 14.0"  # 系统版本
    
    # 地理位置
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # 用户信息模拟
    mock_user_info: bool = False
    user_avatar: Optional[str] = None
    user_nickname: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        settings = get_settings()
        
        # 从全局设置中获取配置
        if not self.app_id and settings.WECHAT_MINI_APP_ID:
            self.app_id = settings.WECHAT_MINI_APP_ID
        
        if not self.project_path and settings.WECHAT_MINI_PROJECT_PATH:
            self.project_path = settings.WECHAT_MINI_PROJECT_PATH
        
        if self.ide_port == 9420:
            self.ide_port = settings.WECHAT_MINI_IDE_PORT
        
        # 设置默认路径
        if self.screenshot_path is None:
            self.screenshot_path = str(settings.get_screenshots_dir() / "mini")
            Path(self.screenshot_path).mkdir(parents=True, exist_ok=True)
        
        if self.video_path is None:
            self.video_path = str(settings.get_output_dir() / "videos" / "mini")
            Path(self.video_path).mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "appId": self.app_id,
            "projectPath": self.project_path,
            "port": self.ide_port,
            "host": self.ide_host,
            "timeout": self.ide_timeout,
            "autoAuthorize": self.auto_authorize,
            "autoLogin": self.auto_login,
            "mockNetwork": self.mock_network,
            "networkType": self.network_type,
            "debugMode": self.debug_mode,
            "enableDebugLog": self.enable_debug_log,
            "autoScreenshot": self.auto_screenshot,
            "screenshotOnFailure": self.screenshot_on_failure,
            "screenshotPath": self.screenshot_path,
            "recordVideo": self.record_video,
            "videoPath": self.video_path,
            "pageLoadTimeout": self.page_load_timeout,
            "elementTimeout": self.element_timeout,
            "actionTimeout": self.action_timeout,
            "deviceType": self.device_type,
            "systemVersion": self.system_version,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "mockUserInfo": self.mock_user_info,
            "userAvatar": self.user_avatar,
            "userNickname": self.user_nickname
        }
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        if not self.app_id:
            errors.append("app_id is required")
        
        if not self.project_path:
            errors.append("project_path is required")
        elif not Path(self.project_path).exists():
            errors.append(f"project_path does not exist: {self.project_path}")
        
        if self.ide_port < 1 or self.ide_port > 65535:
            errors.append("ide_port must be between 1 and 65535")
        
        if self.network_type not in ["wifi", "2g", "3g", "4g", "none"]:
            errors.append("network_type must be one of: wifi, 2g, 3g, 4g, none")
        
        return errors


@dataclass
class WechatMiniElement:
    """小程序元素配置"""
    
    # 元素定位
    selector: str = ""
    xpath: str = ""
    text: str = ""
    
    # 等待配置
    wait_timeout: int = 5000
    wait_for_visible: bool = True
    wait_for_enabled: bool = True
    
    # 操作配置
    click_delay: int = 100  # 点击延迟
    input_delay: int = 50  # 输入延迟
    
    # 滚动配置
    scroll_into_view: bool = True
    scroll_behavior: str = "smooth"  # smooth, instant
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "selector": self.selector,
            "xpath": self.xpath,
            "text": self.text,
            "waitTimeout": self.wait_timeout,
            "waitForVisible": self.wait_for_visible,
            "waitForEnabled": self.wait_for_enabled,
            "clickDelay": self.click_delay,
            "inputDelay": self.input_delay,
            "scrollIntoView": self.scroll_into_view,
            "scrollBehavior": self.scroll_behavior
        }


class WechatMiniConfigManager:
    """微信小程序配置管理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self._config: Optional[WechatMiniConfig] = None
    
    def get_config(self, **overrides) -> WechatMiniConfig:
        """获取小程序配置"""
        if self._config is None:
            self._config = WechatMiniConfig()
        
        # 应用覆盖参数
        if overrides:
            config_dict = self._config.__dict__.copy()
            config_dict.update(overrides)
            return WechatMiniConfig(**config_dict)
        
        return self._config
    
    def get_debug_config(self) -> WechatMiniConfig:
        """获取调试配置"""
        return self.get_config(
            debug_mode=True,
            enable_debug_log=True,
            auto_screenshot=True,
            screenshot_on_failure=True,
            record_video=True,
            page_load_timeout=30000,
            element_timeout=10000,
            action_timeout=5000
        )
    
    def get_ci_config(self) -> WechatMiniConfig:
        """获取CI环境配置"""
        return self.get_config(
            debug_mode=False,
            enable_debug_log=False,
            auto_screenshot=False,
            screenshot_on_failure=True,
            record_video=False,
            page_load_timeout=15000,
            element_timeout=8000,
            action_timeout=3000
        )
    
    def get_performance_config(self) -> WechatMiniConfig:
        """获取性能测试配置"""
        return self.get_config(
            debug_mode=False,
            enable_debug_log=False,
            auto_screenshot=False,
            screenshot_on_failure=False,
            record_video=False,
            page_load_timeout=5000,
            element_timeout=3000,
            action_timeout=1000
        )
    
    def load_from_file(self, config_file: Union[str, Path]) -> WechatMiniConfig:
        """从文件加载配置"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 转换键名格式
            converted_data = {}
            for key, value in config_data.items():
                # 将驼峰命名转换为下划线命名
                snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
                converted_data[snake_key] = value
            
            return WechatMiniConfig(**converted_data)
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except TypeError as e:
            raise ValueError(f"Invalid config format: {e}")
    
    def save_to_file(self, config: WechatMiniConfig, config_file: Union[str, Path]):
        """保存配置到文件"""
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
    
    def validate_config(self, config: Optional[WechatMiniConfig] = None) -> List[str]:
        """验证配置"""
        if config is None:
            config = self.get_config()
        
        return config.validate()


# 全局配置管理器实例
wechat_mini_config_manager = WechatMiniConfigManager()


def get_wechat_mini_config(**overrides) -> WechatMiniConfig:
    """获取微信小程序配置
    
    Args:
        **overrides: 配置覆盖参数
    
    Returns:
        微信小程序配置对象
    """
    return wechat_mini_config_manager.get_config(**overrides)


def get_debug_config() -> WechatMiniConfig:
    """获取调试配置"""
    return wechat_mini_config_manager.get_debug_config()


def get_ci_config() -> WechatMiniConfig:
    """获取CI环境配置"""
    return wechat_mini_config_manager.get_ci_config()


def get_performance_config() -> WechatMiniConfig:
    """获取性能测试配置"""
    return wechat_mini_config_manager.get_performance_config()


def validate_wechat_config() -> bool:
    """验证微信小程序配置"""
    try:
        errors = wechat_mini_config_manager.validate_config()
        
        if errors:
            print("WeChat Mini Program configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("WeChat Mini Program configuration validation passed")
        return True
    
    except Exception as e:
        print(f"WeChat Mini Program configuration validation failed: {e}")
        return False


# 常用设备配置
DEVICE_CONFIGS = {
    "iPhone X": {
        "device_type": "iPhone X",
        "system_version": "iOS 14.0"
    },
    "iPhone 12": {
        "device_type": "iPhone 12",
        "system_version": "iOS 15.0"
    },
    "Android": {
        "device_type": "Android",
        "system_version": "Android 11"
    },
    "iPad": {
        "device_type": "iPad",
        "system_version": "iPadOS 15.0"
    }
}


def get_device_config(device_name: str) -> Dict:
    """获取设备配置"""
    return DEVICE_CONFIGS.get(device_name, DEVICE_CONFIGS["iPhone X"])


if __name__ == "__main__":
    # 测试配置
    print("Testing WeChat Mini Program configurations...")
    
    # 基础配置
    config = get_wechat_mini_config()
    print(f"Basic Config: app_id={config.app_id}, port={config.ide_port}")
    
    # 调试配置
    debug_config = get_debug_config()
    print(f"Debug Config: debug_mode={debug_config.debug_mode}, record_video={debug_config.record_video}")
    
    # CI 配置
    ci_config = get_ci_config()
    print(f"CI Config: debug_mode={ci_config.debug_mode}, auto_screenshot={ci_config.auto_screenshot}")
    
    # 验证配置
    validate_wechat_config()
    
    print("WeChat Mini Program configuration tests completed.")
