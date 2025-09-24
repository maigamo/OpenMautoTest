"""
OpenMautoTest 参数化测试用例示例

展示如何实现测试用例的参数化执行，支持多种测试场景和数据驱动测试
"""

import asyncio
import pytest
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

from common.logger import get_logger
from configs.settings import get_settings
from orchestrator.flow_runner import create_flow, FlowContext
from orchestrator.fixtures.web_context import web_context, web_test_data
from orchestrator.fixtures.mini_context import mini_context, mini_test_data
from flows.login_and_buy.web_steps import create_web_steps
from flows.login_and_buy.mini_steps import create_mini_steps


logger = get_logger("parameterized_flow_test")


@dataclass
class TestUser:
    """测试用户数据类"""
    username: str
    password: str
    user_type: str
    expected_result: str
    description: str


@dataclass
class ProductInfo:
    """商品信息数据类"""
    product_id: str
    product_name: str
    category: str
    price: float
    stock: int


@dataclass
class TestEnvironment:
    """测试环境配置"""
    env_name: str
    base_url: str
    api_url: str
    timeout: int


class TestParameterizedFlow:
    """参数化流程测试类"""
    
    # 测试用户数据
    TEST_USERS = [
        TestUser(
            username="user001",
            password="password123",
            user_type="normal",
            expected_result="success",
            description="普通用户登录"
        ),
        TestUser(
            username="vip001",
            password="vippass456",
            user_type="vip",
            expected_result="success",
            description="VIP用户登录"
        ),
        TestUser(
            username="admin001",
            password="adminpass789",
            user_type="admin",
            expected_result="success",
            description="管理员用户登录"
        ),
        TestUser(
            username="invalid_user",
            password="wrong_password",
            user_type="normal",
            expected_result="failure",
            description="无效用户登录"
        ),
        TestUser(
            username="",
            password="",
            user_type="empty",
            expected_result="failure",
            description="空用户名密码登录"
        ),
        TestUser(
            username="test@example.com",
            password="short",
            user_type="normal",
            expected_result="failure",
            description="密码过短登录"
        )
    ]
    
    # 商品测试数据
    TEST_PRODUCTS = [
        ProductInfo(
            product_id="P001",
            product_name="智能手机",
            category="电子产品",
            price=2999.00,
            stock=50
        ),
        ProductInfo(
            product_id="P002",
            product_name="笔记本电脑",
            category="电子产品",
            price=5999.00,
            stock=20
        ),
        ProductInfo(
            product_id="P003",
            product_name="运动鞋",
            category="服装鞋帽",
            price=399.00,
            stock=100
        )
    ]
    
    # 环境配置数据
    TEST_ENVIRONMENTS = [
        TestEnvironment(
            env_name="development",
            base_url="http://dev.example.com",
            api_url="http://dev-api.example.com",
            timeout=30
        ),
        TestEnvironment(
            env_name="testing",
            base_url="http://test.example.com",
            api_url="http://test-api.example.com",
            timeout=45
        ),
        TestEnvironment(
            env_name="staging",
            base_url="http://staging.example.com",
            api_url="http://staging-api.example.com",
            timeout=60
        )
    ]
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_user", TEST_USERS, ids=[u.description for u in TEST_USERS])
    async def test_login_with_different_users(self, web_context, test_user: TestUser):
        """测试不同类型用户的登录功能
        
        Args:
            web_context: Web测试上下文
            test_user: 测试用户数据
        """
        logger.info(f"Testing login for: {test_user.description}")
        
        try:
            # 创建流程执行器
            flow = create_flow(
                f"login_test_{test_user.user_type}",
                f"用户登录测试 - {test_user.description}"
            )
            
            # 创建Web步骤实例
            web_steps = create_web_steps(web_context)
            
            # 设置测试数据
            web_context.test_data.update({
                "username": test_user.username,
                "password": test_user.password,
                "user_type": test_user.user_type,
                "expected_result": test_user.expected_result
            })
            
            # 添加流程步骤
            flow.add_step(
                "navigate_login",
                web_steps.navigate_to_login,
                "导航到登录页面",
                "web"
            )
            
            flow.add_step(
                "perform_login",
                web_steps.perform_login,
                f"执行登录 - {test_user.description}",
                "web"
            )
            
            # 根据期望结果添加不同的验证步骤
            if test_user.expected_result == "success":
                flow.add_step(
                    "verify_login_success",
                    web_steps.verify_login_success,
                    "验证登录成功",
                    "web"
                )
            else:
                flow.add_step(
                    "verify_login_failure",
                    web_steps.verify_login_failure,
                    "验证登录失败",
                    "web"
                )
            
            # 执行流程
            flow_context = FlowContext()
            result = await flow.execute(flow_context)
            
            # 断言结果
            if test_user.expected_result == "success":
                assert result.success, f"Login should succeed for {test_user.description}"
            else:
                assert not result.success, f"Login should fail for {test_user.description}"
                
        except Exception as e:
            logger.error(f"Login test failed for {test_user.description}: {e}")
            raise
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("product", TEST_PRODUCTS, ids=[p.product_name for p in TEST_PRODUCTS])
    async def test_product_purchase(self, web_context, product: ProductInfo):
        """测试不同商品的购买流程
        
        Args:
            web_context: Web测试上下文
            product: 商品信息
        """
        logger.info(f"Testing purchase for product: {product.product_name}")
        
        try:
            # 创建流程执行器
            flow = create_flow(
                f"purchase_test_{product.product_id}",
                f"商品购买测试 - {product.product_name}"
            )
            
            # 创建Web步骤实例
            web_steps = create_web_steps(web_context)
            
            # 设置测试数据
            web_context.test_data.update({
                "product_id": product.product_id,
                "product_name": product.product_name,
                "category": product.category,
                "price": product.price,
                "stock": product.stock
            })
            
            # 添加流程步骤
            flow.add_step(
                "search_product",
                web_steps.search_product,
                f"搜索商品 - {product.product_name}",
                "web"
            )
            
            flow.add_step(
                "view_product_details",
                web_steps.view_product_details,
                "查看商品详情",
                "web"
            )
            
            flow.add_step(
                "add_to_cart",
                web_steps.add_to_cart,
                "添加到购物车",
                "web"
            )
            
            flow.add_step(
                "proceed_to_checkout",
                web_steps.proceed_to_checkout,
                "进入结算页面",
                "web"
            )
            
            flow.add_step(
                "complete_purchase",
                web_steps.complete_purchase,
                "完成购买",
                "web"
            )
            
            # 执行流程
            flow_context = FlowContext()
            result = await flow.execute(flow_context)
            
            # 断言结果
            assert result.success, f"Purchase should succeed for {product.product_name}"
            
        except Exception as e:
            logger.error(f"Purchase test failed for {product.product_name}: {e}")
            raise
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("user,product", [
        (TEST_USERS[0], TEST_PRODUCTS[0]),  # 普通用户购买手机
        (TEST_USERS[1], TEST_PRODUCTS[1]),  # VIP用户购买电脑
        (TEST_USERS[0], TEST_PRODUCTS[2]),  # 普通用户购买运动鞋
    ], ids=["normal_user_phone", "vip_user_laptop", "normal_user_shoes"])
    async def test_user_product_combination(self, web_context, user: TestUser, product: ProductInfo):
        """测试用户和商品的组合场景
        
        Args:
            web_context: Web测试上下文
            user: 测试用户
            product: 测试商品
        """
        logger.info(f"Testing combination: {user.description} buying {product.product_name}")
        
        try:
            # 创建流程执行器
            flow = create_flow(
                f"combo_test_{user.user_type}_{product.product_id}",
                f"组合测试 - {user.description} 购买 {product.product_name}"
            )
            
            # 创建Web步骤实例
            web_steps = create_web_steps(web_context)
            
            # 设置测试数据
            web_context.test_data.update({
                "username": user.username,
                "password": user.password,
                "user_type": user.user_type,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "price": product.price
            })
            
            # 完整的登录购买流程
            flow.add_step("navigate_login", web_steps.navigate_to_login, "导航到登录页面", "web")
            flow.add_step("perform_login", web_steps.perform_login, "执行登录", "web")
            flow.add_step("verify_login_success", web_steps.verify_login_success, "验证登录成功", "web")
            flow.add_step("search_product", web_steps.search_product, "搜索商品", "web")
            flow.add_step("add_to_cart", web_steps.add_to_cart, "添加到购物车", "web")
            flow.add_step("proceed_to_checkout", web_steps.proceed_to_checkout, "进入结算", "web")
            flow.add_step("complete_purchase", web_steps.complete_purchase, "完成购买", "web")
            
            # 执行流程
            flow_context = FlowContext()
            result = await flow.execute(flow_context)
            
            # 断言结果
            assert result.success, f"Combination test should succeed"
            
        except Exception as e:
            logger.error(f"Combination test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("env", TEST_ENVIRONMENTS, ids=[e.env_name for e in TEST_ENVIRONMENTS])
    async def test_cross_environment(self, web_context, env: TestEnvironment):
        """测试跨环境的功能验证
        
        Args:
            web_context: Web测试上下文
            env: 测试环境配置
        """
        logger.info(f"Testing on environment: {env.env_name}")
        
        try:
            # 更新环境配置
            web_context.test_data.update({
                "base_url": env.base_url,
                "api_url": env.api_url,
                "timeout": env.timeout,
                "environment": env.env_name
            })
            
            # 创建流程执行器
            flow = create_flow(
                f"env_test_{env.env_name}",
                f"环境测试 - {env.env_name}"
            )
            
            # 创建Web步骤实例
            web_steps = create_web_steps(web_context)
            
            # 基础功能验证
            flow.add_step("check_homepage", web_steps.check_homepage_availability, "检查首页可用性", "web")
            flow.add_step("check_login_page", web_steps.check_login_page, "检查登录页面", "web")
            flow.add_step("check_api_health", web_steps.check_api_health, "检查API健康状态", "web")
            
            # 执行流程
            flow_context = FlowContext()
            result = await flow.execute(flow_context)
            
            # 断言结果
            assert result.success, f"Environment test should succeed for {env.env_name}"
            
        except Exception as e:
            logger.error(f"Environment test failed for {env.env_name}: {e}")
            raise
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("browser_type", ["chromium", "firefox", "webkit"])
    async def test_cross_browser(self, web_context, browser_type: str):
        """测试跨浏览器兼容性
        
        Args:
            web_context: Web测试上下文
            browser_type: 浏览器类型
        """
        logger.info(f"Testing on browser: {browser_type}")
        
        # 注意：这里需要在fixture中支持动态浏览器切换
        # 或者使用不同的fixture配置
        
        try:
            # 设置浏览器类型
            web_context.test_data["browser_type"] = browser_type
            
            # 创建流程执行器
            flow = create_flow(
                f"browser_test_{browser_type}",
                f"浏览器兼容性测试 - {browser_type}"
            )
            
            # 创建Web步骤实例
            web_steps = create_web_steps(web_context)
            
            # 基础功能测试
            flow.add_step("navigate_homepage", web_steps.navigate_to_homepage, "导航首页", "web")
            flow.add_step("check_page_elements", web_steps.check_page_elements, "检查页面元素", "web")
            flow.add_step("perform_basic_interactions", web_steps.perform_basic_interactions, "基础交互测试", "web")
            
            # 执行流程
            flow_context = FlowContext()
            result = await flow.execute(flow_context)
            
            # 断言结果
            assert result.success, f"Browser test should succeed for {browser_type}"
            
        except Exception as e:
            logger.error(f"Browser test failed for {browser_type}: {e}")
            raise


# 数据驱动测试示例
class TestDataDrivenFlow:
    """数据驱动测试类"""
    
    @pytest.fixture(scope="class")
    def test_data_from_file(self):
        """从文件加载测试数据"""
        # 这里可以从CSV、JSON、Excel等文件加载数据
        return [
            {"username": "user1", "password": "pass1", "expected": "success"},
            {"username": "user2", "password": "pass2", "expected": "success"},
            {"username": "invalid", "password": "wrong", "expected": "failure"},
        ]
    
    @pytest.fixture(scope="class")
    def test_data_from_database(self):
        """从数据库加载测试数据"""
        # 这里可以从数据库查询测试数据
        # 示例：SELECT username, password, expected_result FROM test_users
        return []
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_case", [
        {"id": "TC001", "username": "user1", "password": "pass1", "expected": "success"},
        {"id": "TC002", "username": "user2", "password": "pass2", "expected": "success"},
        {"id": "TC003", "username": "invalid", "password": "wrong", "expected": "failure"},
    ], ids=lambda x: x["id"])
    async def test_data_driven_login(self, web_context, test_case: Dict[str, Any]):
        """数据驱动的登录测试
        
        Args:
            web_context: Web测试上下文
            test_case: 测试用例数据
        """
        logger.info(f"Executing test case: {test_case['id']}")
        
        try:
            # 设置测试数据
            web_context.test_data.update(test_case)
            
            # 创建和执行流程
            flow = create_flow(test_case["id"], f"数据驱动测试 - {test_case['id']}")
            web_steps = create_web_steps(web_context)
            
            flow.add_step("login", web_steps.perform_login, "执行登录", "web")
            
            flow_context = FlowContext()
            result = await flow.execute(flow_context)
            
            # 验证结果
            if test_case["expected"] == "success":
                assert result.success
            else:
                assert not result.success
                
        except Exception as e:
            logger.error(f"Data driven test failed for {test_case['id']}: {e}")
            raise


# pytest标记示例
pytestmark = [
    pytest.mark.parametrized,  # 自定义标记
    pytest.mark.smoke,         # 冒烟测试
    pytest.mark.regression,    # 回归测试
]


# ===== 高级参数化测试示例 =====

class TestAdvancedParameterization:
    """高级参数化测试示例"""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("browser_type,headless", [
        ("chromium", True),
        ("chromium", False),
        ("firefox", True),
        ("webkit", True),
    ], ids=["chrome-headless", "chrome-headed", "firefox-headless", "webkit-headless"])
    async def test_cross_browser_login(self, browser_type: str, headless: bool):
        """跨浏览器登录测试
        
        Args:
            browser_type: 浏览器类型
            headless: 是否无头模式
        """
        logger.info(f"Testing login on {browser_type} (headless={headless})")
        
        # 动态配置浏览器
        from configs.browser import get_browser_config
        config = get_browser_config("playwright", 
                                   BROWSER_TYPE=browser_type, 
                                   HEADLESS=headless)
        
        # 这里可以使用配置创建特定的测试上下文
        # 实际测试逻辑...
        
        assert True  # 占位符
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("environment,expected_performance", [
        ("development", {"max_load_time": 5.0, "max_response_time": 2.0}),
        ("testing", {"max_load_time": 3.0, "max_response_time": 1.5}),
        ("staging", {"max_load_time": 2.0, "max_response_time": 1.0}),
    ], ids=["dev-env", "test-env", "staging-env"])
    async def test_environment_performance(self, environment: str, expected_performance: Dict[str, float]):
        """不同环境的性能测试
        
        Args:
            environment: 测试环境
            expected_performance: 预期性能指标
        """
        logger.info(f"Testing performance in {environment} environment")
        
        # 模拟性能测试
        import time
        start_time = time.time()
        
        # 模拟页面加载
        await asyncio.sleep(0.1)
        
        load_time = time.time() - start_time
        
        # 验证性能指标
        assert load_time < expected_performance["max_load_time"]
        
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_data", [
        # 使用外部数据文件
        pytest.param(
            {"file": "test_data/user_data.json", "case": "valid_user"},
            id="json-valid-user"
        ),
        pytest.param(
            {"file": "test_data/user_data.csv", "case": "invalid_user"},
            id="csv-invalid-user"
        ),
    ])
    async def test_external_data_source(self, test_data: Dict[str, str]):
        """使用外部数据源的测试
        
        Args:
            test_data: 外部数据源配置
        """
        logger.info(f"Loading test data from {test_data['file']}")
        
        # 这里可以实现从外部文件加载数据的逻辑
        # import json, csv, pandas等
        
        assert True  # 占位符


# ===== 参数化测试最佳实践 =====

class TestParameterizationBestPractices:
    """参数化测试最佳实践示例"""
    
    # 1. 使用有意义的测试ID
    @pytest.mark.parametrize("username,password,expected", [
        ("admin", "admin123", True),
        ("user", "user123", True), 
        ("guest", "wrong", False),
    ], ids=["admin-login", "user-login", "guest-fail"])
    def test_with_meaningful_ids(self, username, password, expected):
        """使用有意义的测试ID"""
        # 测试逻辑
        result = username != "guest" or password != "wrong"
        assert result == expected
    
    # 2. 使用indirect参数化
    @pytest.fixture
    def user_session(self, request):
        """用户会话fixture"""
        user_type = request.param
        # 根据用户类型创建会话
        return f"session_for_{user_type}"
    
    @pytest.mark.parametrize("user_session", ["admin", "normal", "guest"], indirect=True)
    def test_with_indirect_parametrization(self, user_session):
        """使用indirect参数化"""
        assert "session_for_" in user_session
    
    # 3. 条件跳过参数化测试
    @pytest.mark.parametrize("browser", [
        "chromium",
        pytest.param("firefox", marks=pytest.mark.skipif(
            False,  # 简化条件，避免版本检查问题
            reason="Firefox support"
        )),
        pytest.param("webkit", marks=pytest.mark.xfail(
            reason="WebKit support is experimental"
        )),
    ])
    def test_conditional_skip(self, browser):
        """条件跳过测试"""
        assert browser in ["chromium", "firefox", "webkit"]
    
    # 4. 嵌套参数化
    @pytest.mark.parametrize("env", ["dev", "test", "prod"])
    @pytest.mark.parametrize("browser", ["chrome", "firefox"])
    @pytest.mark.parametrize("device", ["desktop", "mobile"])
    def test_nested_parametrization(self, env, browser, device):
        """嵌套参数化测试 - 会生成3x2x2=12个测试用例"""
        test_config = {
            "environment": env,
            "browser": browser, 
            "device": device
        }
        logger.info(f"Testing with config: {test_config}")
        assert all([env, browser, device])


# ===== 数据驱动测试工具类 =====

class DataDrivenTestUtils:
    """数据驱动测试工具类"""
    
    @staticmethod
    def load_test_data_from_json(file_path: str) -> List[Dict[str, Any]]:
        """从JSON文件加载测试数据"""
        import json
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Test data file not found: {file_path}")
            return []
    
    @staticmethod
    def load_test_data_from_csv(file_path: str) -> List[Dict[str, Any]]:
        """从CSV文件加载测试数据"""
        import csv
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except FileNotFoundError:
            logger.warning(f"Test data file not found: {file_path}")
            return []
    
    @staticmethod
    def load_test_data_from_excel(file_path: str, sheet_name: str = None) -> List[Dict[str, Any]]:
        """从Excel文件加载测试数据"""
        try:
            import pandas as pd
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            return df.to_dict('records')
        except ImportError:
            logger.error("pandas is required for Excel support")
            return []
        except FileNotFoundError:
            logger.warning(f"Test data file not found: {file_path}")
            return []


# ===== 使用示例 =====

def pytest_generate_tests(metafunc):
    """动态生成测试参数"""
    if "dynamic_user_data" in metafunc.fixturenames:
        # 动态加载测试数据
        test_data = [
            {"username": "dynamic_user1", "password": "pass1"},
            {"username": "dynamic_user2", "password": "pass2"},
        ]
        metafunc.parametrize("dynamic_user_data", test_data)
