"""
Storage Service
文件存储服务 - 支持多种存储后端
"""

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
import uuid
from typing import BinaryIO, Tuple
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    async def save(self, file_content: bytes, file_name: str, content_type: str, user_id: int) -> Tuple[str, str]:
        """
        保存文件
        
        Args:
            file_content: 文件内容
            file_name: 原始文件名
            content_type: MIME类型
            user_id: 用户ID（用于文件隔离）
        
        Returns:
            Tuple[file_id, file_url]: 文件ID和访问URL
        """
        pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
        
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_url(self, file_id: str) -> str | None:
        """
        获取文件访问URL
        
        Args:
            file_id: 文件ID
        
        Returns:
            str | None: 文件URL，不存在返回None
        """
        pass


class LocalStorageBackend(StorageBackend):
    """本地文件系统存储（开发/测试环境）"""
    
    def __init__(self, base_dir: str = "uploads/attachments"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info("local_storage_initialized", base_dir=str(self.base_dir))
    
    async def save(self, file_content: bytes, file_name: str, content_type: str, user_id: int) -> Tuple[str, str]:
        """
        保存文件到本地文件系统
        
        文件路径结构: uploads/attachments/user_{user_id}/uuid.ext
        例如: uploads/attachments/user_123/550e8400-e29b-41d4-a716-446655440000.pdf
        """
        # 创建用户专属目录
        user_dir = self.base_dir / f"user_{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        file_extension = Path(file_name).suffix
        stored_filename = f"{file_id}{file_extension}"
        file_path = user_dir / stored_filename
        
        # 保存文件
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            logger.info(
                "file_saved_locally",
                file_id=file_id,
                user_id=user_id,
                file_name=file_name,
                file_size=len(file_content),
                stored_path=str(file_path)
            )
            
            # 构建访问URL（包含用户ID路径）
            file_url = f"/api/v1/attachments/files/user_{user_id}/{stored_filename}"
            return file_id, file_url
            
        except Exception as e:
            logger.error("file_save_failed", file_id=file_id, user_id=user_id, error=str(e))
            raise
    
    async def delete(self, file_id: str) -> bool:
        """从本地文件系统删除文件"""
        # 在所有用户目录中查找文件
        found_file = None
        for user_dir in self.base_dir.glob("user_*"):
            if not user_dir.is_dir():
                continue
            for file_path in user_dir.glob(f"{file_id}.*"):
                found_file = file_path
                break
            if found_file:
                break
        
        if not found_file:
            logger.warning("file_not_found_for_deletion", file_id=file_id)
            return False
        
        try:
            found_file.unlink()
            logger.info("file_deleted_locally", file_id=file_id, file_path=str(found_file))
            return True
        except Exception as e:
            logger.error("file_deletion_failed", file_id=file_id, error=str(e))
            return False
    
    async def get_url(self, file_id: str) -> str | None:
        """获取本地文件的访问URL"""
        # 在所有用户目录中查找文件
        for user_dir in self.base_dir.glob("user_*"):
            if not user_dir.is_dir():
                continue
            for file_path in user_dir.glob(f"{file_id}.*"):
                user_dir_name = user_dir.name  # 例如: user_123
                filename = file_path.name
                return f"/api/v1/attachments/files/{user_dir_name}/{filename}"
        return None


class AliyunOSSBackend(StorageBackend):
    """阿里云OSS存储（生产环境推荐）"""
    
    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        bucket_name: str
    ):
        """
        初始化阿里云OSS客户端
        
        需要安装: pip install oss2
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        
        # 延迟导入，避免未安装 oss2 时报错
        try:
            import oss2
            auth = oss2.Auth(access_key_id, access_key_secret)
            self.bucket = oss2.Bucket(auth, endpoint, bucket_name)
            logger.info(
                "aliyun_oss_initialized",
                bucket=bucket_name,
                endpoint=endpoint
            )
        except ImportError:
            logger.error("oss2_not_installed", message="请安装 oss2: pip install oss2")
            raise RuntimeError("oss2 未安装")
    
    async def save(self, file_content: bytes, file_name: str, content_type: str, user_id: int) -> Tuple[str, str]:
        """
        上传文件到阿里云OSS
        
        文件路径结构: attachments/{user_id}/2025/12/28/uuid.ext
        例如: attachments/123/2025/12/28/550e8400-e29b-41d4-a716-446655440000.pdf
        """
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        file_extension = Path(file_name).suffix
        
        # OSS对象key（路径）- 添加用户ID隔离
        # 格式: attachments/{user_id}/2025/12/28/uuid.pdf
        date_path = datetime.now().strftime("%Y/%m/%d")
        object_key = f"attachments/{user_id}/{date_path}/{file_id}{file_extension}"
        
        try:
            # 上传文件
            self.bucket.put_object(
                object_key,
                file_content,
                headers={'Content-Type': content_type}
            )
            
            logger.info(
                "file_uploaded_to_oss",
                file_id=file_id,
                user_id=user_id,
                object_key=object_key,
                file_size=len(file_content)
            )
            
            # 构建访问URL
            # 如果bucket是公共读，直接返回URL
            # 如果是私有，需要生成签名URL
            file_url = f"https://{self.bucket_name}.{self.endpoint}/{object_key}"
            
            return file_id, file_url
            
        except Exception as e:
            logger.error("oss_upload_failed", file_id=file_id, user_id=user_id, error=str(e))
            raise
    
    async def delete(self, file_id: str) -> bool:
        """从阿里云OSS删除文件"""
        # 这里需要额外维护一个 file_id -> object_key 的映射
        # 或者在数据库中存储 object_key
        # 简化处理：通过 list_objects 查找
        try:
            # 实际应该从数据库获取 object_key
            # 这里仅作示例
            logger.warning(
                "oss_delete_needs_object_key",
                file_id=file_id,
                message="需要从数据库获取 object_key"
            )
            return False
        except Exception as e:
            logger.error("oss_deletion_failed", file_id=file_id, error=str(e))
            return False
    
    async def get_url(self, file_id: str) -> str | None:
        """获取OSS文件的访问URL（可能是签名URL）"""
        # 实际应该从数据库获取存储的URL
        return None


class StorageService:
    """存储服务（单例模式）"""
    
    _instance = None
    _backend: StorageBackend = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """根据配置初始化存储后端"""
        if self._backend is not None:
            return  # 已初始化
        
        storage_type = getattr(settings, 'STORAGE_TYPE', 'local')
        
        if storage_type == 'aliyun_oss':
            # 阿里云OSS存储
            self._backend = AliyunOSSBackend(
                access_key_id=settings.ALIYUN_OSS_ACCESS_KEY_ID,
                access_key_secret=settings.ALIYUN_OSS_ACCESS_KEY_SECRET,
                endpoint=settings.ALIYUN_OSS_ENDPOINT,
                bucket_name=settings.ALIYUN_OSS_BUCKET_NAME
            )
            logger.info("storage_service_initialized", backend="aliyun_oss")
        else:
            # 默认使用本地存储
            upload_dir = getattr(settings, 'UPLOAD_DIR', 'uploads/attachments')
            self._backend = LocalStorageBackend(upload_dir)
            logger.info("storage_service_initialized", backend="local")
    
    async def save_file(self, file_content: bytes, file_name: str, content_type: str, user_id: int) -> Tuple[str, str]:
        """
        保存文件
        
        Args:
            file_content: 文件内容
            file_name: 文件名
            content_type: MIME类型
            user_id: 用户ID（用于文件隔离）
        
        Returns:
            Tuple[file_id, file_url]
        """
        return await self._backend.save(file_content, file_name, content_type, user_id)
    
    async def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        return await self._backend.delete(file_id)
    
    async def get_file_url(self, file_id: str) -> str | None:
        """获取文件URL"""
        return await self._backend.get_url(file_id)
    
    async def get_user_storage_usage(self, user_id: int) -> dict:
        """
        获取用户存储使用情况
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: {
                'total_files': 文件总数,
                'total_size': 总大小（字节）,
                'total_size_mb': 总大小（MB）
            }
        """
        if isinstance(self._backend, LocalStorageBackend):
            user_dir = self._backend.base_dir / f"user_{user_id}"
            if not user_dir.exists():
                return {'total_files': 0, 'total_size': 0, 'total_size_mb': 0}
            
            total_size = 0
            total_files = 0
            
            for file_path in user_dir.iterdir():
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            return {
                'total_files': total_files,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        else:
            # OSS 需要通过API查询
            logger.warning("user_storage_usage_not_implemented_for_oss", user_id=user_id)
            return {'total_files': 0, 'total_size': 0, 'total_size_mb': 0}


# 全局存储服务实例
storage_service = StorageService()
