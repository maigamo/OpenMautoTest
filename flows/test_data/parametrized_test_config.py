"""
参数化测试配置文件

定义各种测试场景的参数配置，支持从文件、数据库等多种数据源加载测试数据
"""

import json
import csv
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from common.logger import get_logger


logger = get_logger("parametrized_test_config")


@dataclass
class TestCase:
    """测试用例数据结构"""
    id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    expected_result: str
    tags: List[str]
    priority: str = "medium"
    timeout: int = 60
    retry_count: int = 0


class TestDataLoader:
    """测试数据加载器"""
    
    def __init__(self, data_dir: str = "flows/test_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_from_json(self, filename: str) -> List[TestCase]:
        """从JSON文件加载测试数据"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.warning(f"JSON file not found: {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            test_cases = []
            for item in data.get('test_cases', []):
                test_case = TestCase(**item)
                test_cases.append(test_case)
            
            logger.info(f"Loaded {len(test_cases)} test cases from {filename}")
            return test_cases
            
        except Exception as e:
            logger.error(f"Failed to load JSON file {filename}: {e}")
            return []
    
    def load_from_csv(self, filename: str) -> List[TestCase]:
        """从CSV文件加载测试数据"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return []
        
        try:
            test_cases = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 处理参数字段（假设是JSON字符串）
                    parameters = json.loads(row.get('parameters', '{}'))
                    tags = row.get('tags', '').split(',') if row.get('tags') else []
                    
                    test_case = TestCase(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        parameters=parameters,
                        expected_result=row['expected_result'],
                        tags=tags,
                        priority=row.get('priority', 'medium'),
                        timeout=int(row.get('timeout', 60)),
                        retry_count=int(row.get('retry_count', 0))
                    )
                    test_cases.append(test_case)
            
            logger.info(f"Loaded {len(test_cases)} test cases from {filename}")
            return test_cases
            
        except Exception as e:
            logger.error(f"Failed to load CSV file {filename}: {e}")
            return []
    
    def load_from_yaml(self, filename: str) -> List[TestCase]:
        """从YAML文件加载测试数据"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.warning(f"YAML file not found: {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            test_cases = []
            for item in data.get('test_cases', []):
                test_case = TestCase(**item)
                test_cases.append(test_case)
            
            logger.info(f"Loaded {len(test_cases)} test cases from {filename}")
            return test_cases
            
        except Exception as e:
            logger.error(f"Failed to load YAML file {filename}: {e}")
            return []
    
    def save_to_json(self, test_cases: List[TestCase], filename: str):
        """保存测试数据到JSON文件"""
        file_path = self.data_dir / filename
        
        try:
            data = {
                'test_cases': [asdict(tc) for tc in test_cases],
                'metadata': {
                    'total_count': len(test_cases),
                    'generated_at': str(Path(__file__).stat().st_mtime)
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(test_cases)} test cases to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save JSON file {filename}: {e}")


# 预定义的测试数据集
class TestDataSets:
    """预定义测试数据集"""
    
    # 登录测试数据
    LOGIN_TEST_CASES = [
        TestCase(
            id="LOGIN_001",
            name="valid_normal_user_login",
            description="普通用户有效登录",
            parameters={
                "username": "normal_user",
                "password": "password123",
                "user_type": "normal"
            },
            expected_result="success",
            tags=["login", "positive", "smoke"],
            priority="high"
        ),
        TestCase(
            id="LOGIN_002",
            name="valid_vip_user_login",
            description="VIP用户有效登录",
            parameters={
                "username": "vip_user",
                "password": "vippass456",
                "user_type": "vip"
            },
            expected_result="success",
            tags=["login", "positive", "vip"],
            priority="high"
        ),
        TestCase(
            id="LOGIN_003",
            name="invalid_password_login",
            description="无效密码登录",
            parameters={
                "username": "normal_user",
                "password": "wrong_password",
                "user_type": "normal"
            },
            expected_result="failure",
            tags=["login", "negative", "security"],
            priority="medium"
        ),
        TestCase(
            id="LOGIN_004",
            name="empty_username_login",
            description="空用户名登录",
            parameters={
                "username": "",
                "password": "password123",
                "user_type": "normal"
            },
            expected_result="failure",
            tags=["login", "negative", "validation"],
            priority="medium"
        ),
        TestCase(
            id="LOGIN_005",
            name="sql_injection_login",
            description="SQL注入登录测试",
            parameters={
                "username": "admin' OR '1'='1",
                "password": "anything",
                "user_type": "normal"
            },
            expected_result="failure",
            tags=["login", "negative", "security", "injection"],
            priority="high"
        )
    ]
    
    # 购买流程测试数据
    PURCHASE_TEST_CASES = [
        TestCase(
            id="PURCHASE_001",
            name="single_item_purchase",
            description="单商品购买",
            parameters={
                "product_id": "P001",
                "product_name": "智能手机",
                "quantity": 1,
                "payment_method": "credit_card"
            },
            expected_result="success",
            tags=["purchase", "positive", "smoke"],
            priority="high"
        ),
        TestCase(
            id="PURCHASE_002",
            name="multiple_items_purchase",
            description="多商品购买",
            parameters={
                "products": [
                    {"product_id": "P001", "quantity": 2},
                    {"product_id": "P002", "quantity": 1}
                ],
                "payment_method": "alipay"
            },
            expected_result="success",
            tags=["purchase", "positive", "multiple"],
            priority="medium"
        ),
        TestCase(
            id="PURCHASE_003",
            name="out_of_stock_purchase",
            description="缺货商品购买",
            parameters={
                "product_id": "P999",
                "product_name": "缺货商品",
                "quantity": 1,
                "payment_method": "wechat_pay"
            },
            expected_result="failure",
            tags=["purchase", "negative", "stock"],
            priority="medium"
        )
    ]
    
    # 跨浏览器测试数据
    BROWSER_TEST_CASES = [
        TestCase(
            id="BROWSER_001",
            name="chromium_compatibility",
            description="Chromium浏览器兼容性测试",
            parameters={
                "browser_type": "chromium",
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "custom_chromium_agent"
            },
            expected_result="success",
            tags=["browser", "compatibility", "chromium"],
            priority="high"
        ),
        TestCase(
            id="BROWSER_002",
            name="firefox_compatibility",
            description="Firefox浏览器兼容性测试",
            parameters={
                "browser_type": "firefox",
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "custom_firefox_agent"
            },
            expected_result="success",
            tags=["browser", "compatibility", "firefox"],
            priority="medium"
        ),
        TestCase(
            id="BROWSER_003",
            name="webkit_compatibility",
            description="WebKit浏览器兼容性测试",
            parameters={
                "browser_type": "webkit",
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "custom_webkit_agent"
            },
            expected_result="success",
            tags=["browser", "compatibility", "webkit"],
            priority="medium"
        )
    ]
    
    # 性能测试数据
    PERFORMANCE_TEST_CASES = [
        TestCase(
            id="PERF_001",
            name="page_load_performance",
            description="页面加载性能测试",
            parameters={
                "page_url": "/homepage",
                "max_load_time": 3000,  # 毫秒
                "concurrent_users": 1
            },
            expected_result="success",
            tags=["performance", "load_time"],
            priority="high",
            timeout=120
        ),
        TestCase(
            id="PERF_002",
            name="api_response_performance",
            description="API响应性能测试",
            parameters={
                "api_endpoint": "/api/products",
                "max_response_time": 1000,  # 毫秒
                "request_count": 100
            },
            expected_result="success",
            tags=["performance", "api"],
            priority="medium",
            timeout=300
        )
    ]


# 测试数据工厂
class TestDataFactory:
    """测试数据工厂"""
    
    def __init__(self):
        self.loader = TestDataLoader()
    
    def get_login_test_cases(self, tags: Optional[List[str]] = None) -> List[TestCase]:
        """获取登录测试用例"""
        test_cases = TestDataSets.LOGIN_TEST_CASES.copy()
        
        if tags:
            test_cases = [tc for tc in test_cases if any(tag in tc.tags for tag in tags)]
        
        return test_cases
    
    def get_purchase_test_cases(self, tags: Optional[List[str]] = None) -> List[TestCase]:
        """获取购买测试用例"""
        test_cases = TestDataSets.PURCHASE_TEST_CASES.copy()
        
        if tags:
            test_cases = [tc for tc in test_cases if any(tag in tc.tags for tag in tags)]
        
        return test_cases
    
    def get_browser_test_cases(self, tags: Optional[List[str]] = None) -> List[TestCase]:
        """获取浏览器测试用例"""
        test_cases = TestDataSets.BROWSER_TEST_CASES.copy()
        
        if tags:
            test_cases = [tc for tc in test_cases if any(tag in tc.tags for tag in tags)]
        
        return test_cases
    
    def get_performance_test_cases(self, tags: Optional[List[str]] = None) -> List[TestCase]:
        """获取性能测试用例"""
        test_cases = TestDataSets.PERFORMANCE_TEST_CASES.copy()
        
        if tags:
            test_cases = [tc for tc in test_cases if any(tag in tc.tags for tag in tags)]
        
        return test_cases
    
    def get_all_test_cases(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[TestCase]:
        """获取所有测试用例"""
        all_cases = []
        
        if not category or category == "login":
            all_cases.extend(self.get_login_test_cases(tags))
        
        if not category or category == "purchase":
            all_cases.extend(self.get_purchase_test_cases(tags))
        
        if not category or category == "browser":
            all_cases.extend(self.get_browser_test_cases(tags))
        
        if not category or category == "performance":
            all_cases.extend(self.get_performance_test_cases(tags))
        
        return all_cases
    
    def generate_sample_data_files(self):
        """生成示例数据文件"""
        # 生成JSON格式示例
        self.loader.save_to_json(TestDataSets.LOGIN_TEST_CASES, "login_test_cases.json")
        self.loader.save_to_json(TestDataSets.PURCHASE_TEST_CASES, "purchase_test_cases.json")
        
        # 生成CSV格式示例
        self._generate_csv_sample()
        
        # 生成YAML格式示例
        self._generate_yaml_sample()
    
    def _generate_csv_sample(self):
        """生成CSV格式示例文件"""
        import csv
        
        csv_file = self.loader.data_dir / "sample_test_cases.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'name', 'description', 'parameters', 'expected_result', 'tags', 'priority', 'timeout', 'retry_count']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for tc in TestDataSets.LOGIN_TEST_CASES[:3]:  # 只写入前3个作为示例
                row = asdict(tc)
                row['parameters'] = json.dumps(row['parameters'])
                row['tags'] = ','.join(row['tags'])
                writer.writerow(row)
    
    def _generate_yaml_sample(self):
        """生成YAML格式示例文件"""
        import yaml
        
        yaml_file = self.loader.data_dir / "sample_test_cases.yaml"
        
        data = {
            'test_cases': [asdict(tc) for tc in TestDataSets.LOGIN_TEST_CASES[:3]]
        }
        
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


# 全局实例
test_data_factory = TestDataFactory()


# 便捷函数
def get_test_cases_for_pytest(category: str = None, tags: List[str] = None) -> List[tuple]:
    """获取适用于pytest参数化的测试用例数据
    
    Args:
        category: 测试类别
        tags: 标签过滤
    
    Returns:
        适用于pytest.mark.parametrize的元组列表
    """
    test_cases = test_data_factory.get_all_test_cases(category, tags)
    return [(tc.id, tc.parameters, tc.expected_result) for tc in test_cases]


def get_test_case_ids(category: str = None, tags: List[str] = None) -> List[str]:
    """获取测试用例ID列表，用于pytest的ids参数
    
    Args:
        category: 测试类别
        tags: 标签过滤
    
    Returns:
        测试用例ID列表
    """
    test_cases = test_data_factory.get_all_test_cases(category, tags)
    return [tc.id for tc in test_cases]


if __name__ == "__main__":
    # 生成示例数据文件
    factory = TestDataFactory()
    factory.generate_sample_data_files()
    print("Sample data files generated successfully!")
