"""
Session Management Service
会话管理服务 - 实现单点登录/互踢机制
"""
from typing import Literal
from datetime import datetime, timedelta, UTC
from redis import Redis
from app.core.config import settings

# 设备类型定义
DeviceType = Literal["web", "ios", "android", "desktop"]


class SessionManager:
    """会话管理器"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.session_prefix = "user_session"
        self.blacklist_prefix = "token_blacklist"
        self.session_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 秒
        self.blacklist_ttl = self.session_ttl + 3600  # 黑名单保留时间多1小时
    
    def _get_session_key(self, user_id: int, device_type: DeviceType) -> str:
        """生成会话键"""
        return f"{self.session_prefix}:{user_id}:{device_type}"
    
    def _get_blacklist_key(self, jti: str) -> str:
        """生成黑名单键"""
        return f"{self.blacklist_prefix}:{jti}"
    
    def create_session(
        self,
        user_id: int,
        device_type: DeviceType,
        jti: str,
        kick_previous: bool = True
    ) -> str | None:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            device_type: 设备类型
            jti: JWT唯一标识符
            kick_previous: 是否踢掉之前的会话
            
        Returns:
            被踢掉的旧token的jti，如果没有则返回None
        """
        session_key = self._get_session_key(user_id, device_type)
        
        # 获取旧会话
        old_jti = None
        if kick_previous:
            old_jti_raw = self.redis.get(session_key)
            if old_jti_raw:
                old_jti = old_jti_raw.decode('utf-8') if isinstance(old_jti_raw, bytes) else str(old_jti_raw)
                # 将旧token加入黑名单
                self._add_to_blacklist(old_jti, f"被新登录踢出 - 设备类型: {device_type}")
        
        # 存储新会话
        self.redis.setex(
            session_key,
            self.session_ttl,
            jti
        )
        
        return old_jti
    
    def _add_to_blacklist(self, jti: str, reason: str = ""):
        """将token加入黑名单"""
        blacklist_key = self._get_blacklist_key(jti)
        self.redis.setex(
            blacklist_key,
            self.blacklist_ttl,
            reason or "token revoked"
        )
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """检查token是否在黑名单中"""
        blacklist_key = self._get_blacklist_key(jti)
        return bool(self.redis.exists(blacklist_key))
    
    def is_active_session(self, user_id: int, device_type: DeviceType, jti: str) -> bool:
        """
        检查是否为活跃会话
        
        Args:
            user_id: 用户ID
            device_type: 设备类型
            jti: 当前token的jti
            
        Returns:
            True表示是活跃会话，False表示已被踢出
        """
        session_key = self._get_session_key(user_id, device_type)
        current_jti = self.redis.get(session_key)
        
        if not current_jti:
            # 会话不存在，可能过期了
            return False
        
        current_jti = current_jti.decode('utf-8') if isinstance(current_jti, bytes) else current_jti
        
        # 检查是否为当前活跃的jti
        return current_jti == jti
    
    def revoke_session(self, user_id: int, device_type: DeviceType) -> bool:
        """
        撤销指定设备的会话（登出）
        
        Args:
            user_id: 用户ID
            device_type: 设备类型
            
        Returns:
            是否成功撤销
        """
        session_key = self._get_session_key(user_id, device_type)
        jti_raw = self.redis.get(session_key)
        
        if jti_raw:
            jti = jti_raw.decode('utf-8') if isinstance(jti_raw, bytes) else str(jti_raw)
            # 加入黑名单
            self._add_to_blacklist(jti, "用户主动登出")
            # 删除会话
            self.redis.delete(session_key)
            return True
        
        return False
    
    def revoke_all_sessions(self, user_id: int) -> int:
        """
        撤销用户的所有会话（全局登出）
        
        Args:
            user_id: 用户ID
            
        Returns:
            撤销的会话数量
        """
        device_types: list[DeviceType] = ["web", "ios", "android", "desktop"]
        revoked_count = 0
        
        for device_type in device_types:
            if self.revoke_session(user_id, device_type):
                revoked_count += 1
        
        return revoked_count
    
    def get_active_sessions(self, user_id: int) -> dict[DeviceType, dict]:
        """
        获取用户的所有活跃会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            设备类型 -> 会话信息的字典
        """
        device_types: list[DeviceType] = ["web", "ios", "android", "desktop"]
        active_sessions = {}
        
        for device_type in device_types:
            session_key = self._get_session_key(user_id, device_type)
            jti_raw = self.redis.get(session_key)
            
            if jti_raw:
                jti = jti_raw.decode('utf-8') if isinstance(jti_raw, bytes) else str(jti_raw)
                ttl_raw = self.redis.ttl(session_key)  # type: ignore
                ttl = int(ttl_raw) if ttl_raw is not None else 0  # type: ignore
                active_sessions[device_type] = {
                    "jti": jti,
                    "expires_in_seconds": ttl,
                    "last_activity": datetime.now(UTC) - timedelta(seconds=self.session_ttl - ttl)
                }
        
        return active_sessions
    
    def extend_session(self, user_id: int, device_type: DeviceType) -> bool:
        """
        延长会话时间（用户活跃时调用）
        
        Args:
            user_id: 用户ID
            device_type: 设备类型
            
        Returns:
            是否成功延长
        """
        session_key = self._get_session_key(user_id, device_type)
        
        # 重新设置过期时间
        if self.redis.exists(session_key):
            self.redis.expire(session_key, self.session_ttl)
            return True
        
        return False


# 全局会话管理器实例（需要在应用启动时初始化）
_session_manager: SessionManager | None = None


def init_session_manager(redis_client: Redis):
    """初始化会话管理器"""
    global _session_manager
    _session_manager = SessionManager(redis_client)


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    if _session_manager is None:
        raise RuntimeError("会话管理器未初始化，请先调用 init_session_manager()")
    return _session_manager
