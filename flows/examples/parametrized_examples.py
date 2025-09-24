"""
参数化测试使用示例

展示如何在OpenMautoTest中实现各种参数化测试场景
"""

import pytest
from typing import Dict, Any, List, Tuple

from flows.test_data.parametrized_test_config import (
    test_data_factory,
    get_test_cases_for_pytest,
    get_test_case_ids,
    TestCase
)
from orchestrator.fixtures.web_context import web_context
from flows.login_and_buy.web_steps import create_web_steps
from orchestrator.flow_runner import create_flow, FlowContext
from common.logger import get_logger


logger = get_logger("parametrized_examples")


class TestParametrizedExamples:
    """参数化测试示例类"""
    
    # 示例1: 简单的参数化测试
    @pytest.mark.asyncio
    @pytest.mark.parametrize("username,password,expected", [
        ("user1", "pass1", "success"),
        ("user2", "pass2", "success"),
        ("invalid", "wrong", "failure"),
    ])
    async def test_simple_parametrize(self, web_context, username, password, expected):
        """简单参数化测试示例"""
        logger.info(f"Testing login: {username}")
        
        # 设置测试数据
        web_context.test_data.update({
            "username": username,
            "password": password
        })
        
        # 执行测试逻辑
        web_steps = create_web_steps(web_context)
        
        # 这里添加实际的测试步骤
        # result = await web_steps.perform_login()
        # assert (result.success) == (expected == "success")
    
    # 示例2: 使用数据工厂的参数化测试
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_id,parameters,expected",
        get_test_cases_for_pytest(category="login", tags=["positive"]),
        ids=get_test_case_ids(category="login", tags=["positive"])
    )
    async def test_login_with_data_factory(self, web_context, test_id, parameters, expected):
        """使用数据工厂的登录测试"""
        logger.info(f"Executing test case: {test_id}")
        
        # 设置测试数据
        web_context.test_data.update(parameters)
        
        # 创建流程
        flow = create_flow(test_id, f"Login test - {test_id}")
        web_steps = create_web_steps(web_context)
        
        # 添加测试步骤
        flow.add_step("login", web_steps.perform_login, "执行登录", "web")
        
        # 执行流程
        flow_context = FlowContext()
        result = await flow.execute(flow_context)
        
        # 验证结果
        assert (result.success) == (expected == "success")
    
    # 示例3: 复合参数化测试
    @pytest.mark.asyncio
    @pytest.mark.parametrize("browser_type", ["chromium", "firefox"])
    @pytest.mark.parametrize("user_type", ["normal", "vip"])
    async def test_cross_browser_user_types(self, web_context, browser_type, user_type):
        """跨浏览器和用户类型的组合测试"""
        logger.info(f"Testing {user_type} user on {browser_type}")
        
        # 设置测试数据
        web_context.test_data.update({
            "browser_type": browser_type,
            "user_type": user_type
        })
        
        # 执行测试逻辑
        # ... 实际测试代码 ...
    
    # 示例4: 使用fixture参数化
    @pytest.fixture(params=["dev", "test", "staging"])
    def environment(self, request):
        """环境参数化fixture"""
        return request.param
    
    @pytest.mark.asyncio
    async def test_cross_environment(self, web_context, environment):
        """跨环境测试"""
        logger.info(f"Testing on environment: {environment}")
        
        # 根据环境设置不同的配置
        env_configs = {
            "dev": {"base_url": "http://dev.example.com", "timeout": 30},
            "test": {"base_url": "http://test.example.com", "timeout": 45},
            "staging": {"base_url": "http://staging.example.com", "timeout": 60}
        }
        
        web_context.test_data.update(env_configs[environment])
        
        # 执行环境特定的测试
        # ... 实际测试代码 ...
    
    # 示例5: 动态参数化
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        test_data_factory.get_login_test_cases(tags=["smoke"]),
        ids=lambda tc: tc.id
    )
    async def test_dynamic_parametrize(self, web_context, test_case: TestCase):
        """动态参数化测试"""
        logger.info(f"Executing dynamic test: {test_case.id}")
        
        # 设置测试数据
        web_context.test_data.update(test_case.parameters)
        
        # 根据测试用例配置设置超时
        web_context.test_data["timeout"] = test_case.timeout
        
        # 执行测试
        # ... 实际测试代码 ...
    
    # 示例6: 条件参数化
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        [tc for tc in test_data_factory.get_all_test_cases() if tc.priority == "high"],
        ids=lambda tc: f"{tc.id}_high_priority"
    )
    async def test_high_priority_only(self, web_context, test_case: TestCase):
        """只执行高优先级测试用例"""
        logger.info(f"Executing high priority test: {test_case.id}")
        
        # 执行高优先级测试
        # ... 实际测试代码 ...
    
    # 示例7: 嵌套参数化
    @pytest.mark.asyncio
    @pytest.mark.parametrize("device_type", ["desktop", "mobile"])
    @pytest.mark.parametrize(
        "login_data",
        [
            {"username": "user1", "password": "pass1"},
            {"username": "user2", "password": "pass2"}
        ]
    )
    async def test_nested_parametrize(self, web_context, device_type, login_data):
        """嵌套参数化测试"""
        logger.info(f"Testing {login_data['username']} on {device_type}")
        
        # 设置设备类型相关配置
        device_configs = {
            "desktop": {"viewport": {"width": 1920, "height": 1080}},
            "mobile": {"viewport": {"width": 375, "height": 667}}
        }
        
        web_context.test_data.update(login_data)
        web_context.test_data.update(device_configs[device_type])
        
        # 执行测试
        # ... 实际测试代码 ...


class TestDataDrivenExamples:
    """数据驱动测试示例"""
    
    # 示例8: 从外部文件加载数据
    @pytest.fixture(scope="class")
    def external_test_data(self):
        """从外部文件加载测试数据"""
        loader = test_data_factory.loader
        
        # 尝试从JSON文件加载
        json_cases = loader.load_from_json("login_test_cases.json")
        if json_cases:
            return json_cases
        
        # 如果JSON文件不存在，使用默认数据
        return test_data_factory.get_login_test_cases()
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        lambda: test_data_factory.loader.load_from_json("login_test_cases.json") or 
                test_data_factory.get_login_test_cases()[:3],  # 回退到前3个默认用例
        ids=lambda tc: tc.id
    )
    async def test_external_data_driven(self, web_context, test_case: TestCase):
        """外部数据驱动测试"""
        logger.info(f"Executing external data test: {test_case.id}")
        
        # 设置测试数据
        web_context.test_data.update(test_case.parameters)
        
        # 执行测试
        # ... 实际测试代码 ...


class TestAdvancedParametrization:
    """高级参数化测试示例"""
    
    # 示例9: 参数化与标记结合
    @pytest.mark.asyncio
    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "test_case",
        [tc for tc in test_data_factory.get_all_test_cases() if "smoke" in tc.tags],
        ids=lambda tc: tc.id
    )
    async def test_smoke_parametrized(self, web_context, test_case: TestCase):
        """冒烟测试参数化"""
        logger.info(f"Executing smoke test: {test_case.id}")
        
        # 执行冒烟测试
        # ... 实际测试代码 ...
    
    # 示例10: 参数化与跳过条件结合
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        test_data_factory.get_browser_test_cases(),
        ids=lambda tc: tc.id
    )
    async def test_browser_with_skip(self, web_context, test_case: TestCase):
        """带跳过条件的浏览器测试"""
        browser_type = test_case.parameters.get("browser_type")
        
        # 条件跳过
        if browser_type == "webkit":
            pytest.skip("WebKit tests are temporarily disabled")
        
        logger.info(f"Testing browser: {browser_type}")
        
        # 执行浏览器测试
        # ... 实际测试代码 ...
    
    # 示例11: 参数化与重试结合
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        [tc for tc in test_data_factory.get_all_test_cases() if tc.retry_count > 0],
        ids=lambda tc: f"{tc.id}_retry_{tc.retry_count}"
    )
    @pytest.mark.flaky(reruns=3)  # 需要安装pytest-rerunfailures
    async def test_with_retry(self, web_context, test_case: TestCase):
        """带重试的参数化测试"""
        logger.info(f"Executing test with retry: {test_case.id}")
        
        # 设置重试相关配置
        web_context.test_data.update(test_case.parameters)
        web_context.test_data["retry_count"] = test_case.retry_count
        
        # 执行可能需要重试的测试
        # ... 实际测试代码 ...


# 自定义pytest收集钩子，用于动态生成测试用例
def pytest_generate_tests(metafunc):
    """动态生成测试用例"""
    
    # 为标记了dynamic_data的测试函数动态生成参数
    if "dynamic_data" in metafunc.fixturenames:
        # 根据测试函数名决定使用哪些数据
        if "login" in metafunc.function.__name__:
            test_cases = test_data_factory.get_login_test_cases()
        elif "purchase" in metafunc.function.__name__:
            test_cases = test_data_factory.get_purchase_test_cases()
        else:
            test_cases = test_data_factory.get_all_test_cases()
        
        # 设置参数化
        metafunc.parametrize(
            "dynamic_data",
            test_cases,
            ids=[tc.id for tc in test_cases]
        )


class TestDynamicGeneration:
    """动态生成测试示例"""
    
    @pytest.mark.asyncio
    async def test_dynamic_login_cases(self, web_context, dynamic_data: TestCase):
        """动态生成的登录测试用例"""
        logger.info(f"Dynamic login test: {dynamic_data.id}")
        
        # 使用动态数据执行测试
        web_context.test_data.update(dynamic_data.parameters)
        
        # 执行测试
        # ... 实际测试代码 ...
    
    @pytest.mark.asyncio
    async def test_dynamic_purchase_cases(self, web_context, dynamic_data: TestCase):
        """动态生成的购买测试用例"""
        logger.info(f"Dynamic purchase test: {dynamic_data.id}")
        
        # 使用动态数据执行测试
        web_context.test_data.update(dynamic_data.parameters)
        
        # 执行测试
        # ... 实际测试代码 ...


# 运行示例
if __name__ == "__main__":
    # 生成示例数据文件
    test_data_factory.generate_sample_data_files()
    
    # 显示可用的测试用例
    print("Available test cases:")
    for category in ["login", "purchase", "browser", "performance"]:
        cases = test_data_factory.get_all_test_cases(category=category)
        print(f"\n{category.upper()} ({len(cases)} cases):")
        for case in cases:
            print(f"  - {case.id}: {case.description}")
    
    print("\nSample data files generated in flows/test_data/")
    print("Run tests with: pytest flows/examples/parametrized_examples.py -v")
