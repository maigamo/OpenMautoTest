"""
OpenMautoTest 流程执行引擎

支持跨端流程编排和步骤间数据传递
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, Awaitable

from common.logger import get_logger
from common.utils.time_utils import Timer
from configs.settings import get_settings
from orchestrator.recorder import get_recorder


class FlowExecutionError(Exception):
    """流程执行异常"""
    pass


class FlowStep:
    """流程步骤"""
    
    def __init__(
        self,
        name: str,
        func: Callable,
        description: str = "",
        platform: str = "unknown",
        timeout: Optional[int] = None,
        retry_count: int = 0,
        continue_on_failure: bool = False,
        depends_on: Optional[List[str]] = None
    ):
        """初始化流程步骤
        
        Args:
            name: 步骤名称
            func: 执行函数
            description: 步骤描述
            platform: 平台类型 (web/mini/api)
            timeout: 超时时间(秒)
            retry_count: 重试次数
            continue_on_failure: 失败时是否继续
            depends_on: 依赖的步骤名称列表
        """
        self.name = name
        self.func = func
        self.description = description
        self.platform = platform
        self.timeout = timeout or 300  # 默认5分钟
        self.retry_count = retry_count
        self.continue_on_failure = continue_on_failure
        self.depends_on = depends_on or []
        
        # 执行状态
        self.status = "pending"  # pending/running/passed/failed/skipped
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.retry_attempts = 0
        self.result: Optional[Any] = None


class FlowContext:
    """流程上下文"""
    
    def __init__(self, flow_name: str, run_id: Optional[str] = None):
        """初始化流程上下文
        
        Args:
            flow_name: 流程名称
            run_id: 运行ID
        """
        self.flow_name = flow_name
        self.run_id = run_id or str(uuid.uuid4())
        self.data: Dict[str, Any] = {}
        self.shared_data: Dict[str, Any] = {}
        self.logger = get_logger(f"flow_context_{flow_name}")
        
        self.logger.info(f"Initialized flow context: {flow_name} [{self.run_id}]")
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取数据
        
        Args:
            key: 数据键
            default: 默认值
        
        Returns:
            数据值
        """
        return self.data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        self.data[key] = value
        self.logger.debug(f"Set flow data: {key} = {value}")
    
    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """获取共享数据
        
        Args:
            key: 数据键
            default: 默认值
        
        Returns:
            数据值
        """
        return self.shared_data.get(key, default)
    
    def set_shared_data(self, key: str, value: Any) -> None:
        """设置共享数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        self.shared_data[key] = value
        self.logger.debug(f"Set shared data: {key} = {value}")


class FlowRunner:
    """流程执行引擎"""
    
    def __init__(self, name: str, description: str = ""):
        """初始化流程执行器
        
        Args:
            name: 流程名称
            description: 流程描述
        """
        self.name = name
        self.description = description
        self.steps: List[FlowStep] = []
        self.logger = get_logger(f"flow_runner_{name}")
        self.settings = get_settings()
        self.recorder = get_recorder()
        
        # 执行状态
        self.status = "pending"  # pending/running/passed/failed/cancelled
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.context: Optional[FlowContext] = None
        
        self.logger.info(f"Initialized flow runner: {name}")
    
    def add_step(
        self,
        name: str,
        func: Callable,
        description: str = "",
        platform: str = "unknown",
        timeout: Optional[int] = None,
        retry_count: int = 0,
        continue_on_failure: bool = False,
        depends_on: Optional[List[str]] = None
    ) -> FlowStep:
        """添加流程步骤
        
        Args:
            name: 步骤名称
            func: 执行函数
            description: 步骤描述
            platform: 平台类型
            timeout: 超时时间
            retry_count: 重试次数
            continue_on_failure: 失败时是否继续
            depends_on: 依赖的步骤名称列表
        
        Returns:
            流程步骤实例
        """
        # 检查步骤名称是否重复
        if any(step.name == name for step in self.steps):
            raise FlowExecutionError(f"Step name '{name}' already exists")
        
        # 检查依赖的步骤是否存在
        if depends_on:
            existing_step_names = {step.name for step in self.steps}
            for dep in depends_on:
                if dep not in existing_step_names:
                    raise FlowExecutionError(f"Dependency step '{dep}' not found")
        
        step = FlowStep(
            name=name,
            func=func,
            description=description,
            platform=platform,
            timeout=timeout,
            retry_count=retry_count,
            continue_on_failure=continue_on_failure,
            depends_on=depends_on
        )
        
        self.steps.append(step)
        self.logger.info(f"Added step: {name} [{platform}]")
        return step
    
    def remove_step(self, name: str) -> bool:
        """移除流程步骤
        
        Args:
            name: 步骤名称
        
        Returns:
            是否成功移除
        """
        for i, step in enumerate(self.steps):
            if step.name == name:
                # 检查是否有其他步骤依赖此步骤
                dependent_steps = [
                    s.name for s in self.steps 
                    if name in s.depends_on
                ]
                if dependent_steps:
                    raise FlowExecutionError(
                        f"Cannot remove step '{name}', it is required by: {dependent_steps}"
                    )
                
                self.steps.pop(i)
                self.logger.info(f"Removed step: {name}")
                return True
        
        return False
    
    def get_step(self, name: str) -> Optional[FlowStep]:
        """获取流程步骤
        
        Args:
            name: 步骤名称
        
        Returns:
            流程步骤实例
        """
        for step in self.steps:
            if step.name == name:
                return step
        return None
    
    def _validate_flow(self) -> None:
        """验证流程定义"""
        if not self.steps:
            raise FlowExecutionError("No steps defined in flow")
        
        # 检查循环依赖
        def has_circular_dependency(step_name: str, visited: set, path: set) -> bool:
            if step_name in path:
                return True
            if step_name in visited:
                return False
            
            visited.add(step_name)
            path.add(step_name)
            
            step = self.get_step(step_name)
            if step:
                for dep in step.depends_on:
                    if has_circular_dependency(dep, visited, path):
                        return True
            
            path.remove(step_name)
            return False
        
        visited = set()
        for step in self.steps:
            if has_circular_dependency(step.name, visited, set()):
                raise FlowExecutionError(f"Circular dependency detected in step: {step.name}")
    
    def _get_executable_steps(self) -> List[FlowStep]:
        """获取可执行的步骤（依赖已满足）"""
        executable = []
        
        for step in self.steps:
            if step.status != "pending":
                continue
            
            # 检查依赖是否满足
            dependencies_satisfied = True
            for dep_name in step.depends_on:
                dep_step = self.get_step(dep_name)
                if dep_step is None or dep_step.status not in ["passed", "skipped"]:
                    dependencies_satisfied = False
                    break
            
            if dependencies_satisfied:
                executable.append(step)
        
        return executable
    
    async def _execute_step(self, step: FlowStep, context: FlowContext) -> bool:
        """执行单个步骤
        
        Args:
            step: 流程步骤
            context: 流程上下文
        
        Returns:
            是否执行成功
        """
        step.status = "running"
        step.start_time = datetime.now()
        
        self.logger.info(f"Executing step: {step.name} [{step.platform}]")
        
        try:
            # 记录步骤开始
            step_data = {
                'step_name': step.name,
                'step_description': step.description,
                'platform': step.platform,
                'status': 'running',
                'start_time': step.start_time,
                'input_data': {
                    'context_data': dict(context.data),
                    'shared_data': dict(context.shared_data)
                }
            }
            
            # 执行步骤函数
            if asyncio.iscoroutinefunction(step.func):
                # 异步函数
                result = await asyncio.wait_for(
                    step.func(context),
                    timeout=step.timeout
                )
            else:
                # 同步函数
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: step.func(context)
                )
            
            step.result = result
            step.status = "passed"
            step.end_time = datetime.now()
            
            # 记录步骤成功
            step_data.update({
                'status': 'passed',
                'end_time': step.end_time,
                'duration': (step.end_time - step.start_time).total_seconds(),
                'output_data': {'result': result} if result is not None else None
            })
            
            self.logger.info(f"Step completed: {step.name} -> passed")
            return True
        
        except asyncio.TimeoutError:
            step.status = "failed"
            step.end_time = datetime.now()
            step.error_message = f"Step timeout after {step.timeout} seconds"
            
            self.logger.error(f"Step timeout: {step.name}")
            return False
        
        except Exception as e:
            step.status = "failed"
            step.end_time = datetime.now()
            step.error_message = str(e)
            
            self.logger.error(f"Step failed: {step.name} - {e}")
            return False
    
    async def _retry_step(self, step: FlowStep, context: FlowContext) -> bool:
        """重试步骤执行
        
        Args:
            step: 流程步骤
            context: 流程上下文
        
        Returns:
            是否执行成功
        """
        for attempt in range(step.retry_count):
            step.retry_attempts = attempt + 1
            step.status = "pending"  # 重置状态
            
            self.logger.info(f"Retrying step: {step.name} (attempt {attempt + 1}/{step.retry_count})")
            
            if await self._execute_step(step, context):
                return True
            
            # 重试间隔
            if attempt < step.retry_count - 1:
                await asyncio.sleep(min(2 ** attempt, 10))  # 指数退避，最大10秒
        
        return False
    
    async def run(self, run_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """运行流程
        
        Args:
            run_id: 运行ID
            **kwargs: 初始化数据
        
        Returns:
            执行结果
        """
        self.status = "running"
        self.start_time = datetime.now()
        
        # 创建流程上下文
        self.context = FlowContext(self.name, run_id)
        self.context.data.update(kwargs)
        
        self.logger.info(f"Starting flow: {self.name} [{self.context.run_id}]")
        
        try:
            # 验证流程定义
            self._validate_flow()
            
            # 重置所有步骤状态
            for step in self.steps:
                step.status = "pending"
                step.retry_attempts = 0
                step.start_time = None
                step.end_time = None
                step.error_message = None
                step.result = None
            
            # 执行流程
            completed_steps = 0
            failed_steps = 0
            skipped_steps = 0
            
            while completed_steps + failed_steps + skipped_steps < len(self.steps):
                executable_steps = self._get_executable_steps()
                
                if not executable_steps:
                    # 检查是否有待执行的步骤但依赖未满足
                    pending_steps = [s for s in self.steps if s.status == "pending"]
                    if pending_steps:
                        self.logger.error("Deadlock detected: steps have unmet dependencies")
                        for step in pending_steps:
                            step.status = "skipped"
                            skipped_steps += 1
                    break
                
                # 并发执行可执行的步骤
                tasks = []
                for step in executable_steps:
                    task = self._execute_step(step, self.context)
                    tasks.append((step, task))
                
                # 等待所有任务完成
                for step, task in tasks:
                    success = await task
                    
                    if success:
                        completed_steps += 1
                    elif step.retry_count > 0:
                        # 尝试重试
                        if await self._retry_step(step, self.context):
                            completed_steps += 1
                        else:
                            if step.continue_on_failure:
                                step.status = "skipped"
                                skipped_steps += 1
                            else:
                                failed_steps += 1
                    else:
                        if step.continue_on_failure:
                            step.status = "skipped"
                            skipped_steps += 1
                        else:
                            failed_steps += 1
                
                # 如果有步骤失败且不允许继续，则停止执行
                if failed_steps > 0:
                    remaining_steps = [s for s in self.steps if s.status == "pending"]
                    for step in remaining_steps:
                        step.status = "skipped"
                        skipped_steps += 1
                    break
            
            # 确定流程执行结果
            if failed_steps > 0:
                self.status = "failed"
            elif completed_steps > 0:
                self.status = "passed"
            else:
                self.status = "skipped"
            
            self.end_time = datetime.now()
            
            # 构建执行结果
            result = {
                'flow_name': self.name,
                'run_id': self.context.run_id,
                'status': self.status,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'duration': (self.end_time - self.start_time).total_seconds(),
                'total_steps': len(self.steps),
                'completed_steps': completed_steps,
                'failed_steps': failed_steps,
                'skipped_steps': skipped_steps,
                'steps': [
                    {
                        'name': step.name,
                        'status': step.status,
                        'platform': step.platform,
                        'start_time': step.start_time,
                        'end_time': step.end_time,
                        'duration': (
                            (step.end_time - step.start_time).total_seconds()
                            if step.start_time and step.end_time
                            else None
                        ),
                        'retry_attempts': step.retry_attempts,
                        'error_message': step.error_message,
                        'result': step.result
                    }
                    for step in self.steps
                ],
                'context_data': dict(self.context.data),
                'shared_data': dict(self.context.shared_data)
            }
            
            self.logger.info(
                f"Flow completed: {self.name} -> {self.status} "
                f"({completed_steps} passed, {failed_steps} failed, {skipped_steps} skipped)"
            )
            
            return result
        
        except Exception as e:
            self.status = "failed"
            self.end_time = datetime.now()
            
            self.logger.error(f"Flow execution failed: {self.name} - {e}")
            raise FlowExecutionError(f"Flow execution failed: {e}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要
        
        Returns:
            执行摘要信息
        """
        if not self.start_time:
            return {
                'flow_name': self.name,
                'status': self.status,
                'message': 'Flow not started'
            }
        
        passed_steps = [s for s in self.steps if s.status == "passed"]
        failed_steps = [s for s in self.steps if s.status == "failed"]
        skipped_steps = [s for s in self.steps if s.status == "skipped"]
        
        return {
            'flow_name': self.name,
            'status': self.status,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': (
                (self.end_time - self.start_time).total_seconds()
                if self.end_time
                else None
            ),
            'total_steps': len(self.steps),
            'passed_steps': len(passed_steps),
            'failed_steps': len(failed_steps),
            'skipped_steps': len(skipped_steps),
            'success_rate': (
                len(passed_steps) / len(self.steps) * 100
                if self.steps
                else 0
            )
        }


# 工厂函数和装饰器

def create_flow(name: str, description: str = "") -> FlowRunner:
    """创建流程执行器
    
    Args:
        name: 流程名称
        description: 流程描述
    
    Returns:
        流程执行器实例
    """
    return FlowRunner(name, description)


def flow_step(
    name: str,
    description: str = "",
    platform: str = "unknown",
    timeout: Optional[int] = None,
    retry_count: int = 0,
    continue_on_failure: bool = False,
    depends_on: Optional[List[str]] = None
):
    """流程步骤装饰器
    
    Args:
        name: 步骤名称
        description: 步骤描述
        platform: 平台类型
        timeout: 超时时间
        retry_count: 重试次数
        continue_on_failure: 失败时是否继续
        depends_on: 依赖的步骤名称列表
    """
    def decorator(func: Callable):
        func._flow_step_config = {
            'name': name,
            'description': description,
            'platform': platform,
            'timeout': timeout,
            'retry_count': retry_count,
            'continue_on_failure': continue_on_failure,
            'depends_on': depends_on
        }
        return func
    return decorator


if __name__ == "__main__":
    # 测试流程执行引擎
    async def test_flow_runner():
        print("Testing Flow Runner...")
        
        # 创建测试流程
        flow = create_flow("test_flow", "测试流程")
        
        # 定义测试步骤
        async def step1(context: FlowContext):
            print("Executing step 1")
            context.set_shared_data("step1_result", "success")
            return "step1_done"
        
        def step2(context: FlowContext):
            print("Executing step 2")
            step1_result = context.get_shared_data("step1_result")
            print(f"Step 1 result: {step1_result}")
            return "step2_done"
        
        async def step3(context: FlowContext):
            print("Executing step 3")
            await asyncio.sleep(1)  # 模拟异步操作
            return "step3_done"
        
        # 添加步骤
        flow.add_step("step1", step1, "第一步", "test")
        flow.add_step("step2", step2, "第二步", "test", depends_on=["step1"])
        flow.add_step("step3", step3, "第三步", "test", depends_on=["step1"])
        
        # 执行流程
        try:
            result = await flow.run(test_data="test_value")
            print(f"Flow result: {result['status']}")
            print(f"Duration: {result['duration']:.2f} seconds")
            print(f"Steps: {result['completed_steps']} passed, {result['failed_steps']} failed")
            
            # 获取执行摘要
            summary = flow.get_execution_summary()
            print(f"Success rate: {summary['success_rate']:.1f}%")
            
        except Exception as e:
            print(f"Flow execution failed: {e}")
    
    # 运行测试
    asyncio.run(test_flow_runner())
