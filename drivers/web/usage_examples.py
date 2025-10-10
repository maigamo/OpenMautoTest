
"""
OpenMautoTest BaseWebDriver使用示例

展示BaseWebDriver的各种功能和用法，包括动态代理和Playwright操作封装
"""

import asyncio
from pathlib import Path

from drivers.web.base_web_driver import BaseWebDriver


async def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    async with BaseWebDriver() as driver:
        # 导航到页面
        await driver.goto("https://example.com")
        
        # 获取页面标题
        title = await driver.title()
        print(f"页面标题: {title}")
        
        # 截图
        await driver.screenshot("example_basic.png")
        print("截图已保存")


async def example_element_locators():
    """元素定位器示例"""
    print("\n=== 元素定位器示例 ===")
    
    async with BaseWebDriver() as driver:
        await driver.goto("https://example.com")
        
        # 使用不同的定位方法
        try:
            # 通过角色定位
            button = await driver.get_by_role("button", name="More information")
            if await button.is_visible():
                print("找到按钮: More information")
            
            # 通过文本定位
            link = await driver.get_by_text("More information")
            if await link.is_visible():
                print("找到链接: More information")
            
            # 通过测试ID定位（如果存在）
            element = await driver.get_by_test_id("example-element")
            if await element.count() > 0:
                print("找到测试元素")
                
        except Exception as e:
            print(f"元素定位示例执行完成（部分元素可能不存在）: {e}")


async def example_playwright_operations():
    """Playwright操作封装示例"""
    print("\n=== Playwright操作封装示例 ===")
    
    async with BaseWebDriver() as driver:
        await driver.goto("https://example.com")
        
        # 使用playwright_ops属性访问封装的操作
        ops = driver.playwright_ops
        
        # 截图
        screenshot_bytes = await ops.screenshot("example_ops.png", full_page=True)
        print(f"全页截图已保存，大小: {len(screenshot_bytes)} bytes")
        
        # 执行JavaScript
        page_height = await ops.evaluate("document.body.scrollHeight")
        print(f"页面高度: {page_height}px")
        
        # 设置视口大小
        await ops.set_viewport_size(1920, 1080)
        print("视口大小已设置为 1920x1080")


async def example_dynamic_proxy():
    """动态代理使用示例"""
    print("\n=== 动态代理使用示例 ===")
    
    async with BaseWebDriver() as driver:
        # 直接调用Playwright Page API（通过动态代理）
        await driver.goto("https://example.com")
        
        # 这些调用会被自动代理到 driver._page
        url = driver.url
        print(f"当前URL: {url}")
        
        # 获取页面内容
        content = await driver.content()
        print(f"页面内容长度: {len(content)} characters")
        
        # 等待元素
        try:
            await driver.wait_for_selector("body", timeout=5000)
            print("页面body元素已加载")
        except Exception as e:
            print(f"等待元素超时: {e}")
        
        # 使用locator方法
        body_locator = driver.locator("body")
        is_visible = await body_locator.is_visible()
        print(f"Body元素可见: {is_visible}")


async def example_advanced_features():
    """高级功能示例"""
    print("\n=== 高级功能示例 ===")
    
    async with BaseWebDriver() as driver:
        await driver.goto("https://example.com")
        
        # 添加自定义样式
        await driver.playwright_ops.add_style_tag(
            content="body { border: 5px solid red; }"
        )
        print("添加了红色边框样式")
        
        # 模拟打印媒体
        await driver.playwright_ops.emulate_media(media="print")
        print("切换到打印媒体模式")
        
        # 截图对比
        await driver.screenshot("example_print_mode.png")
        
        # 恢复屏幕媒体
        await driver.playwright_ops.emulate_media(media="screen")
        print("恢复到屏幕媒体模式")
        
        # 生成PDF
        try:
            pdf_bytes = await driver.playwright_ops.pdf("example_page.pdf")
            print(f"PDF已生成，大小: {len(pdf_bytes)} bytes")
        except Exception as e:
            print(f"PDF生成失败（可能需要Chromium浏览器）: {e}")


async def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    driver = BaseWebDriver()
    
    # 在未启动时尝试访问方法
    try:
        await driver.goto("https://example.com")
    except Exception as e:
        print(f"预期的错误: {e}")
    
    # 启动驱动器
    await driver.start()
    
    try:
        # 访问不存在的属性
        nonexistent = driver.nonexistent_method
    except AttributeError as e:
        print(f"属性错误: {e}")
    
    try:
        # 导航到无效URL
        await driver.goto("invalid-url")
    except Exception as e:
        print(f"导航错误: {e}")
    
    await driver.stop()


async def main():
    """主函数"""
    print("OpenMautoTest BaseWebDriver 使用示例")
    print("=" * 50)
    
    try:
        await example_basic_usage()
        await example_element_locators()
        await example_playwright_operations()
        await example_dynamic_proxy()
        await example_advanced_features()
        await example_error_handling()
        
    except Exception as e:
        print(f"示例执行出错: {e}")
    
    print("\n" + "=" * 50)
    print("所有示例执行完成")


if __name__ == "__main__":
    asyncio.run(main())
