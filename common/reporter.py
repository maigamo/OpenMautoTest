"""
OpenMautoTest 报告生成基础模块

提供测试报告生成的基础功能，支持多种格式的报告输出
集成Allure报告功能和增强截图支持
"""

import json
import time
import base64
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jinja2
try:
    import allure
    from allure_commons.types import AttachmentType
    ALLURE_AVAILABLE = True
except ImportError:
    ALLURE_AVAILABLE = False

from common.logger import get_logger
from common.utils.file_utils import ensure_dir, write_json_file, write_text_file
from common.utils.string_utils import format_duration
from common.utils.time_utils import format_timestamp
from configs.settings import get_settings


class TestResult:
    """测试结果类"""
    
    def __init__(
        self,
        test_name: str,
        status: str = "pending",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration: Optional[float] = None,
        error_message: Optional[str] = None,
        screenshots: Optional[List[str]] = None,
        logs: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.test_name = test_name
        self.status = status  # pending, running, passed, failed, skipped
        self.start_time = start_time or datetime.now()
        self.end_time = end_time
        self.duration = duration
        self.error_message = error_message
        self.screenshots = screenshots or []
        self.logs = logs or []
        self.metadata = metadata or {}
    
    def start(self) -> None:
        """开始测试"""
        self.status = "running"
        self.start_time = datetime.now()
    
    def finish(self, status: str, error_message: Optional[str] = None) -> None:
        """完成测试
        
        Args:
            status: 测试状态
            error_message: 错误消息
        """
        self.status = status
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.error_message = error_message
    
    def add_screenshot(self, screenshot_path: str) -> None:
        """添加截图
        
        Args:
            screenshot_path: 截图路径
        """
        self.screenshots.append(screenshot_path)
    
    def add_log(self, log_message: str) -> None:
        """添加日志
        
        Args:
            log_message: 日志消息
        """
        timestamp = format_timestamp(datetime.now(), "%H:%M:%S.%f")[:-3]
        self.logs.append(f"[{timestamp}] {log_message}")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据
        
        Args:
            key: 键
            value: 值
        """
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            测试结果字典
        """
        return {
            "test_name": self.test_name,
            "status": self.status,
            "start_time": format_timestamp(self.start_time) if self.start_time else None,
            "end_time": format_timestamp(self.end_time) if self.end_time else None,
            "duration": self.duration,
            "error_message": self.error_message,
            "screenshots": self.screenshots,
            "logs": self.logs,
            "metadata": self.metadata
        }


class TestSuite:
    """测试套件类"""
    
    def __init__(
        self,
        suite_name: str,
        description: str = "",
        environment: str = "",
        browser: str = "",
        platform: str = ""
    ):
        self.suite_name = suite_name
        self.description = description
        self.environment = environment
        self.browser = browser
        self.platform = platform
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.duration: Optional[float] = None
        self.results: List[TestResult] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_result(self, result: TestResult) -> None:
        """添加测试结果
        
        Args:
            result: 测试结果
        """
        self.results.append(result)
    
    def finish(self) -> None:
        """完成测试套件"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
    
    def get_summary(self) -> Dict[str, Any]:
        """获取汇总信息
        
        Returns:
            汇总信息字典
        """
        total = len(self.results)
        passed = len([r for r in self.results if r.status == "passed"])
        failed = len([r for r in self.results if r.status == "failed"])
        skipped = len([r for r in self.results if r.status == "skipped"])
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": round(pass_rate, 2),
            "duration": self.duration or 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            测试套件字典
        """
        return {
            "suite_name": self.suite_name,
            "description": self.description,
            "environment": self.environment,
            "browser": self.browser,
            "platform": self.platform,
            "start_time": format_timestamp(self.start_time),
            "end_time": format_timestamp(self.end_time) if self.end_time else None,
            "duration": self.duration,
            "summary": self.get_summary(),
            "results": [result.to_dict() for result in self.results],
            "metadata": self.metadata
        }


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("reporter")
        self.template_env = self._setup_template_env()
    
    def _setup_template_env(self) -> jinja2.Environment:
        """设置模板环境
        
        Returns:
            Jinja2环境对象
        """
        template_dir = Path(__file__).parent / "templates"
        
        # 如果模板目录不存在，创建内置模板
        if not template_dir.exists():
            self._create_builtin_templates(template_dir)
        
        loader = jinja2.FileSystemLoader(str(template_dir))
        env = jinja2.Environment(
            loader=loader,
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # 添加自定义过滤器
        env.filters['format_duration'] = format_duration
        env.filters['format_timestamp'] = format_timestamp
        
        return env
    
    def _create_builtin_templates(self, template_dir: Path) -> None:
        """创建内置模板
        
        Args:
            template_dir: 模板目录
        """
        ensure_dir(template_dir)
        
        # HTML报告模板
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ suite.suite_name }} - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .summary-item { background: #fff; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .skipped { color: #ffc107; }
        .test-result { margin: 10px 0; padding: 15px; border-left: 4px solid #ccc; }
        .test-result.passed { border-left-color: #28a745; }
        .test-result.failed { border-left-color: #dc3545; }
        .test-result.skipped { border-left-color: #ffc107; }
        .error-message { background: #f8d7da; padding: 10px; border-radius: 3px; margin: 10px 0; }
        .screenshots img { max-width: 200px; margin: 5px; border: 1px solid #ddd; }
        .logs { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ suite.suite_name }} - Test Report</h1>
        <p><strong>Environment:</strong> {{ suite.environment }}</p>
        <p><strong>Browser:</strong> {{ suite.browser }}</p>
        <p><strong>Start Time:</strong> {{ suite.start_time }}</p>
        <p><strong>Duration:</strong> {{ suite.duration | format_duration }}</p>
    </div>
    
    <div class="summary">
        <div class="summary-item">
            <h3>Total Tests</h3>
            <p>{{ suite.summary.total }}</p>
        </div>
        <div class="summary-item passed">
            <h3>Passed</h3>
            <p>{{ suite.summary.passed }}</p>
        </div>
        <div class="summary-item failed">
            <h3>Failed</h3>
            <p>{{ suite.summary.failed }}</p>
        </div>
        <div class="summary-item skipped">
            <h3>Skipped</h3>
            <p>{{ suite.summary.skipped }}</p>
        </div>
        <div class="summary-item">
            <h3>Pass Rate</h3>
            <p>{{ suite.summary.pass_rate }}%</p>
        </div>
    </div>
    
    <h2>Test Results</h2>
    {% for result in suite.results %}
    <div class="test-result {{ result.status }}">
        <h3>{{ result.test_name }}</h3>
        <p><strong>Status:</strong> <span class="{{ result.status }}">{{ result.status.upper() }}</span></p>
        <p><strong>Duration:</strong> {{ result.duration | format_duration }}</p>
        
        {% if result.error_message %}
        <div class="error-message">
            <strong>Error:</strong> {{ result.error_message }}
        </div>
        {% endif %}
        
        {% if result.screenshots %}
        <div class="screenshots">
            <strong>Screenshots:</strong>
            {% for screenshot in result.screenshots %}
            <img src="{{ screenshot }}" alt="Screenshot">
            {% endfor %}
        </div>
        {% endif %}
        
        {% if result.logs %}
        <div class="logs">
            <strong>Logs:</strong>
            <pre>{{ result.logs | join('\\n') }}</pre>
        </div>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
        """
        
        write_text_file(template_dir / "report.html", html_template.strip())
        
        # JSON报告模板（实际上是Python代码）
        json_template = """{{ suite | tojson(indent=2) }}"""
        write_text_file(template_dir / "report.json", json_template.strip())
    
    def generate_html_report(
        self,
        suite: TestSuite,
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """生成HTML报告
        
        Args:
            suite: 测试套件
            output_path: 输出路径
        
        Returns:
            报告文件路径
        """
        if output_path is None:
            output_dir = self.settings.get_output_dir() / "reports"
            ensure_dir(output_dir)
            timestamp = int(time.time())
            output_path = output_dir / f"report_{timestamp}.html"
        
        template = self.template_env.get_template("report.html")
        html_content = template.render(suite=suite.to_dict())
        
        write_text_file(output_path, html_content)
        self.logger.info(f"HTML report generated: {output_path}")
        
        return Path(output_path)
    
    def generate_json_report(
        self,
        suite: TestSuite,
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """生成JSON报告
        
        Args:
            suite: 测试套件
            output_path: 输出路径
        
        Returns:
            报告文件路径
        """
        if output_path is None:
            output_dir = self.settings.get_output_dir() / "reports"
            ensure_dir(output_dir)
            timestamp = int(time.time())
            output_path = output_dir / f"report_{timestamp}.json"
        
        write_json_file(output_path, suite.to_dict())
        self.logger.info(f"JSON report generated: {output_path}")
        
        return Path(output_path)
    
    def generate_junit_xml(
        self,
        suite: TestSuite,
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """生成JUnit XML报告
        
        Args:
            suite: 测试套件
            output_path: 输出路径
        
        Returns:
            报告文件路径
        """
        if output_path is None:
            output_dir = self.settings.get_output_dir() / "reports"
            ensure_dir(output_dir)
            timestamp = int(time.time())
            output_path = output_dir / f"junit_{timestamp}.xml"
        
        # 生成JUnit XML格式
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        
        summary = suite.get_summary()
        xml_lines.append(
            f'<testsuite name="{suite.suite_name}" '
            f'tests="{summary["total"]}" '
            f'failures="{summary["failed"]}" '
            f'skipped="{summary["skipped"]}" '
            f'time="{suite.duration or 0:.3f}">'
        )
        
        for result in suite.results:
            xml_lines.append(f'  <testcase name="{result.test_name}" time="{result.duration or 0:.3f}">')
            
            if result.status == "failed":
                xml_lines.append('    <failure message="Test failed">')
                if result.error_message:
                    xml_lines.append(f'      {result.error_message}')
                xml_lines.append('    </failure>')
            elif result.status == "skipped":
                xml_lines.append('    <skipped/>')
            
            xml_lines.append('  </testcase>')
        
        xml_lines.append('</testsuite>')
        
        xml_content = '\n'.join(xml_lines)
        write_text_file(output_path, xml_content)
        self.logger.info(f"JUnit XML report generated: {output_path}")
        
        return Path(output_path)
    
    def generate_all_reports(
        self,
        suite: TestSuite,
        output_dir: Optional[Union[str, Path]] = None
    ) -> Dict[str, Path]:
        """生成所有格式的报告
        
        Args:
            suite: 测试套件
            output_dir: 输出目录
        
        Returns:
            报告文件路径字典
        """
        if output_dir is None:
            output_dir = self.settings.get_output_dir() / "reports"
        
        ensure_dir(output_dir)
        timestamp = int(time.time())
        
        reports = {}
        
        # HTML报告
        html_path = output_dir / f"report_{timestamp}.html"
        reports["html"] = self.generate_html_report(suite, html_path)
        
        # JSON报告
        json_path = output_dir / f"report_{timestamp}.json"
        reports["json"] = self.generate_json_report(suite, json_path)
        
        # JUnit XML报告
        junit_path = output_dir / f"junit_{timestamp}.xml"
        reports["junit"] = self.generate_junit_xml(suite, junit_path)
        
        self.logger.info(f"All reports generated in: {output_dir}")
        return reports


class ReportCollector:
    """报告收集器"""
    
    def __init__(self):
        self.current_suite: Optional[TestSuite] = None
        self.current_result: Optional[TestResult] = None
        self.logger = get_logger("report_collector")
    
    def start_suite(
        self,
        suite_name: str,
        description: str = "",
        environment: str = "",
        browser: str = "",
        platform: str = ""
    ) -> TestSuite:
        """开始测试套件
        
        Args:
            suite_name: 套件名称
            description: 描述
            environment: 环境
            browser: 浏览器
            platform: 平台
        
        Returns:
            测试套件对象
        """
        self.current_suite = TestSuite(
            suite_name, description, environment, browser, platform
        )
        self.logger.info(f"Started test suite: {suite_name}")
        return self.current_suite
    
    def start_test(self, test_name: str) -> TestResult:
        """开始测试
        
        Args:
            test_name: 测试名称
        
        Returns:
            测试结果对象
        """
        self.current_result = TestResult(test_name)
        self.current_result.start()
        self.logger.info(f"Started test: {test_name}")
        return self.current_result
    
    def finish_test(
        self,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[TestResult]:
        """完成测试
        
        Args:
            status: 测试状态
            error_message: 错误消息
        
        Returns:
            测试结果对象
        """
        if self.current_result is None:
            self.logger.warning("No current test to finish")
            return None
        
        self.current_result.finish(status, error_message)
        
        if self.current_suite:
            self.current_suite.add_result(self.current_result)
        
        self.logger.info(f"Finished test: {self.current_result.test_name} - {status}")
        
        result = self.current_result
        self.current_result = None
        return result
    
    def finish_suite(self) -> Optional[TestSuite]:
        """完成测试套件
        
        Returns:
            测试套件对象
        """
        if self.current_suite is None:
            self.logger.warning("No current suite to finish")
            return None
        
        self.current_suite.finish()
        self.logger.info(f"Finished test suite: {self.current_suite.suite_name}")
        
        suite = self.current_suite
        self.current_suite = None
        return suite
    
    def add_screenshot(self, screenshot_path: str) -> None:
        """添加截图
        
        Args:
            screenshot_path: 截图路径
        """
        if self.current_result:
            self.current_result.add_screenshot(screenshot_path)
    
    def add_log(self, log_message: str) -> None:
        """添加日志
        
        Args:
            log_message: 日志消息
        """
        if self.current_result:
            self.current_result.add_log(log_message)


# 全局报告收集器实例
report_collector = ReportCollector()


def get_report_collector() -> ReportCollector:
    """获取全局报告收集器实例
    
    Returns:
        报告收集器实例
    """
    return report_collector


if __name__ == "__main__":
    # 测试报告生成功能
    print("Testing report generation...")
    
    # 创建测试套件
    suite = TestSuite(
        "Sample Test Suite",
        "This is a sample test suite",
        "development",
        "chromium",
        "Windows"
    )
    
    # 添加测试结果
    result1 = TestResult("test_login", "passed")
    result1.start()
    result1.finish("passed")
    result1.add_log("User logged in successfully")
    
    result2 = TestResult("test_logout", "failed", error_message="Logout button not found")
    result2.start()
    result2.finish("failed", "Logout button not found")
    result2.add_log("Clicked logout button")
    result2.add_log("Error: Element not found")
    
    suite.add_result(result1)
    suite.add_result(result2)
    suite.finish()
    
    # 生成报告
    generator = ReportGenerator()
    reports = generator.generate_all_reports(suite)
    
    print(f"Generated reports: {list(reports.keys())}")
    print("Report generation tests completed.")


class AllureReporter:
    """Allure报告集成器"""
    
    def __init__(self):
        """初始化Allure报告器"""
        self.logger = get_logger("allure_reporter")
        self.available = ALLURE_AVAILABLE
        
        if not self.available:
            self.logger.warning("Allure not available, some reporting features will be disabled")
    
    def attach_screenshot(self, screenshot_path: Union[str, Path], name: str = "Screenshot") -> None:
        """附加截图到Allure报告"""
        if not self.available:
            return
        
        try:
            screenshot_path = Path(screenshot_path)
            if screenshot_path.exists():
                with open(screenshot_path, "rb") as f:
                    allure.attach(
                        f.read(),
                        name=name,
                        attachment_type=AttachmentType.PNG
                    )
                self.logger.debug(f"Attached screenshot to Allure: {name}")
        except Exception as e:
            self.logger.error(f"Failed to attach screenshot to Allure: {e}")
    
    def attach_text(self, content: str, name: str = "Text", attachment_type: str = "TEXT") -> None:
        """附加文本到Allure报告"""
        if not self.available:
            return
        
        try:
            allure_type = getattr(AttachmentType, attachment_type, AttachmentType.TEXT)
            allure.attach(content, name=name, attachment_type=allure_type)
            self.logger.debug(f"Attached text to Allure: {name}")
        except Exception as e:
            self.logger.error(f"Failed to attach text to Allure: {e}")
    
    def attach_json(self, data: Dict[str, Any], name: str = "JSON Data") -> None:
        """附加JSON数据到Allure报告"""
        if not self.available:
            return
        
        try:
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            allure.attach(json_content, name=name, attachment_type=AttachmentType.JSON)
            self.logger.debug(f"Attached JSON to Allure: {name}")
        except Exception as e:
            self.logger.error(f"Failed to attach JSON to Allure: {e}")
    
    def step(self, name: str):
        """创建Allure测试步骤"""
        if not self.available:
            return _DummyStep(name)
        return allure.step(name)


class _DummyStep:
    """虚拟步骤类（当Allure不可用时使用）"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger("dummy_step")
    
    def __enter__(self):
        self.logger.info(f"Step: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"Step failed: {self.name} - {exc_val}")
        else:
            self.logger.info(f"Step completed: {self.name}")


class ScreenshotManager:
    """截图管理器"""
    
    def __init__(self, output_dir: Union[str, Path] = "output/screenshots"):
        """初始化截图管理器"""
        self.output_dir = Path(output_dir)
        self.logger = get_logger("screenshot_manager")
        self.allure_reporter = AllureReporter()
        
        # 确保输出目录存在
        ensure_dir(self.output_dir)
        self.screenshot_counter = 0
    
    def save_screenshot(
        self,
        screenshot_data: bytes,
        name: str = None,
        attach_to_allure: bool = True,
        timestamp: bool = True
    ) -> Path:
        """保存截图"""
        try:
            self.screenshot_counter += 1
            
            if name is None:
                name = f"screenshot_{self.screenshot_counter}"
            
            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                name = f"{name}_{timestamp_str}"
            
            screenshot_path = self.output_dir / f"{name}.png"
            
            # 保存截图文件
            with open(screenshot_path, "wb") as f:
                f.write(screenshot_data)
            
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            
            # 附加到Allure报告
            if attach_to_allure:
                self.allure_reporter.attach_screenshot(screenshot_path, name)
            
            return screenshot_path
        
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")
            raise


# 全局实例
_global_allure_reporter: Optional[AllureReporter] = None
_global_screenshot_manager: Optional[ScreenshotManager] = None


def get_allure_reporter() -> AllureReporter:
    """获取全局Allure报告器实例"""
    global _global_allure_reporter
    if _global_allure_reporter is None:
        _global_allure_reporter = AllureReporter()
    return _global_allure_reporter


def get_screenshot_manager() -> ScreenshotManager:
    """获取全局截图管理器实例"""
    global _global_screenshot_manager
    if _global_screenshot_manager is None:
        _global_screenshot_manager = ScreenshotManager()
    return _global_screenshot_manager
