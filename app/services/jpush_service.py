"""
JPush Service - 极光推送服务封装
官方文档: https://docs.jiguang.cn/jpush/server/push/rest_api_v3_push
"""

import requests
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class JPushClient:
    """
    极光推送客户端
    """
    
    BASE_URL = "https://api.jpush.cn/v3"
    
    def __init__(self, app_key: str = None, master_secret: str = None):
        """
        初始化极光推送客户端
        
        Args:
            app_key: 应用Key
            master_secret: 主密钥
        """
        self.app_key = app_key or settings.JPUSH_APP_KEY
        self.master_secret = master_secret or settings.JPUSH_MASTER_SECRET
        
        if not self.app_key or not self.master_secret:
            logger.warning("JPush credentials not configured")
        
        self.auth = (self.app_key, self.master_secret)
    
    def push_to_user(
        self,
        user_id: str,
        title: str,
        content: str,
        extras: Optional[Dict[str, Any]] = None,
        badge: int = 1
    ) -> Dict[str, Any]:
        """
        向指定用户推送消息
        
        Args:
            user_id: 用户ID（别名）
            title: 通知标题
            content: 通知内容
            extras: 额外数据
            badge: iOS角标数
            
        Returns:
            推送结果
        """
        payload = {
            "platform": ["android", "ios"],
            "audience": {
                "alias": [str(user_id)]
            },
            "notification": {
                "alert": content,
                "android": {
                    "alert": content,
                    "title": title,
                    "extras": extras or {}
                },
                "ios": {
                    "alert": content,
                    "badge": badge,
                    "extras": extras or {}
                }
            },
            "options": {
                "apns_production": not settings.DEBUG  # 生产环境使用生产证书
            }
        }
        
        return self._send_push(payload)
    
    def push_to_all(
        self,
        title: str,
        content: str,
        extras: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        向所有用户推送消息（广播）
        
        Args:
            title: 通知标题
            content: 通知内容
            extras: 额外数据
            
        Returns:
            推送结果
        """
        payload = {
            "platform": "all",
            "audience": "all",
            "notification": {
                "alert": content,
                "android": {
                    "alert": content,
                    "title": title,
                    "extras": extras or {}
                },
                "ios": {
                    "alert": content,
                    "badge": 1,
                    "extras": extras or {}
                }
            },
            "options": {
                "apns_production": not settings.DEBUG
            }
        }
        
        return self._send_push(payload)
    
    def push_to_tags(
        self,
        tags: List[str],
        title: str,
        content: str,
        extras: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        向指定标签的用户推送消息
        
        Args:
            tags: 标签列表
            title: 通知标题
            content: 通知内容
            extras: 额外数据
            
        Returns:
            推送结果
        """
        payload = {
            "platform": ["android", "ios"],
            "audience": {
                "tag": tags
            },
            "notification": {
                "alert": content,
                "android": {
                    "alert": content,
                    "title": title,
                    "extras": extras or {}
                },
                "ios": {
                    "alert": content,
                    "badge": 1,
                    "extras": extras or {}
                }
            },
            "options": {
                "apns_production": not settings.DEBUG
            }
        }
        
        return self._send_push(payload)
    
    def _send_push(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送推送请求
        
        Args:
            payload: 推送负载
            
        Returns:
            推送结果
        """
        url = f"{self.BASE_URL}/push"
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Sending push to JPush: {json.dumps(payload, ensure_ascii=False)}")
            
            response = requests.post(
                url,
                auth=self.auth,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            result = response.json()
            
            if response.status_code == 200:
                logger.info(f"Push sent successfully: {result}")
                return {
                    "success": True,
                    "msg_id": result.get("msg_id"),
                    "sendno": result.get("sendno"),
                    "response": result
                }
            else:
                logger.error(f"Push failed: {response.status_code} - {result}")
                return {
                    "success": False,
                    "error": result.get("error", {}).get("message", "Unknown error"),
                    "error_code": result.get("error", {}).get("code"),
                    "response": result
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Push request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "NETWORK_ERROR"
            }
        except Exception as e:
            logger.error(f"Unexpected error during push: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "UNKNOWN_ERROR"
            }
    
    def set_alias(self, registration_id: str, alias: str) -> Dict[str, Any]:
        """
        设置设备别名（用户ID）
        
        Args:
            registration_id: 设备的注册ID
            alias: 别名（通常是用户ID）
            
        Returns:
            设置结果
        """
        url = f"{self.BASE_URL}/devices/{registration_id}"
        payload = {
            "alias": alias
        }
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return {"success": True}
            else:
                result = response.json()
                return {
                    "success": False,
                    "error": result.get("error", {}).get("message", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Set alias failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_credentials(self) -> bool:
        """
        验证推送凭证是否有效
        
        Returns:
            是否有效
        """
        if not self.app_key or not self.master_secret:
            return False
        
        # 尝试获取应用信息来验证凭证
        url = f"{self.BASE_URL}/push/validate"
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                json={
                    "platform": "all",
                    "audience": "all",
                    "notification": {
                        "alert": "test"
                    }
                },
                timeout=10
            )
            
            return response.status_code == 200
        except Exception:
            return False


# 单例客户端
_jpush_client: Optional[JPushClient] = None


def get_jpush_client() -> JPushClient:
    """
    获取极光推送客户端单例
    """
    global _jpush_client
    if _jpush_client is None:
        _jpush_client = JPushClient()
    return _jpush_client


# 便捷函数
def push_reminder_notification(
    user_id: int,
    reminder_id: int,
    title: str,
    content: str
) -> Dict[str, Any]:
    """
    推送提醒通知
    
    Args:
        user_id: 用户ID
        reminder_id: 提醒ID
        title: 标题
        content: 内容
        
    Returns:
        推送结果
    """
    if not settings.JPUSH_ENABLED:
        logger.info("JPush is disabled, skip push")
        return {
            "success": False,
            "error": "JPush is disabled",
            "error_code": "DISABLED"
        }
    
    client = get_jpush_client()
    
    extras = {
        "reminder_id": reminder_id,
        "type": "reminder",
        "timestamp": datetime.now().isoformat()
    }
    
    return client.push_to_user(
        user_id=str(user_id),
        title=title,
        content=content,
        extras=extras
    )
