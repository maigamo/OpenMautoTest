"""
OpenMautoTest API客户端

基于httpx实现的HTTP API客户端，提供统一的API调用接口
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import httpx
from httpx import Response, Timeout

from common.logger import get_logger
from common.utils.file_utils import ensure_dir, write_json_file
from common.utils.time_utils import Timer
from configs.settings import get_settings


class APIClientError(Exception):
    """API客户端异常"""
    pass


class BaseAPIClient:
    """基础API客户端"""
    
    def __init__(
        self,
        base_url: str,
        timeout: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """初始化API客户端
        
        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            headers: 默认请求头
        """
        self.settings = get_settings()
        self.logger = get_logger("api_client")
        
        # 基础配置
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout or 30
        self.default_headers = {
            'Content-Type': 'application/json',
            'User-Agent': f'OpenMautoTest/{self.settings.VERSION}',
            **(headers or {})
        }
        
        # HTTP客户端
        self._client: Optional[httpx.Client] = None
        
        # 认证信息
        self._auth_token: Optional[str] = None
        self._auth_type: str = 'Bearer'
        
        # 请求记录
        self.request_history: List[Dict[str, Any]] = []
        self.log_dir = ensure_dir(self.settings.get_output_dir() / "api_logs")
        
        # 性能监控
        self.performance_metrics = {}
        
        self.logger.info(f"Initialized API client: {self.base_url}")
    
    def start(self) -> None:
        """启动API客户端"""
        try:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=Timeout(self.timeout),
                headers=self.default_headers,
                verify=not self.settings.is_development(),  # 开发环境跳过SSL验证
                follow_redirects=True
            )
            
            self.logger.info("API client started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start API client: {e}")
            raise APIClientError(f"API client startup failed: {e}")
    
    def stop(self) -> None:
        """停止API客户端"""
        try:
            if self._client:
                self._client.close()
                self._client = None
            
            self.logger.info("API client stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping API client: {e}")
    
    @property
    def client(self) -> httpx.Client:
        """获取HTTP客户端实例
        
        Returns:
            HTTP客户端实例
        
        Raises:
            APIClientError: 客户端未启动时抛出
        """
        if self._client is None:
            raise APIClientError("API client not started. Call start() first.")
        return self._client
    
    def set_auth_token(self, token: str, auth_type: str = 'Bearer') -> None:
        """设置认证令牌
        
        Args:
            token: 认证令牌
            auth_type: 认证类型
        """
        self._auth_token = token
        self._auth_type = auth_type
        
        auth_header = f"{auth_type} {token}"
        self.default_headers['Authorization'] = auth_header
        
        if self._client:
            self._client.headers['Authorization'] = auth_header
        
        self.logger.info(f"Set auth token: {auth_type} {token[:10]}...")
    
    def clear_auth_token(self) -> None:
        """清除认证令牌"""
        self._auth_token = None
        self._auth_type = 'Bearer'
        
        if 'Authorization' in self.default_headers:
            del self.default_headers['Authorization']
        
        if self._client and 'Authorization' in self._client.headers:
            del self._client.headers['Authorization']
        
        self.logger.info("Cleared auth token")
    
    def _prepare_url(self, endpoint: str) -> str:
        """准备完整URL
        
        Args:
            endpoint: API端点
        
        Returns:
            完整URL
        """
        if endpoint.startswith('http'):
            return endpoint
        
        return urljoin(self.base_url + '/', endpoint.lstrip('/'))
    
    def _log_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        response: Optional[Response] = None,
        duration: Optional[float] = None
    ) -> None:
        """记录请求日志
        
        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            data: 请求数据
            response: 响应对象
            duration: 请求耗时
        """
        log_entry = {
            'timestamp': time.time(),
            'method': method,
            'url': url,
            'headers': headers,
            'request_data': data,
            'duration': duration
        }
        
        if response:
            log_entry.update({
                'status_code': response.status_code,
                'response_headers': dict(response.headers),
                'response_size': len(response.content) if response.content else 0
            })
            
            # 记录响应内容（限制大小）
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    response_text = response.text
                    if len(response_text) <= 10000:  # 限制10KB
                        log_entry['response_data'] = response.json()
                    else:
                        log_entry['response_data'] = f"<large response: {len(response_text)} bytes>"
                else:
                    log_entry['response_data'] = f"<non-json response: {response.headers.get('content-type')}>"
            except Exception:
                log_entry['response_data'] = "<failed to parse response>"
        
        self.request_history.append(log_entry)
        
        # 记录到文件（可选）
        if self.settings.is_development():
            try:
                timestamp = int(time.time() * 1000)
                log_file = self.log_dir / f"api_request_{timestamp}.json"
                write_json_file(log_file, log_entry)
            except Exception as e:
                self.logger.warning(f"Failed to write API log: {e}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Response:
        """发起HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: URL参数
            data: 表单数据
            json_data: JSON数据
            headers: 请求头
            timeout: 超时时间
            **kwargs: 其他请求参数
        
        Returns:
            HTTP响应对象
        """
        url = self._prepare_url(endpoint)
        
        # 合并请求头
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)
        
        # 准备请求参数
        request_kwargs = {
            'params': params,
            'headers': request_headers,
            'timeout': timeout or self.timeout,
            **kwargs
        }
        
        if json_data is not None:
            request_kwargs['json'] = json_data
        elif data is not None:
            request_kwargs['data'] = data
        
        # 发起请求
        response = None
        start_time = time.time()
        
        try:
            response = self.client.request(method, url, **request_kwargs)
            duration = time.time() - start_time
            
            # 记录请求
            self._log_request(
                method=method,
                url=url,
                headers=request_headers,
                data=json_data or data,
                response=response,
                duration=duration
            )
            
            # 更新性能指标
            self.performance_metrics[f'{method.lower()}_requests'] = \
                self.performance_metrics.get(f'{method.lower()}_requests', 0) + 1
            self.performance_metrics['total_requests'] = \
                self.performance_metrics.get('total_requests', 0) + 1
            self.performance_metrics['avg_response_time'] = \
                (self.performance_metrics.get('avg_response_time', 0) * 
                 (self.performance_metrics['total_requests'] - 1) + duration) / \
                self.performance_metrics['total_requests']
            
            self.logger.info(f"{method} {url} -> {response.status_code} ({duration:.3f}s)")
            
            # 检查响应状态
            if not response.is_success:
                self.logger.warning(f"Request failed: {response.status_code} {response.text}")
            
            return response
            
        except httpx.TimeoutException as e:
            duration = time.time() - start_time
            self.logger.error(f"Request timeout: {method} {url} ({duration:.3f}s)")
            self._log_request(method, url, request_headers, json_data or data, None, duration)
            raise APIClientError(f"Request timeout: {e}")
        
        except httpx.RequestError as e:
            duration = time.time() - start_time
            self.logger.error(f"Request error: {method} {url} - {e}")
            self._log_request(method, url, request_headers, json_data or data, None, duration)
            raise APIClientError(f"Request error: {e}")
        
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Unexpected error: {method} {url} - {e}")
            self._log_request(method, url, request_headers, json_data or data, response, duration)
            raise APIClientError(f"Unexpected error: {e}")
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Response:
        """发起GET请求
        
        Args:
            endpoint: API端点
            params: URL参数
            headers: 请求头
            timeout: 超时时间
            **kwargs: 其他请求参数
        
        Returns:
            HTTP响应对象
        """
        return self._make_request('GET', endpoint, params=params, headers=headers, timeout=timeout, **kwargs)
    
    def post(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json_data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Response:
        """发起POST请求
        
        Args:
            endpoint: API端点
            data: 表单数据
            json_data: JSON数据
            params: URL参数
            headers: 请求头
            timeout: 超时时间
            **kwargs: 其他请求参数
        
        Returns:
            HTTP响应对象
        """
        return self._make_request(
            'POST', endpoint,
            params=params,
            data=data,
            json_data=json_data,
            headers=headers,
            timeout=timeout,
            **kwargs
        )
    
    def put(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json_data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Response:
        """发起PUT请求
        
        Args:
            endpoint: API端点
            data: 表单数据
            json_data: JSON数据
            params: URL参数
            headers: 请求头
            timeout: 超时时间
            **kwargs: 其他请求参数
        
        Returns:
            HTTP响应对象
        """
        return self._make_request(
            'PUT', endpoint,
            params=params,
            data=data,
            json_data=json_data,
            headers=headers,
            timeout=timeout,
            **kwargs
        )
    
    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Response:
        """发起DELETE请求
        
        Args:
            endpoint: API端点
            params: URL参数
            headers: 请求头
            timeout: 超时时间
            **kwargs: 其他请求参数
        
        Returns:
            HTTP响应对象
        """
        return self._make_request('DELETE', endpoint, params=params, headers=headers, timeout=timeout, **kwargs)
    
    def patch(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json_data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Response:
        """发起PATCH请求
        
        Args:
            endpoint: API端点
            data: 表单数据
            json_data: JSON数据
            params: URL参数
            headers: 请求头
            timeout: 超时时间
            **kwargs: 其他请求参数
        
        Returns:
            HTTP响应对象
        """
        return self._make_request(
            'PATCH', endpoint,
            params=params,
            data=data,
            json_data=json_data,
            headers=headers,
            timeout=timeout,
            **kwargs
        )
    
    def upload_file(
        self,
        endpoint: str,
        file_path: Union[str, Path],
        file_field: str = 'file',
        additional_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Response:
        """上传文件
        
        Args:
            endpoint: API端点
            file_path: 文件路径
            file_field: 文件字段名
            additional_data: 附加表单数据
            headers: 请求头
            timeout: 超时时间
        
        Returns:
            HTTP响应对象
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise APIClientError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {file_field: (file_path.name, f, 'application/octet-stream')}
                data = additional_data or {}
                
                return self._make_request(
                    'POST', endpoint,
                    data=data,
                    headers=headers,
                    timeout=timeout or 60,  # 文件上传使用更长的超时时间
                    files=files
                )
        
        except Exception as e:
            self.logger.error(f"Failed to upload file {file_path}: {e}")
            raise APIClientError(f"File upload failed: {e}")
    
    def download_file(
        self,
        endpoint: str,
        file_path: Union[str, Path],
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Path:
        """下载文件
        
        Args:
            endpoint: API端点
            file_path: 保存文件路径
            params: URL参数
            headers: 请求头
            timeout: 超时时间
        
        Returns:
            保存的文件路径
        """
        file_path = Path(file_path)
        ensure_dir(file_path.parent)
        
        try:
            response = self.get(endpoint, params=params, headers=headers, timeout=timeout or 60)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"Downloaded file: {file_path} ({len(response.content)} bytes)")
            return file_path
        
        except Exception as e:
            self.logger.error(f"Failed to download file to {file_path}: {e}")
            raise APIClientError(f"File download failed: {e}")
    
    def get_json(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发起GET请求并返回JSON数据
        
        Args:
            endpoint: API端点
            **kwargs: 请求参数
        
        Returns:
            JSON响应数据
        """
        response = self.get(endpoint, **kwargs)
        try:
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            raise APIClientError(f"JSON parse error: {e}")
    
    def post_json(self, endpoint: str, json_data: Any, **kwargs) -> Dict[str, Any]:
        """发起POST请求并返回JSON数据
        
        Args:
            endpoint: API端点
            json_data: JSON请求数据
            **kwargs: 请求参数
        
        Returns:
            JSON响应数据
        """
        response = self.post(endpoint, json_data=json_data, **kwargs)
        try:
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            raise APIClientError(f"JSON parse error: {e}")
    
    def health_check(self, endpoint: str = '/health') -> bool:
        """健康检查
        
        Args:
            endpoint: 健康检查端点
        
        Returns:
            是否健康
        """
        try:
            response = self.get(endpoint, timeout=5)
            is_healthy = response.is_success
            self.logger.info(f"Health check: {'OK' if is_healthy else 'FAILED'}")
            return is_healthy
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标
        
        Returns:
            性能指标字典
        """
        return {
            'request_count': len(self.request_history),
            'success_rate': self._calculate_success_rate(),
            **self.performance_metrics
        }
    
    def _calculate_success_rate(self) -> float:
        """计算成功率
        
        Returns:
            成功率百分比
        """
        if not self.request_history:
            return 0.0
        
        success_count = sum(
            1 for entry in self.request_history
            if entry.get('status_code', 0) < 400
        )
        
        return (success_count / len(self.request_history)) * 100
    
    def clear_history(self) -> None:
        """清除请求历史"""
        self.request_history.clear()
        self.performance_metrics.clear()
        self.logger.info("Cleared request history and metrics")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop()


if __name__ == "__main__":
    # 测试API客户端
    def test_api_client():
        print("Testing API Client...")
        
        try:
            with BaseAPIClient("https://httpbin.org") as client:
                # 测试GET请求
                response = client.get("/get", params={"test": "value"})
                print(f"GET request: {response.status_code}")
                
                # 测试POST请求
                response = client.post("/post", json_data={"key": "value"})
                print(f"POST request: {response.status_code}")
                
                # 测试健康检查
                is_healthy = client.health_check("/status/200")
                print(f"Health check: {is_healthy}")
                
                # 获取性能指标
                metrics = client.get_performance_metrics()
                print(f"Performance metrics: {metrics}")
        
        except Exception as e:
            print(f"API client test failed: {e}")
    
    # 运行测试
    test_api_client()
    print("API client test completed.")
