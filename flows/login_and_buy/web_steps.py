"""
OpenMautoTest Web端登录购买流程步骤

实现Web端的业务步骤封装
"""

import asyncio
from typing import Dict, Any, Optional

from common.logger import get_logger
from configs.settings import get_settings
from orchestrator.flow_runner import FlowContext, flow_step


logger = get_logger("web_login_buy_steps")


class WebLoginBuySteps:
    """Web端登录购买步骤"""
    
    def __init__(self, web_context):
        """初始化Web步骤
        
        Args:
            web_context: Web测试上下文
        """
        self.web_context = web_context
        self.driver = web_context.driver
        self.logger = get_logger("web_steps")
        self.settings = get_settings()
    
    @flow_step(
        name="web_navigate_to_homepage",
        description="导航到首页",
        platform="web",
        timeout=30
    )
    async def navigate_to_homepage(self, context: FlowContext) -> Dict[str, Any]:
        """导航到首页
        
        Args:
            context: 流程上下文
        
        Returns:
            导航结果
        """
        base_url = context.get_data("base_url") or "https://example.com"
        
        self.logger.info(f"Navigating to homepage: {base_url}")
        
        try:
            await self.web_context.navigate_and_record(
                base_url,
                step_name="导航到首页"
            )
            
            # 等待页面加载完成
            await self.driver.wait_for_element("body", timeout=10)
            
            # 获取页面标题
            page_title = await self.driver.get_page_title()
            
            result = {
                "url": base_url,
                "title": page_title,
                "status": "success"
            }
            
            # 保存到上下文
            context.set_shared_data("homepage_title", page_title)
            context.set_shared_data("current_url", base_url)
            
            self.logger.info(f"Successfully navigated to homepage: {page_title}")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to navigate to homepage: {e}")
            raise
    
    @flow_step(
        name="web_navigate_to_login",
        description="导航到登录页面",
        platform="web",
        timeout=30,
        depends_on=["web_navigate_to_homepage"]
    )
    async def navigate_to_login(self, context: FlowContext) -> Dict[str, Any]:
        """导航到登录页面
        
        Args:
            context: 流程上下文
        
        Returns:
            导航结果
        """
        login_url = context.get_data("login_url") or "/login"
        base_url = context.get_shared_data("current_url", "https://example.com")
        
        # 构建完整登录URL
        if login_url.startswith("http"):
            full_login_url = login_url
        else:
            full_login_url = f"{base_url.rstrip('/')}{login_url}"
        
        self.logger.info(f"Navigating to login page: {full_login_url}")
        
        try:
            await self.web_context.navigate_and_record(
                full_login_url,
                step_name="导航到登录页面"
            )
            
            # 等待登录表单加载
            await self.driver.wait_for_element("#username, [name='username'], .username-input", timeout=10)
            
            # 获取页面信息
            page_title = await self.driver.get_page_title()
            current_url = await self.driver.get_current_url()
            
            result = {
                "url": current_url,
                "title": page_title,
                "status": "success"
            }
            
            # 保存到上下文
            context.set_shared_data("login_page_title", page_title)
            context.set_shared_data("current_url", current_url)
            
            self.logger.info(f"Successfully navigated to login page: {page_title}")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to navigate to login page: {e}")
            raise
    
    @flow_step(
        name="web_perform_login",
        description="执行登录操作",
        platform="web",
        timeout=60,
        retry_count=2,
        depends_on=["web_navigate_to_login"]
    )
    async def perform_login(self, context: FlowContext) -> Dict[str, Any]:
        """执行登录操作
        
        Args:
            context: 流程上下文
        
        Returns:
            登录结果
        """
        # 获取登录凭据
        username = context.get_data("username") or "test_user"
        password = context.get_data("password") or "test_password"
        
        self.logger.info(f"Performing login for user: {username}")
        
        try:
            # 查找并填写用户名
            username_selectors = [
                "#username",
                "[name='username']",
                ".username-input",
                "input[type='text']",
                "input[placeholder*='用户名']",
                "input[placeholder*='账号']"
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    await self.web_context.fill_and_record(
                        selector,
                        username,
                        step_name="输入用户名",
                        timeout=5
                    )
                    username_filled = True
                    break
                except Exception:
                    continue
            
            if not username_filled:
                raise Exception("Could not find username input field")
            
            # 查找并填写密码
            password_selectors = [
                "#password",
                "[name='password']",
                ".password-input",
                "input[type='password']",
                "input[placeholder*='密码']"
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    await self.web_context.fill_and_record(
                        selector,
                        password,
                        step_name="输入密码",
                        timeout=5
                    )
                    password_filled = True
                    break
                except Exception:
                    continue
            
            if not password_filled:
                raise Exception("Could not find password input field")
            
            # 点击登录按钮
            login_button_selectors = [
                "#login-button",
                "[type='submit']",
                ".login-button",
                ".login-btn",
                "button[contains(text(), '登录')]",
                "input[value*='登录']"
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    await self.web_context.click_and_record(
                        selector,
                        step_name="点击登录按钮",
                        timeout=5
                    )
                    login_clicked = True
                    break
                except Exception:
                    continue
            
            if not login_clicked:
                raise Exception("Could not find login button")
            
            # 等待登录完成 - 检查页面变化
            await asyncio.sleep(2)
            
            # 验证登录是否成功
            success_indicators = [
                ".welcome",
                ".user-info",
                ".logout",
                ".dashboard",
                "[href*='logout']"
            ]
            
            login_success = False
            for selector in success_indicators:
                try:
                    element = await self.driver.wait_for_element(selector, timeout=5)
                    if element:
                        login_success = True
                        break
                except Exception:
                    continue
            
            # 检查是否还在登录页面（登录失败的指示）
            current_url = await self.driver.get_current_url()
            if "login" in current_url.lower() and not login_success:
                # 检查错误消息
                error_selectors = [
                    ".error",
                    ".error-message",
                    ".alert-danger",
                    ".login-error"
                ]
                
                error_message = "Login failed - still on login page"
                for selector in error_selectors:
                    try:
                        error_element = await self.driver.find_element(selector)
                        if error_element:
                            error_text = await self.driver.get_element_text(error_element)
                            if error_text:
                                error_message = f"Login failed: {error_text}"
                                break
                    except Exception:
                        continue
                
                raise Exception(error_message)
            
            # 获取登录后的页面信息
            page_title = await self.driver.get_page_title()
            final_url = await self.driver.get_current_url()
            
            result = {
                "username": username,
                "login_success": True,
                "final_url": final_url,
                "page_title": page_title,
                "status": "success"
            }
            
            # 保存到上下文
            context.set_shared_data("logged_in_user", username)
            context.set_shared_data("login_success", True)
            context.set_shared_data("current_url", final_url)
            
            self.logger.info(f"Successfully logged in as: {username}")
            return result
        
        except Exception as e:
            self.logger.error(f"Login failed for user {username}: {e}")
            # 截图以便调试
            try:
                await self.web_context.take_screenshot("login_failure")
            except Exception:
                pass
            raise
    
    @flow_step(
        name="web_navigate_to_products",
        description="导航到商品页面",
        platform="web",
        timeout=30,
        depends_on=["web_perform_login"]
    )
    async def navigate_to_products(self, context: FlowContext) -> Dict[str, Any]:
        """导航到商品页面
        
        Args:
            context: 流程上下文
        
        Returns:
            导航结果
        """
        products_url = context.get_data("products_url") or "/products"
        base_url = context.get_shared_data("current_url", "https://example.com")
        
        # 构建完整商品URL
        if products_url.startswith("http"):
            full_products_url = products_url
        else:
            # 从当前URL提取base URL
            if "://" in base_url:
                base_domain = "/".join(base_url.split("/")[:3])
            else:
                base_domain = "https://example.com"
            full_products_url = f"{base_domain}{products_url}"
        
        self.logger.info(f"Navigating to products page: {full_products_url}")
        
        try:
            await self.web_context.navigate_and_record(
                full_products_url,
                step_name="导航到商品页面"
            )
            
            # 等待商品列表加载
            product_list_selectors = [
                ".product-list",
                ".products",
                ".product-grid",
                ".product-item",
                "[data-testid='product-list']"
            ]
            
            products_loaded = False
            for selector in product_list_selectors:
                try:
                    await self.driver.wait_for_element(selector, timeout=10)
                    products_loaded = True
                    break
                except Exception:
                    continue
            
            if not products_loaded:
                self.logger.warning("Could not find product list, but continuing...")
            
            # 获取页面信息
            page_title = await self.driver.get_page_title()
            current_url = await self.driver.get_current_url()
            
            result = {
                "url": current_url,
                "title": page_title,
                "products_loaded": products_loaded,
                "status": "success"
            }
            
            # 保存到上下文
            context.set_shared_data("products_page_title", page_title)
            context.set_shared_data("current_url", current_url)
            
            self.logger.info(f"Successfully navigated to products page: {page_title}")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to navigate to products page: {e}")
            raise
    
    @flow_step(
        name="web_select_product",
        description="选择商品",
        platform="web",
        timeout=30,
        depends_on=["web_navigate_to_products"]
    )
    async def select_product(self, context: FlowContext) -> Dict[str, Any]:
        """选择商品
        
        Args:
            context: 流程上下文
        
        Returns:
            选择结果
        """
        product_name = context.get_data("product_name") or "第一个商品"
        
        self.logger.info(f"Selecting product: {product_name}")
        
        try:
            # 查找商品元素
            product_selectors = [
                ".product-item:first-child",
                ".product:first-child",
                ".product-card:first-child",
                "[data-testid='product-item']:first-child"
            ]
            
            product_selected = False
            selected_product_info = {}
            
            for selector in product_selectors:
                try:
                    # 等待商品元素出现
                    product_element = await self.driver.wait_for_element(selector, timeout=5)
                    if product_element:
                        # 获取商品信息
                        try:
                            product_title = await self.driver.get_element_text(
                                f"{selector} .product-title, {selector} .title, {selector} h3, {selector} h4"
                            )
                        except Exception:
                            product_title = "Unknown Product"
                        
                        try:
                            product_price = await self.driver.get_element_text(
                                f"{selector} .price, {selector} .product-price"
                            )
                        except Exception:
                            product_price = "Unknown Price"
                        
                        selected_product_info = {
                            "title": product_title,
                            "price": product_price,
                            "selector": selector
                        }
                        
                        # 点击商品
                        await self.web_context.click_and_record(
                            selector,
                            step_name="选择商品",
                            timeout=10
                        )
                        
                        product_selected = True
                        break
                except Exception:
                    continue
            
            if not product_selected:
                raise Exception("Could not find or select any product")
            
            # 等待商品详情页面加载
            await asyncio.sleep(2)
            
            # 验证是否进入商品详情页
            detail_selectors = [
                ".product-detail",
                ".product-info",
                ".add-to-cart",
                ".buy-now"
            ]
            
            on_detail_page = False
            for selector in detail_selectors:
                try:
                    await self.driver.wait_for_element(selector, timeout=5)
                    on_detail_page = True
                    break
                except Exception:
                    continue
            
            # 获取当前页面信息
            current_url = await self.driver.get_current_url()
            page_title = await self.driver.get_page_title()
            
            result = {
                "product_info": selected_product_info,
                "on_detail_page": on_detail_page,
                "current_url": current_url,
                "page_title": page_title,
                "status": "success"
            }
            
            # 保存到上下文
            context.set_shared_data("selected_product", selected_product_info)
            context.set_shared_data("current_url", current_url)
            
            self.logger.info(f"Successfully selected product: {selected_product_info.get('title', 'Unknown')}")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to select product: {e}")
            raise
    
    @flow_step(
        name="web_add_to_cart",
        description="添加到购物车",
        platform="web",
        timeout=30,
        retry_count=1,
        depends_on=["web_select_product"]
    )
    async def add_to_cart(self, context: FlowContext) -> Dict[str, Any]:
        """添加商品到购物车
        
        Args:
            context: 流程上下文
        
        Returns:
            添加结果
        """
        selected_product = context.get_shared_data("selected_product", {})
        product_title = selected_product.get("title", "Unknown Product")
        
        self.logger.info(f"Adding product to cart: {product_title}")
        
        try:
            # 查找加入购物车按钮
            add_to_cart_selectors = [
                ".add-to-cart",
                "#add-to-cart",
                ".add-cart",
                "button[contains(text(), '加入购物车')]",
                "button[contains(text(), 'Add to Cart')]",
                ".btn-add-cart"
            ]
            
            cart_added = False
            for selector in add_to_cart_selectors:
                try:
                    await self.web_context.click_and_record(
                        selector,
                        step_name="点击加入购物车",
                        timeout=5
                    )
                    cart_added = True
                    break
                except Exception:
                    continue
            
            if not cart_added:
                raise Exception("Could not find add to cart button")
            
            # 等待添加完成
            await asyncio.sleep(2)
            
            # 检查成功提示或购物车数量变化
            success_indicators = [
                ".cart-success",
                ".success-message",
                ".alert-success",
                ".cart-count",
                ".cart-badge"
            ]
            
            add_success = False
            success_message = ""
            
            for selector in success_indicators:
                try:
                    element = await self.driver.wait_for_element(selector, timeout=3)
                    if element:
                        try:
                            text = await self.driver.get_element_text(element)
                            if text:
                                success_message = text
                        except Exception:
                            pass
                        add_success = True
                        break
                except Exception:
                    continue
            
            # 如果没有明确的成功指示，检查购物车图标或数量
            if not add_success:
                cart_selectors = [".cart", ".shopping-cart", "#cart"]
                for selector in cart_selectors:
                    try:
                        cart_element = await self.driver.find_element(selector)
                        if cart_element:
                            add_success = True
                            break
                    except Exception:
                        continue
            
            result = {
                "product_title": product_title,
                "add_success": add_success,
                "success_message": success_message,
                "status": "success" if add_success else "warning"
            }
            
            # 保存到上下文
            context.set_shared_data("cart_item_added", product_title)
            context.set_shared_data("add_to_cart_success", add_success)
            
            if add_success:
                self.logger.info(f"Successfully added product to cart: {product_title}")
            else:
                self.logger.warning(f"Add to cart may have failed for: {product_title}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to add product to cart: {e}")
            raise
    
    @flow_step(
        name="web_proceed_to_checkout",
        description="进入结算页面",
        platform="web",
        timeout=60,
        depends_on=["web_add_to_cart"]
    )
    async def proceed_to_checkout(self, context: FlowContext) -> Dict[str, Any]:
        """进入结算页面
        
        Args:
            context: 流程上下文
        
        Returns:
            结算结果
        """
        self.logger.info("Proceeding to checkout")
        
        try:
            # 查找购物车链接或按钮
            cart_selectors = [
                ".cart",
                "#cart",
                ".shopping-cart",
                "[href*='cart']",
                "a[contains(text(), '购物车')]"
            ]
            
            cart_opened = False
            for selector in cart_selectors:
                try:
                    await self.web_context.click_and_record(
                        selector,
                        step_name="打开购物车",
                        timeout=5
                    )
                    cart_opened = True
                    break
                except Exception:
                    continue
            
            if cart_opened:
                # 等待购物车页面加载
                await asyncio.sleep(2)
            
            # 查找结算按钮
            checkout_selectors = [
                ".checkout",
                "#checkout",
                ".btn-checkout",
                "button[contains(text(), '结算')]",
                "button[contains(text(), 'Checkout')]",
                ".proceed-checkout"
            ]
            
            checkout_clicked = False
            for selector in checkout_selectors:
                try:
                    await self.web_context.click_and_record(
                        selector,
                        step_name="点击结算",
                        timeout=5
                    )
                    checkout_clicked = True
                    break
                except Exception:
                    continue
            
            if not checkout_clicked:
                # 如果没有找到结算按钮，尝试直接导航到结算页面
                checkout_url = "/checkout"
                current_url = context.get_shared_data("current_url", "https://example.com")
                
                if "://" in current_url:
                    base_domain = "/".join(current_url.split("/")[:3])
                else:
                    base_domain = "https://example.com"
                
                full_checkout_url = f"{base_domain}{checkout_url}"
                
                await self.web_context.navigate_and_record(
                    full_checkout_url,
                    step_name="导航到结算页面"
                )
            
            # 等待结算页面加载
            await asyncio.sleep(3)
            
            # 验证是否在结算页面
            checkout_indicators = [
                ".checkout-form",
                ".billing-info",
                ".payment-method",
                ".order-summary",
                "form[action*='checkout']"
            ]
            
            on_checkout_page = False
            for selector in checkout_indicators:
                try:
                    await self.driver.wait_for_element(selector, timeout=5)
                    on_checkout_page = True
                    break
                except Exception:
                    continue
            
            # 获取页面信息
            current_url = await self.driver.get_current_url()
            page_title = await self.driver.get_page_title()
            
            result = {
                "on_checkout_page": on_checkout_page,
                "current_url": current_url,
                "page_title": page_title,
                "status": "success" if on_checkout_page else "warning"
            }
            
            # 保存到上下文
            context.set_shared_data("on_checkout_page", on_checkout_page)
            context.set_shared_data("current_url", current_url)
            
            if on_checkout_page:
                self.logger.info("Successfully reached checkout page")
            else:
                self.logger.warning("May not be on checkout page, but continuing...")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to proceed to checkout: {e}")
            raise


# 便捷函数

def create_web_steps(web_context):
    """创建Web步骤实例
    
    Args:
        web_context: Web测试上下文
    
    Returns:
        Web步骤实例
    """
    return WebLoginBuySteps(web_context)


if __name__ == "__main__":
    # 测试Web步骤
    print("Web Login Buy Steps module loaded successfully")
    print("Available steps:")
    
    steps = [
        "navigate_to_homepage",
        "navigate_to_login", 
        "perform_login",
        "navigate_to_products",
        "select_product",
        "add_to_cart",
        "proceed_to_checkout"
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")
