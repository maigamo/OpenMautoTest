# BaseWebDriver 增强功能说明

## 概述

BaseWebDriver 现在提供了更完善的基础操作封装和动态代理功能，让 Playwright 的使用更加便捷和直观。

## 新增功能

### 1. 动态代理 (Dynamic Proxy)

通过 `__getattr__` 实现的动态代理，允许直接调用 Playwright Page API，无需显式访问 `_page` 对象。

```python
async with BaseWebDriver() as driver:
    # 直接调用 Playwright API
    await driver.goto("https://example.com")  # 等价于 await driver._page.goto(...)
    await driver.click("button")             # 等价于 await driver._page.click(...)
    await driver.fill("input", "text")       # 等价于 await driver._page.fill(...)
    
    # 访问属性
    url = driver.url                         # 等价于 driver._page.url
    title = await driver.title()            # 等价于 await driver._page.title()
```

### 2. Playwright 操作封装

提供了常用 Playwright 操作的封装，包括：

#### 元素定位器
- `get_by_role(role, **kwargs)` - 通过 ARIA 角色定位
- `get_by_text(text, **kwargs)` - 通过文本内容定位
- `get_by_label(text, **kwargs)` - 通过标签文本定位
- `get_by_placeholder(text, **kwargs)` - 通过占位符定位
- `get_by_test_id(test_id)` - 通过测试ID定位
- `get_by_title(text, **kwargs)` - 通过title属性定位

#### 页面操作
- `screenshot(path=None, **kwargs)` - 截图
- `pdf(path=None, **kwargs)` - 生成PDF
- `evaluate(expression, *args)` - 执行JavaScript
- `add_script_tag(**kwargs)` - 添加脚本标签
- `add_style_tag(**kwargs)` - 添加样式标签
- `set_viewport_size(width, height)` - 设置视口大小
- `emulate_media(media=None, color_scheme=None)` - 模拟媒体类型

## 使用方式

### 方式一：直接调用（动态代理）

```python
async with BaseWebDriver() as driver:
    # 所有 Playwright Page API 都可以直接调用
    await driver.goto("https://example.com")
    await driver.wait_for_load_state("networkidle")
    
    # 元素操作
    await driver.click("text=Click me")
    await driver.fill("input[name='username']", "admin")
    
    # 获取信息
    title = await driver.title()
    url = driver.url
```

### 方式二：使用封装的操作对象

```python
async with BaseWebDriver() as driver:
    await driver.goto("https://example.com")
    
    # 通过 playwright_ops 属性访问封装的操作
    ops = driver.playwright_ops
    
    # 使用封装的方法
    button = await ops.get_by_role("button", name="Submit")
    await ops.screenshot("test.png", full_page=True)
    result = await ops.evaluate("document.title")
```

### 方式三：便捷方法

```python
async with BaseWebDriver() as driver:
    await driver.goto("https://example.com")
    
    # 常用操作提供了便捷方法
    await driver.screenshot()  # 自动生成文件名
    button = await driver.get_by_role("button", name="Submit")
    element = await driver.get_by_text("Click me")
```

## 代理优先级

动态代理按以下优先级查找方法：

1. **PlaywrightOperations 方法** - 封装的操作方法
2. **PlaywrightProxy 代理** - 直接代理到 Playwright Page API
3. **AttributeError** - 方法不存在时抛出异常

## 错误处理

### Page 未初始化

```python
driver = BaseWebDriver()
# 未调用 start() 就尝试访问方法
try:
    await driver.goto("https://example.com")
except WebDriverError as e:
    print(f"错误: {e}")  # Page not initialized...
```

### 方法不存在

```python
try:
    result = driver.nonexistent_method()
except AttributeError as e:
    print(f"错误: {e}")  # 'BaseWebDriver' object has no attribute 'nonexistent_method'...
```

## 架构设计

### 模块分离

- **`base_web_driver.py`** - 主驱动器类，负责浏览器生命周期管理
- **`playwright_proxy.py`** - 代理和操作封装，负责 API 转发和常用操作
- **`usage_examples.py`** - 使用示例和最佳实践

### 代理模式优势

1. **简化调用** - 无需记住复杂的对象层次
2. **类型安全** - 保持 Playwright 的类型提示
3. **错误友好** - 提供有用的错误信息和建议
4. **扩展性强** - 易于添加新的封装方法

## 性能考虑

- 动态代理只在方法查找时有微小开销
- 封装方法提供了额外的日志记录和错误处理
- 代理对象在驱动器初始化时创建，运行时无额外开销

## 最佳实践

### 1. 使用上下文管理器

```python
async with BaseWebDriver() as driver:
    # 自动处理启动和关闭
    await driver.goto("https://example.com")
```

### 2. 选择合适的定位方式

```python
# 优先使用语义化定位
button = await driver.get_by_role("button", name="Submit")

# 其次使用文本定位
link = await driver.get_by_text("Learn more")

# 最后使用CSS选择器
element = await driver.locator("#specific-id")
```

### 3. 合理使用截图

```python
# 自动命名截图
await driver.screenshot()

# 指定路径和选项
await driver.screenshot("test.png", full_page=True)

# 只获取字节数据
screenshot_bytes = await driver.screenshot(path=None)
```

### 4. JavaScript 执行

```python
# 简单表达式
title = await driver.evaluate("document.title")

# 复杂函数
result = await driver.evaluate("""
    () => {
        return {
            width: window.innerWidth,
            height: window.innerHeight,
            userAgent: navigator.userAgent
        };
    }
""")
```

## 示例代码

完整的使用示例请参考 `usage_examples.py` 文件，包含：

- 基础使用示例
- 元素定位器示例
- Playwright 操作封装示例
- 动态代理使用示例
- 高级功能示例
- 错误处理示例

## 兼容性

- 与现有代码完全兼容
- 支持所有 Playwright Page API
- 保持原有的异步特性
- 维持类型提示和文档
