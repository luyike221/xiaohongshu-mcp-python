"""存储服务"""

from typing import BinaryIO, Optional

from ..config import settings
from ..core.exceptions import StorageError
from ..tools.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """存储服务"""

    def __init__(self):
        self.endpoint = settings.minio_endpoint
        self.access_key = settings.minio_access_key
        self.secret_key = settings.minio_secret_key
        self.bucket = settings.minio_bucket

    async def upload_file(self, file_path: str, object_name: str) -> str:
        """上传文件"""
        # TODO: 实现文件上传逻辑
        raise NotImplementedError

    async def download_file(self, object_name: str, file_path: str) -> None:
        """下载文件"""
        # TODO: 实现文件下载逻辑
        raise NotImplementedError

    async def delete_file(self, object_name: str) -> None:
        """删除文件"""
        # TODO: 实现文件删除逻辑
        raise NotImplementedError

    def get_file_url(self, object_name: str) -> str:
        """获取文件 URL"""
        # TODO: 实现获取文件 URL 逻辑
        raise NotImplementedError

