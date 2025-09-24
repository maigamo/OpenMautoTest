"""
OpenMautoTest 时间处理工具模块

提供时间格式化、时间差计算、等待条件等时间相关的通用函数
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional, Union

import pytz


def get_current_time(tz: Optional[Union[str, timezone]] = None) -> datetime:
    """获取当前时间
    
    Args:
        tz: 时区，可以是时区名称字符串或timezone对象
    
    Returns:
        当前时间的datetime对象
    """
    if tz is None:
        return datetime.now()
    
    if isinstance(tz, str):
        tz = pytz.timezone(tz)
    
    return datetime.now(tz)


def format_timestamp(
    timestamp: Union[datetime, float, int],
    format_str: str = "%Y-%m-%d %H:%M:%S",
    tz: Optional[Union[str, timezone]] = None
) -> str:
    """格式化时间戳
    
    Args:
        timestamp: 时间戳，可以是datetime对象或Unix时间戳
        format_str: 格式化字符串
        tz: 时区
    
    Returns:
        格式化后的时间字符串
    """
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = timestamp
    
    if tz is not None:
        if isinstance(tz, str):
            tz = pytz.timezone(tz)
        dt = dt.astimezone(tz)
    
    return dt.strftime(format_str)


def parse_time_string(
    time_str: str,
    format_str: str = "%Y-%m-%d %H:%M:%S",
    tz: Optional[Union[str, timezone]] = None
) -> datetime:
    """解析时间字符串
    
    Args:
        time_str: 时间字符串
        format_str: 格式化字符串
        tz: 时区
    
    Returns:
        解析后的datetime对象
    """
    dt = datetime.strptime(time_str, format_str)
    
    if tz is not None:
        if isinstance(tz, str):
            tz = pytz.timezone(tz)
        dt = tz.localize(dt)
    
    return dt


def time_diff(
    start_time: Union[datetime, float, int],
    end_time: Optional[Union[datetime, float, int]] = None
) -> float:
    """计算时间差（秒）
    
    Args:
        start_time: 开始时间
        end_time: 结束时间，默认为当前时间
    
    Returns:
        时间差（秒）
    """
    if end_time is None:
        end_time = datetime.now()
    
    # 转换为datetime对象
    if isinstance(start_time, (int, float)):
        start_time = datetime.fromtimestamp(start_time)
    if isinstance(end_time, (int, float)):
        end_time = datetime.fromtimestamp(end_time)
    
    return (end_time - start_time).total_seconds()


def add_time(
    base_time: Union[datetime, float, int],
    **kwargs
) -> datetime:
    """时间加法
    
    Args:
        base_time: 基准时间
        **kwargs: timedelta参数（days, seconds, microseconds, milliseconds, minutes, hours, weeks）
    
    Returns:
        计算后的时间
    """
    if isinstance(base_time, (int, float)):
        base_time = datetime.fromtimestamp(base_time)
    
    delta = timedelta(**kwargs)
    return base_time + delta


def subtract_time(
    base_time: Union[datetime, float, int],
    **kwargs
) -> datetime:
    """时间减法
    
    Args:
        base_time: 基准时间
        **kwargs: timedelta参数
    
    Returns:
        计算后的时间
    """
    if isinstance(base_time, (int, float)):
        base_time = datetime.fromtimestamp(base_time)
    
    delta = timedelta(**kwargs)
    return base_time - delta


def is_within_time_range(
    check_time: Union[datetime, float, int],
    start_time: Union[datetime, float, int],
    end_time: Union[datetime, float, int]
) -> bool:
    """检查时间是否在指定范围内
    
    Args:
        check_time: 要检查的时间
        start_time: 开始时间
        end_time: 结束时间
    
    Returns:
        是否在时间范围内
    """
    # 转换为datetime对象
    if isinstance(check_time, (int, float)):
        check_time = datetime.fromtimestamp(check_time)
    if isinstance(start_time, (int, float)):
        start_time = datetime.fromtimestamp(start_time)
    if isinstance(end_time, (int, float)):
        end_time = datetime.fromtimestamp(end_time)
    
    return start_time <= check_time <= end_time


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 30.0,
    interval: float = 0.5,
    error_message: str = "Condition not met within timeout"
) -> bool:
    """等待条件满足
    
    Args:
        condition: 条件检查函数，返回bool
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）
        error_message: 超时错误消息
    
    Returns:
        条件是否满足
    
    Raises:
        TimeoutError: 超时时抛出异常
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(interval)
    
    raise TimeoutError(error_message)


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """带退避的重试机制
    
    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
        max_delay: 最大延迟时间（秒）
        exceptions: 需要重试的异常类型
    
    Returns:
        函数执行结果
    
    Raises:
        最后一次执行的异常
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt == max_retries:
                break
            
            time.sleep(min(delay, max_delay))
            delay *= backoff_factor
    
    raise last_exception


def measure_execution_time(func: Callable) -> tuple:
    """测量函数执行时间
    
    Args:
        func: 要测量的函数
    
    Returns:
        (执行结果, 执行时间)
    """
    start_time = time.time()
    result = func()
    execution_time = time.time() - start_time
    
    return result, execution_time


class Timer:
    """计时器类"""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self) -> float:
        """停止计时并返回耗时"""
        if self.start_time is None:
            raise ValueError("Timer not started")
        
        self.end_time = time.time()
        return self.elapsed_time()
    
    def elapsed_time(self) -> float:
        """获取已耗时间"""
        if self.start_time is None:
            raise ValueError("Timer not started")
        
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time
    
    def reset(self):
        """重置计时器"""
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class PerformanceTimer:
    """性能计时器"""
    
    def __init__(self, name: str = "operation"):
        self.name = name
        self.timer = Timer()
    
    def __enter__(self):
        self.timer.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = self.timer.stop()
        print(f"Performance - {self.name}: {elapsed:.3f}s")


def sleep_with_progress(
    duration: float,
    step: float = 1.0,
    callback: Optional[Callable[[float], None]] = None
):
    """带进度回调的睡眠
    
    Args:
        duration: 总睡眠时间（秒）
        step: 步长（秒）
        callback: 进度回调函数，接收剩余时间参数
    """
    remaining = duration
    
    while remaining > 0:
        sleep_time = min(step, remaining)
        time.sleep(sleep_time)
        remaining -= sleep_time
        
        if callback:
            callback(remaining)


def get_business_days(
    start_date: datetime,
    end_date: datetime,
    holidays: Optional[list] = None
) -> int:
    """计算工作日天数
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        holidays: 节假日列表
    
    Returns:
        工作日天数
    """
    if holidays is None:
        holidays = []
    
    business_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        # 检查是否为工作日（周一到周五）
        if current_date.weekday() < 5:
            # 检查是否为节假日
            if current_date.date() not in holidays:
                business_days += 1
        
        current_date += timedelta(days=1)
    
    return business_days


def format_duration(seconds: float) -> str:
    """格式化时长
    
    Args:
        seconds: 时长（秒）
    
    Returns:
        格式化后的时长字符串
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.0f}s"


if __name__ == "__main__":
    # 测试时间工具函数
    print("Testing time utilities...")
    
    # 当前时间
    now = get_current_time()
    print(f"Current time: {now}")
    
    # 格式化时间
    formatted = format_timestamp(now, "%Y-%m-%d %H:%M:%S")
    print(f"Formatted time: {formatted}")
    
    # 时间差计算
    past_time = subtract_time(now, hours=1)
    diff = time_diff(past_time, now)
    print(f"Time difference: {diff} seconds")
    
    # 计时器测试
    with Timer() as timer:
        time.sleep(0.1)
    print(f"Timer elapsed: {timer.elapsed_time():.3f}s")
    
    # 性能计时器测试
    with PerformanceTimer("test operation"):
        time.sleep(0.05)
    
    # 格式化时长
    print(f"Duration format: {format_duration(125.5)}")
    
    print("Time utilities tests completed.")
