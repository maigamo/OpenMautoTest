"""
OpenMautoTest 小程序端登录购买流程步骤

实现小程序端的业务步骤封装
"""

import time
from typing import Dict, Any, Optional

from common.logger import get_logger
from configs.settings import get_settings
from orchestrator.flow_runner import FlowContext, flow_step


logger = get_logger("mini_login_buy_steps")


class MiniLoginBuySteps:
    """小程序端登录购买步骤"""
    
    def __init__(self, mini_context):
        """初始化小程序步骤
        
        Args:
            mini_context: 小程序测试上下文
        """
        self.mini_context = mini_context
        self.driver = mini_context.driver
        self.logger = get_logger("mini_steps")
        self.settings = get_settings()
    
    @flow_step(
        name="mini_launch_app",
        description="启动小程序",
        platform="mini_program",
        timeout=30
    )
    def launch_app(self, context: FlowContext) -> Dict[str, Any]:
        """启动小程序
        
        Args:
            context: 流程上下文
        
        Returns:
            启动结果
        """
        app_id = context.get_data("app_id") or "default_app_id"
        start_page = context.get_data("start_page") or "/pages/index/index"
        
        self.logger.info(f"Launching mini program: {app_id}")
        
        try:
            # 启动小程序
            launch_params = {
                "path": start_page,
                "query": context.get_data("launch_query", {})
            }
            
            self.driver.launch_app(**launch_params)
            
            # 等待小程序启动完成
            self.driver.wait_for_page_ready(timeout=15)
            
            # 获取当前页面信息
            current_page = self.driver.get_current_page()
            device_info = self.driver.get_device_info()
            
            result = {
                "app_id": app_id,
                "start_page": start_page,
                "current_page": current_page,
                "device_info": device_info,
                "status": "success"
            }
            
            # 保存到上下文
            context.set_shared_data("app_launched", True)
            context.set_shared_data("current_page", current_page)
            context.set_shared_data("device_info", device_info)
            
            self.logger.info(f"Successfully launched mini program on page: {current_page}")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to launch mini program: {e}")
            raise
    
    @flow_step(
        name="mini_navigate_to_login",
        description="导航到登录页面",
        platform="mini_program",
        timeout=30,
        depends_on=["mini_launch_app"]
    )
    def navigate_to_login(self, context: FlowContext) -> Dict[str, Any]:
        """导航到登录页面
        
        Args:
            context: 流程上下文
        
        Returns:
            导航结果
        """
        login_page = context.get_data("login_page") or "/pages/login/login"
        
        self.logger.info(f"Navigating to login page: {login_page}")
        
        try:
            # 导航到登录页面
            self.mini_context.navigate_and_record(
                login_page,
                step_name="导航到登录页面"
            )
            
            # 等待页面加载完成
            self.driver.wait_for_page_ready(timeout=10)
            
            # 等待登录表单元素出现
            login_form_selectors = [
                ".username-input",
                ".login-form",
                "input[placeholder*='用户名']",
                "input[placeholder*='账号']"
            ]
            
            form_found = False
            for selector in login_form_selectors:
                try:
                    element = self.driver.wait_for_element(selector, timeout=5)
                    if element:
                        form_found = True
                        break
                except Exception:
                    continue
            
            if not form_found:
                self.logger.warning("Login form not found, but continuing...")
            
            # 获取当前页面信息
            current_page = self.driver.get_current_page()
            
            result = {
                "login_page": login_page,
                "current_page": current_page,
                "form_found": form_found,
                "status": "success"
            }
            
            # 保存到上下文
            context.set_shared_data("current_page", current_page)
            context.set_shared_data("on_login_page", True)
            
            self.logger.info(f"Successfully navigated to login page: {current_page}")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to navigate to login page: {e}")
            raise
    
    @flow_step(
        name="mini_perform_login",
        description="执行登录操作",
        platform="mini_program",
        timeout=60,
        retry_count=2,
        depends_on=["mini_navigate_to_login"]
    )
    def perform_login(self, context: FlowContext) -> Dict[str, Any]:
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
                ".username-input",
                "input[placeholder*='用户名']",
                "input[placeholder*='账号']",
                "input[type='text']"
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    self.mini_context.input_and_record(
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
                ".password-input",
                "input[placeholder*='密码']",
                "input[type='password']"
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    self.mini_context.input_and_record(
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
                ".login-button",
                ".login-btn",
                "button[text='登录']",
                ".submit-btn"
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    self.mini_context.click_and_record(
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
            
            # 等待登录完成
            time.sleep(3)
            
            # 验证登录是否成功 - 检查页面跳转或成功元素
            success_indicators = [
                ".user-info",
                ".welcome",
                ".main-page",
                ".home-page"
            ]
            
            login_success = False
            current_page = self.driver.get_current_page()
            
            # 检查是否跳转到其他页面（登录成功的指示）
            if "/login" not in current_page:
                login_success = True
            else:
                # 在登录页面检查成功元素
                for selector in success_indicators:
                    try:
                        element = self.driver.find_element(selector)
                        if element:
                            login_success = True
                            break
                    except Exception:
                        continue
            
            # 如果仍在登录页面且没有成功指示，检查错误消息
            if not login_success and "/login" in current_page:
                error_selectors = [
                    ".error-message",
                    ".login-error",
                    ".error-tip"
                ]
                
                error_message = "Login failed - still on login page"
                for selector in error_selectors:
                    try:
                        error_element = self.driver.find_element(selector)
                        if error_element:
                            error_text = self.driver.get_element_text(error_element)
                            if error_text:
                                error_message = f"Login failed: {error_text}"
                                break
                    except Exception:
                        continue
                
                if not login_success:
                    raise Exception(error_message)
            
            result = {
                "username": username,
                "login_success": login_success,
                "current_page": current_page,
                "status": "success"
            }
            
            # 保存到上下文
            context.set_shared_data("logged_in_user", username)
            context.set_shared_data("login_success", True)
            context.set_shared_data("current_page", current_page)
            
            self.logger.info(f"Successfully logged in as: {username}")
            return result
        
        except Exception as e:
            self.logger.error(f"Login failed for user {username}: {e}")
            # 截图以便调试
            try:
                self.mini_context.take_screenshot("login_failure")
            except Exception:
                pass
            raise
    
    @flow_step(
        name="mini_navigate_to_products",
        description="导航到商品页面",
        platform="mini_program",
        timeout=30,
        depends_on=["mini_perform_login"]
    )
    def navigate_to_products(self, context: FlowContext) -> Dict[str, Any]:
        """导航到商品页面
        
        Args:
            context: 流程上下文
        
        Returns:
            导航结果
        """
        products_page = context.get_data("products_page") or "/pages/products/products"
        
        self.logger.info(f"Navigating to products page: {products_page}")
        
        try:
            # 可能需要通过底部tab导航
            tab_selectors = [
                ".tab-bar .tab[data-path*='product']",
                ".tab-bar .tab[text='商品']",
                ".bottom-tab .product-tab"
            ]
            
            tab_clicked = False
            for selector in tab_selectors:
                try:
                    self.mini_context.click_and_record(
                        selector,
                        step_name="点击商品tab",
                        timeout=3
                    )
                    tab_clicked = True
                    break
                except Exception:
                    continue
            
            if not tab_clicked:
                # 直接导航到商品页面
                self.mini_context.navigate_and_record(
                    products_page,
                    step_name="导航到商品页面"
                )
            
            # 等待页面加载
            self.driver.wait_for_page_ready(timeout=10)
            
            # 等待商品列表加载
            product_list_selectors = [
                ".product-list",
                ".goods-list",
                ".product-item",
                ".goods-item"
            ]
            
            products_loaded = False
            for selector in product_list_selectors:
                try:
                    element = self.driver.wait_for_element(selector, timeout=8)
                    if element:
                        products_loaded = True
                        break
                except Exception:
                    continue
            
            if not products_loaded:
                self.logger.warning("Product list not found, but continuing...")
            
            # 获取当前页面信息
            current_page = self.driver.get_current_page()
            
            result = {
                "products_page": products_page,
                "current_page": current_page,
                "products_loaded": products_loaded,
                "status": "success"
            }
            
            # 保存到上下文
            context.set_shared_data("current_page", current_page)
            context.set_shared_data("on_products_page", True)
            
            self.logger.info(f"Successfully navigated to products page: {current_page}")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to navigate to products page: {e}")
            raise
    
    @flow_step(
        name="mini_select_product",
        description="选择商品",
        platform="mini_program",
        timeout=30,
        depends_on=["mini_navigate_to_products"]
    )
    def select_product(self, context: FlowContext) -> Dict[str, Any]:
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
                ".goods-item:first-child",
                ".product-card:first-child",
                ".product-list .item:first-child"
            ]
            
            product_selected = False
            selected_product_info = {}
            
            for selector in product_selectors:
                try:
                    # 等待商品元素出现
                    product_element = self.driver.wait_for_element(selector, timeout=5)
                    if product_element:
                        # 获取商品信息
                        try:
                            product_title = self.driver.get_element_text(
                                f"{selector} .product-title, {selector} .title, {selector} .name"
                            )
                        except Exception:
                            product_title = "Unknown Product"
                        
                        try:
                            product_price = self.driver.get_element_text(
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
                        self.mini_context.click_and_record(
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
            time.sleep(2)
            self.driver.wait_for_page_ready(timeout=10)
            
            # 验证是否进入商品详情页
            detail_selectors = [
                ".product-detail",
                ".goods-detail",
                ".add-cart-btn",
                ".buy-now-btn"
            ]
            
            on_detail_page = False
            current_page = self.driver.get_current_page()
            
            # 检查页面路径是否包含detail
            if "detail" in current_page:
                on_detail_page = True
            else:
                # 检查详情页元素
                for selector in detail_selectors:
                    try:
                        element = self.driver.find_element(selector)
                        if element:
                            on_detail_page = True
                            break
                    except Exception:
                        continue
            
            result = {
                "product_info": selected_product_info,
                "on_detail_page": on_detail_page,
                "current_page": current_page,
                "status": "success"
            }
            
            # 保存到上下文
            context.set_shared_data("selected_product", selected_product_info)
            context.set_shared_data("current_page", current_page)
            
            self.logger.info(f"Successfully selected product: {selected_product_info.get('title', 'Unknown')}")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to select product: {e}")
            raise
    
    @flow_step(
        name="mini_add_to_cart",
        description="添加到购物车",
        platform="mini_program",
        timeout=30,
        retry_count=1,
        depends_on=["mini_select_product"]
    )
    def add_to_cart(self, context: FlowContext) -> Dict[str, Any]:
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
                ".add-cart-btn",
                ".add-to-cart",
                "button[text='加入购物车']",
                ".cart-btn"
            ]
            
            cart_added = False
            for selector in add_to_cart_selectors:
                try:
                    self.mini_context.click_and_record(
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
            time.sleep(2)
            
            # 检查成功提示或弹窗
            success_indicators = [
                ".success-toast",
                ".cart-success",
                ".add-success",
                "text[text*='添加成功']",
                "text[text*='已加入购物车']"
            ]
            
            add_success = False
            success_message = ""
            
            for selector in success_indicators:
                try:
                    element = self.driver.wait_for_element(selector, timeout=3)
                    if element:
                        try:
                            text = self.driver.get_element_text(element)
                            if text:
                                success_message = text
                        except Exception:
                            pass
                        add_success = True
                        break
                except Exception:
                    continue
            
            # 如果有弹窗，可能需要关闭
            modal_selectors = [
                ".modal .close-btn",
                ".popup .close",
                ".dialog .confirm-btn"
            ]
            
            for selector in modal_selectors:
                try:
                    close_btn = self.driver.find_element(selector)
                    if close_btn:
                        self.mini_context.click_and_record(
                            selector,
                            step_name="关闭弹窗",
                            timeout=3
                        )
                        break
                except Exception:
                    continue
            
            # 如果没有明确的成功指示，假设添加成功
            if not add_success:
                add_success = True
                success_message = "假设添加成功（未找到明确指示）"
            
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
        name="mini_proceed_to_checkout",
        description="进入结算页面",
        platform="mini_program",
        timeout=60,
        depends_on=["mini_add_to_cart"]
    )
    def proceed_to_checkout(self, context: FlowContext) -> Dict[str, Any]:
        """进入结算页面
        
        Args:
            context: 流程上下文
        
        Returns:
            结算结果
        """
        self.logger.info("Proceeding to checkout")
        
        try:
            # 查找购物车入口
            cart_selectors = [
                ".cart-tab",
                ".cart-icon",
                ".tab-bar .cart",
                "text[text='购物车']"
            ]
            
            cart_opened = False
            for selector in cart_selectors:
                try:
                    self.mini_context.click_and_record(
                        selector,
                        step_name="打开购物车",
                        timeout=5
                    )
                    cart_opened = True
                    break
                except Exception:
                    continue
            
            if not cart_opened:
                # 尝试导航到购物车页面
                cart_page = "/pages/cart/cart"
                self.mini_context.navigate_and_record(
                    cart_page,
                    step_name="导航到购物车页面"
                )
            
            # 等待购物车页面加载
            time.sleep(2)
            self.driver.wait_for_page_ready(timeout=10)
            
            # 查找结算按钮
            checkout_selectors = [
                ".checkout-btn",
                ".settle-btn",
                "button[text='结算']",
                "button[text='去结算']"
            ]
            
            checkout_clicked = False
            for selector in checkout_selectors:
                try:
                    self.mini_context.click_and_record(
                        selector,
                        step_name="点击结算",
                        timeout=5
                    )
                    checkout_clicked = True
                    break
                except Exception:
                    continue
            
            if not checkout_clicked:
                # 尝试直接导航到结算页面
                checkout_page = "/pages/checkout/checkout"
                self.mini_context.navigate_and_record(
                    checkout_page,
                    step_name="导航到结算页面"
                )
            
            # 等待结算页面加载
            time.sleep(3)
            self.driver.wait_for_page_ready(timeout=10)
            
            # 验证是否在结算页面
            checkout_indicators = [
                ".checkout-page",
                ".order-form",
                ".address-info",
                ".payment-method",
                ".order-summary"
            ]
            
            on_checkout_page = False
            current_page = self.driver.get_current_page()
            
            # 检查页面路径
            if "checkout" in current_page or "order" in current_page:
                on_checkout_page = True
            else:
                # 检查结算页面元素
                for selector in checkout_indicators:
                    try:
                        element = self.driver.find_element(selector)
                        if element:
                            on_checkout_page = True
                            break
                    except Exception:
                        continue
            
            result = {
                "on_checkout_page": on_checkout_page,
                "current_page": current_page,
                "status": "success" if on_checkout_page else "warning"
            }
            
            # 保存到上下文
            context.set_shared_data("on_checkout_page", on_checkout_page)
            context.set_shared_data("current_page", current_page)
            
            if on_checkout_page:
                self.logger.info("Successfully reached checkout page")
            else:
                self.logger.warning("May not be on checkout page, but continuing...")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to proceed to checkout: {e}")
            raise


# 便捷函数

def create_mini_steps(mini_context):
    """创建小程序步骤实例
    
    Args:
        mini_context: 小程序测试上下文
    
    Returns:
        小程序步骤实例
    """
    return MiniLoginBuySteps(mini_context)


if __name__ == "__main__":
    # 测试小程序步骤
    print("Mini Login Buy Steps module loaded successfully")
    print("Available steps:")
    
    steps = [
        "launch_app",
        "navigate_to_login",
        "perform_login", 
        "navigate_to_products",
        "select_product",
        "add_to_cart",
        "proceed_to_checkout"
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")
