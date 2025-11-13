"""
ASR (Automatic Speech Recognition) Service
语音识别服务 - 支持科大讯飞和百度语音双重保障
"""
import base64
import hashlib
import hmac
import json
import time
from typing import Optional, Tuple
from datetime import datetime
import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ASRError(Exception):
    """语音识别错误基类"""
    pass


class XFYunASR:
    """科大讯飞语音识别（主力）"""
    
    def __init__(self):
        self.app_id = settings.XFYUN_APP_ID
        self.api_key = settings.XFYUN_API_KEY
        self.api_secret = settings.XFYUN_API_SECRET
        self.base_url = "https://api.xfyun.cn/v1/service/v1/iat"
    
    def _generate_signature(self, ts: str) -> str:
        """生成签名"""
        base_string = self.api_key + ts
        md5 = hashlib.md5(base_string.encode()).hexdigest()
        signature = hmac.new(
            self.api_secret.encode(),
            md5.encode(),
            hashlib.sha1
        ).digest()
        return base64.b64encode(signature).decode()
    
    async def recognize(self, audio_data: bytes, audio_format: str = "audio/L16;rate=16000") -> str:
        """
        识别语音
        
        Args:
            audio_data: 音频数据（PCM格式，16k采样率）
            audio_format: 音频格式
            
        Returns:
            识别的文本
        """
        if not self.app_id or not self.api_key or not self.api_secret:
            raise ASRError("科大讯飞配置未完成")
        
        ts = str(int(time.time()))
        signature = self._generate_signature(ts)
        
        headers = {
            "X-Appid": self.app_id,
            "X-CurTime": ts,
            "X-Param": base64.b64encode(json.dumps({
                "engine_type": "sms16k",
                "aue": "raw"
            }).encode()).decode(),
            "X-CheckSum": signature,
            "Content-Type": audio_format
        }
        
        try:
            async with httpx.AsyncClient(timeout=settings.ASR_TIMEOUT) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    content=audio_data
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get("code") != "0":
                    raise ASRError(f"科大讯飞识别失败: {result.get('desc', 'Unknown error')}")
                
                # 提取识别文本
                text = result.get("data", "")
                logger.info(
                    "xfyun_asr_success",
                    text_length=len(text),
                    audio_size=len(audio_data),
                    provider="xfyun"
                )
                return text
                
        except httpx.HTTPError as e:
            logger.error(
                "xfyun_asr_http_error",
                error=str(e),
                provider="xfyun"
            )
            raise ASRError(f"科大讯飞API请求失败: {str(e)}")
        except Exception as e:
            logger.error(
                "xfyun_asr_error",
                error=str(e),
                provider="xfyun"
            )
            raise ASRError(f"科大讯飞识别异常: {str(e)}")


class BaiduASR:
    """百度语音识别（备用）"""
    
    def __init__(self):
        self.app_id = settings.BAIDU_APP_ID
        self.api_key = settings.BAIDU_API_KEY
        self.secret_key = settings.BAIDU_SECRET_KEY
        self.token_url = "https://aip.baidubce.com/oauth/2.0/token"
        self.asr_url = "https://vop.baidu.com/server_api"
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def _get_access_token(self) -> str:
        """获取access token（带缓存）"""
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            self._access_token = result["access_token"]
            # Token有效期30天，提前1天刷新
            expires_in = result.get("expires_in", 2592000) - 86400
            self._token_expires_at = datetime.now().timestamp() + expires_in
            
            return self._access_token
    
    async def recognize(self, audio_data: bytes, rate: int = 16000) -> str:
        """
        识别语音
        
        Args:
            audio_data: 音频数据
            rate: 采样率
            
        Returns:
            识别的文本
        """
        if not self.api_key or not self.secret_key:
            raise ASRError("百度语音配置未完成")
        
        token = await self._get_access_token()
        
        data = {
            "format": "pcm",
            "rate": rate,
            "channel": 1,
            "cuid": settings.APP_NAME,
            "token": token,
            "speech": base64.b64encode(audio_data).decode(),
            "len": len(audio_data)
        }
        
        try:
            async with httpx.AsyncClient(timeout=settings.ASR_TIMEOUT) as client:
                response = await client.post(
                    self.asr_url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get("err_no") != 0:
                    raise ASRError(f"百度语音识别失败: {result.get('err_msg', 'Unknown error')}")
                
                # 提取识别文本
                text = "".join(result.get("result", []))
                logger.info(
                    "baidu_asr_success",
                    text_length=len(text),
                    audio_size=len(audio_data),
                    provider="baidu"
                )
                return text
                
        except httpx.HTTPError as e:
            logger.error(
                "baidu_asr_http_error",
                error=str(e),
                provider="baidu"
            )
            raise ASRError(f"百度语音API请求失败: {str(e)}")
        except Exception as e:
            logger.error(
                "baidu_asr_error",
                error=str(e),
                provider="baidu"
            )
            raise ASRError(f"百度语音识别异常: {str(e)}")


class ASRService:
    """语音识别服务（双重保障）"""
    
    def __init__(self):
        self.xfyun = XFYunASR() if settings.XFYUN_ENABLED else None
        self.baidu = BaiduASR() if settings.BAIDU_ENABLED else None
    
    async def recognize(self, audio_data: bytes, audio_format: str = "pcm") -> Tuple[str, str]:
        """
        识别语音（自动故障切换）
        
        Args:
            audio_data: 音频数据
            audio_format: 音频格式
            
        Returns:
            (识别文本, 使用的提供商)
        """
        # 检查音频大小
        if len(audio_data) > settings.ASR_MAX_AUDIO_SIZE:
            raise ASRError(f"音频文件过大，最大支持 {settings.ASR_MAX_AUDIO_SIZE / 1024 / 1024}MB")
        
        # 优先使用科大讯飞
        if self.xfyun:
            try:
                text = await self.xfyun.recognize(audio_data, audio_format)
                return text, "xfyun"
            except ASRError as e:
                logger.warning(
                    "xfyun_fallback_to_baidu",
                    reason=str(e),
                    event="asr_provider_switch"
                )
        
        # 降级到百度语音
        if self.baidu:
            try:
                text = await self.baidu.recognize(audio_data)
                return text, "baidu"
            except ASRError as e:
                logger.error(
                    "all_asr_providers_failed",
                    xfyun_available=self.xfyun is not None,
                    baidu_available=self.baidu is not None,
                    error=str(e),
                    event="asr_total_failure"
                )
                raise ASRError("所有语音识别服务均不可用")
        
        raise ASRError("未配置任何语音识别服务")


# 全局实例
_asr_service: Optional[ASRService] = None


def get_asr_service() -> ASRService:
    """获取语音识别服务实例"""
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service
