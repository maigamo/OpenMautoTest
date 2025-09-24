"""
OpenMautoTest 登录购买流程端到端测试用例

实现Web端和小程序端的协同测试
"""

import asyncio
import pytest
from typing import Dict, Any

from common.logger import get_logger
from configs.settings import get_settings
from orchestrator.flow_runner import create_flow, FlowContext
from orchestrator.fixtures.web_context import web_context, web_test_data
from orchestrator.fixtures.mini_context import mini_context, mini_test_data
from flows.login_and_buy.web_steps import create_web_steps
from flows.login_and_buy.mini_steps import create_mini_steps


logger = get_logger("login_buy_flow_test")


class TestLoginBuyFlow:
    """登录购买流程测试类"""
    
    @pytest.mark.asyncio
    async def test_web_login_and_buy_flow(self, web_context, web_test_data):
        """Web端登录购买完整流程测试
        
        Args:
            web_context: Web测试上下文
            web_test_data: Web测试数据
        """
        logger.info("Starting Web login and buy flow test")
        
        try:
            # 创建流程执行器
            flow = create_flow("web_login_buy_flow", "Web端登录购买流程")
            
            # 创建Web步骤实例
            web_steps = create_web_steps(web_context)
            
            # 添加流程步骤
            flow.add_step(
                "navigate_homepage",
                web_steps.navigate_to_homepage,
                "导航到首页",
                "web",
                timeout=30
            )
            
            flow.add_step(
                "navigate_login",
                web_steps.navigate_to_login,
                "导航到登录页面",
                "web",
                timeout=30,
                depends_on=["navigate_homepage"]
            )
            
            flow.add_step(
                "perform_login",
                web_steps.perform_login,
                "执行登录操作",
                "web",
                timeout=60,
                retry_count=2,
                depends_on=["navigate_login"]
            )
            
            flow.add_step(
                "navigate_products",
                web_steps.navigate_to_products,
                "导航到商品页面",
                "web",
                timeout=30,
                depends_on=["perform_login"]
            )
            
            flow.add_step(
                "select_product",
                web_steps.select_product,
                "选择商品",
                "web",
                timeout=30,
                depends_on=["navigate_products"]
            )
            
            flow.add_step(
                "add_to_cart",
                web_steps.add_to_cart,
                "添加到购物车",
                "web",
                timeout=30,
                retry_count=1,
                depends_on=["select_product"]
            )
            
            flow.add_step(
                "proceed_checkout",
                web_steps.proceed_to_checkout,
                "进入结算页面",
                "web",
                timeout=60,
                depends_on=["add_to_cart"]
            )
            
            # 准备测试数据
            test_context_data = {
                "base_url": web_test_data.get("base_url", "https://example.com"),
                "login_url": "/login",
                "products_url": "/products",
                "username": web_test_data["test_user"]["username"],
                "password": web_test_data["test_user"]["password"],
                "product_name": "测试商品"
            }
            
            # 执行流程
            result = await flow.run(**test_context_data)
            
            # 验证流程执行结果
            assert result["status"] == "passed", f"Flow failed: {result}"
            assert result["completed_steps"] > 0, "No steps completed"
            assert result["failed_steps"] == 0, f"Failed steps: {result['failed_steps']}"
            
            # 验证关键步骤结果
            login_step = next((s for s in result["steps"] if s["name"] == "perform_login"), None)
            assert login_step is not None, "Login step not found"
            assert login_step["status"] == "passed", "Login step failed"
            
            cart_step = next((s for s in result["steps"] if s["name"] == "add_to_cart"), None)
            assert cart_step is not None, "Add to cart step not found"
            assert cart_step["status"] == "passed", "Add to cart step failed"
            
            # 验证共享数据
            assert result["shared_data"].get("login_success") is True, "Login not successful"
            assert result["shared_data"].get("logged_in_user") == test_context_data["username"], "Wrong logged in user"
            
            logger.info(f"Web flow completed successfully in {result['duration']:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Web login buy flow test failed: {e}")
            raise
    
    def test_mini_login_and_buy_flow(self, mini_context, mini_test_data):
        """小程序端登录购买完整流程测试
        
        Args:
            mini_context: 小程序测试上下文
            mini_test_data: 小程序测试数据
        """
        logger.info("Starting Mini program login and buy flow test")
        
        try:
            # 创建流程执行器
            flow = create_flow("mini_login_buy_flow", "小程序端登录购买流程")
            
            # 创建小程序步骤实例
            mini_steps = create_mini_steps(mini_context)
            
            # 添加流程步骤
            flow.add_step(
                "launch_app",
                mini_steps.launch_app,
                "启动小程序",
                "mini_program",
                timeout=30
            )
            
            flow.add_step(
                "navigate_login",
                mini_steps.navigate_to_login,
                "导航到登录页面",
                "mini_program",
                timeout=30,
                depends_on=["launch_app"]
            )
            
            flow.add_step(
                "perform_login",
                mini_steps.perform_login,
                "执行登录操作",
                "mini_program",
                timeout=60,
                retry_count=2,
                depends_on=["navigate_login"]
            )
            
            flow.add_step(
                "navigate_products",
                mini_steps.navigate_to_products,
                "导航到商品页面",
                "mini_program",
                timeout=30,
                depends_on=["perform_login"]
            )
            
            flow.add_step(
                "select_product",
                mini_steps.select_product,
                "选择商品",
                "mini_program",
                timeout=30,
                depends_on=["navigate_products"]
            )
            
            flow.add_step(
                "add_to_cart",
                mini_steps.add_to_cart,
                "添加到购物车",
                "mini_program",
                timeout=30,
                retry_count=1,
                depends_on=["select_product"]
            )
            
            flow.add_step(
                "proceed_checkout",
                mini_steps.proceed_to_checkout,
                "进入结算页面",
                "mini_program",
                timeout=60,
                depends_on=["add_to_cart"]
            )
            
            # 准备测试数据
            test_context_data = {
                "app_id": mini_test_data.get("app_id", "test_app_id"),
                "start_page": mini_test_data.get("start_page", "/pages/index/index"),
                "login_page": "/pages/login/login",
                "products_page": "/pages/products/products",
                "username": mini_test_data["test_user"]["username"],
                "password": mini_test_data["test_user"]["password"],
                "product_name": "测试商品"
            }
            
            # 执行流程（同步方式，因为小程序驱动器是同步的）
            import asyncio
            result = asyncio.run(flow.run(**test_context_data))
            
            # 验证流程执行结果
            assert result["status"] == "passed", f"Flow failed: {result}"
            assert result["completed_steps"] > 0, "No steps completed"
            assert result["failed_steps"] == 0, f"Failed steps: {result['failed_steps']}"
            
            # 验证关键步骤结果
            launch_step = next((s for s in result["steps"] if s["name"] == "launch_app"), None)
            assert launch_step is not None, "Launch app step not found"
            assert launch_step["status"] == "passed", "Launch app step failed"
            
            login_step = next((s for s in result["steps"] if s["name"] == "perform_login"), None)
            assert login_step is not None, "Login step not found"
            assert login_step["status"] == "passed", "Login step failed"
            
            cart_step = next((s for s in result["steps"] if s["name"] == "add_to_cart"), None)
            assert cart_step is not None, "Add to cart step not found"
            assert cart_step["status"] == "passed", "Add to cart step failed"
            
            # 验证共享数据
            assert result["shared_data"].get("login_success") is True, "Login not successful"
            assert result["shared_data"].get("logged_in_user") == test_context_data["username"], "Wrong logged in user"
            
            logger.info(f"Mini program flow completed successfully in {result['duration']:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Mini program login buy flow test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_cross_platform_data_sharing(self, web_context, mini_context, web_test_data, mini_test_data):
        """跨平台数据共享测试
        
        验证Web端和小程序端之间的数据传递
        
        Args:
            web_context: Web测试上下文
            mini_context: 小程序测试上下文
            web_test_data: Web测试数据
            mini_test_data: 小程序测试数据
        """
        logger.info("Starting cross-platform data sharing test")
        
        try:
            # 创建跨平台流程
            flow = create_flow("cross_platform_flow", "跨平台数据共享流程")
            
            # 创建步骤实例
            web_steps = create_web_steps(web_context)
            mini_steps = create_mini_steps(mini_context)
            
            # Web端登录步骤
            flow.add_step(
                "web_login",
                web_steps.perform_login,
                "Web端登录",
                "web",
                timeout=60
            )
            
            # 小程序启动步骤（依赖Web登录完成）
            flow.add_step(
                "mini_launch",
                mini_steps.launch_app,
                "启动小程序",
                "mini_program",
                timeout=30,
                depends_on=["web_login"]
            )
            
            # 数据验证步骤
            async def verify_data_sharing(context: FlowContext) -> Dict[str, Any]:
                """验证数据共享"""
                web_user = context.get_shared_data("logged_in_user")
                mini_launched = context.get_shared_data("app_launched")
                
                return {
                    "web_user": web_user,
                    "mini_launched": mini_launched,
                    "data_shared": web_user is not None and mini_launched is True
                }
            
            flow.add_step(
                "verify_sharing",
                verify_data_sharing,
                "验证数据共享",
                "test",
                timeout=10,
                depends_on=["web_login", "mini_launch"]
            )
            
            # 准备测试数据
            test_context_data = {
                "base_url": web_test_data.get("base_url", "https://example.com"),
                "username": web_test_data["test_user"]["username"],
                "password": web_test_data["test_user"]["password"],
                "app_id": mini_test_data.get("app_id", "test_app_id")
            }
            
            # 执行流程
            result = await flow.run(**test_context_data)
            
            # 验证结果
            assert result["status"] == "passed", f"Cross-platform flow failed: {result}"
            
            # 验证数据共享步骤
            verify_step = next((s for s in result["steps"] if s["name"] == "verify_sharing"), None)
            assert verify_step is not None, "Data sharing verification step not found"
            assert verify_step["status"] == "passed", "Data sharing verification failed"
            assert verify_step["result"]["data_shared"] is True, "Data not properly shared between platforms"
            
            logger.info("Cross-platform data sharing test completed successfully")
            
        except Exception as e:
            logger.error(f"Cross-platform data sharing test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_flow_error_handling(self, web_context, web_test_data):
        """流程错误处理测试
        
        验证流程在遇到错误时的处理机制
        
        Args:
            web_context: Web测试上下文
            web_test_data: Web测试数据
        """
        logger.info("Starting flow error handling test")
        
        try:
            # 创建包含故意失败步骤的流程
            flow = create_flow("error_handling_flow", "错误处理流程")
            
            # 正常步骤
            web_steps = create_web_steps(web_context)
            flow.add_step(
                "navigate_homepage",
                web_steps.navigate_to_homepage,
                "导航到首页",
                "web",
                timeout=30
            )
            
            # 故意失败的步骤
            async def failing_step(context: FlowContext) -> Dict[str, Any]:
                """故意失败的步骤"""
                raise Exception("This step is designed to fail")
            
            flow.add_step(
                "failing_step",
                failing_step,
                "故意失败的步骤",
                "test",
                timeout=10,
                continue_on_failure=True,  # 允许失败后继续
                depends_on=["navigate_homepage"]
            )
            
            # 后续步骤（应该被跳过或继续执行）
            async def recovery_step(context: FlowContext) -> Dict[str, Any]:
                """恢复步骤"""
                return {"recovered": True}
            
            flow.add_step(
                "recovery_step",
                recovery_step,
                "恢复步骤",
                "test",
                timeout=10,
                depends_on=["failing_step"]
            )
            
            # 准备测试数据
            test_context_data = {
                "base_url": web_test_data.get("base_url", "https://example.com")
            }
            
            # 执行流程
            result = await flow.run(**test_context_data)
            
            # 验证错误处理
            assert result["failed_steps"] == 0, "Flow should handle failures gracefully"
            assert result["skipped_steps"] == 1, "Failing step should be skipped"
            
            # 验证失败步骤状态
            failing_step_result = next((s for s in result["steps"] if s["name"] == "failing_step"), None)
            assert failing_step_result is not None, "Failing step not found"
            assert failing_step_result["status"] == "skipped", "Failing step should be marked as skipped"
            
            # 验证恢复步骤状态
            recovery_step_result = next((s for s in result["steps"] if s["name"] == "recovery_step"), None)
            assert recovery_step_result is not None, "Recovery step not found"
            assert recovery_step_result["status"] == "skipped", "Recovery step should be skipped due to dependency"
            
            logger.info("Flow error handling test completed successfully")
            
        except Exception as e:
            logger.error(f"Flow error handling test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_flow_retry_mechanism(self, web_context, web_test_data):
        """流程重试机制测试
        
        验证步骤的重试功能
        
        Args:
            web_context: Web测试上下文
            web_test_data: Web测试数据
        """
        logger.info("Starting flow retry mechanism test")
        
        try:
            # 创建包含重试步骤的流程
            flow = create_flow("retry_flow", "重试机制流程")
            
            # 计数器用于模拟重试
            attempt_counter = {"count": 0}
            
            async def retry_step(context: FlowContext) -> Dict[str, Any]:
                """需要重试的步骤"""
                attempt_counter["count"] += 1
                
                if attempt_counter["count"] < 3:
                    # 前两次尝试失败
                    raise Exception(f"Attempt {attempt_counter['count']} failed")
                else:
                    # 第三次尝试成功
                    return {"attempt": attempt_counter["count"], "success": True}
            
            flow.add_step(
                "retry_step",
                retry_step,
                "重试步骤",
                "test",
                timeout=10,
                retry_count=3  # 允许重试3次
            )
            
            # 执行流程
            result = await flow.run()
            
            # 验证重试机制
            assert result["status"] == "passed", f"Retry flow should succeed: {result}"
            
            # 验证重试步骤
            retry_step_result = next((s for s in result["steps"] if s["name"] == "retry_step"), None)
            assert retry_step_result is not None, "Retry step not found"
            assert retry_step_result["status"] == "passed", "Retry step should eventually succeed"
            assert retry_step_result["retry_attempts"] == 2, "Should have 2 retry attempts"
            assert retry_step_result["result"]["attempt"] == 3, "Should succeed on 3rd attempt"
            
            logger.info("Flow retry mechanism test completed successfully")
            
        except Exception as e:
            logger.error(f"Flow retry mechanism test failed: {e}")
            raise


# 单独的测试函数（用于快速测试特定功能）

@pytest.mark.asyncio
async def test_web_only_login(web_context, web_test_data):
    """仅Web端登录测试（快速测试）"""
    logger.info("Starting web-only login test")
    
    web_steps = create_web_steps(web_context)
    
    # 简单的登录流程
    flow = create_flow("web_login_only", "仅Web登录")
    flow.add_step("navigate_homepage", web_steps.navigate_to_homepage, "导航首页", "web")
    flow.add_step("navigate_login", web_steps.navigate_to_login, "导航登录", "web", depends_on=["navigate_homepage"])
    flow.add_step("perform_login", web_steps.perform_login, "执行登录", "web", depends_on=["navigate_login"])
    
    result = await flow.run(
        base_url=web_test_data.get("base_url", "https://example.com"),
        username=web_test_data["test_user"]["username"],
        password=web_test_data["test_user"]["password"]
    )
    
    assert result["status"] == "passed"
    assert result["shared_data"]["login_success"] is True
    
    logger.info("Web-only login test completed successfully")


def test_mini_only_launch(mini_context, mini_test_data):
    """仅小程序启动测试（快速测试）"""
    logger.info("Starting mini-only launch test")
    
    mini_steps = create_mini_steps(mini_context)
    
    # 简单的启动流程
    flow = create_flow("mini_launch_only", "仅小程序启动")
    flow.add_step("launch_app", mini_steps.launch_app, "启动应用", "mini_program")
    
    import asyncio
    result = asyncio.run(flow.run(
        app_id=mini_test_data.get("app_id", "test_app_id"),
        start_page=mini_test_data.get("start_page", "/pages/index/index")
    ))
    
    assert result["status"] == "passed"
    assert result["shared_data"]["app_launched"] is True
    
    logger.info("Mini-only launch test completed successfully")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
