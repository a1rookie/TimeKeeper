"""
NLU (Natural Language Understanding) Service
意图理解服务 - 使用 DeepSeek-V3 大模型解析用户意图
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class NLUError(Exception):
    """意图理解错误基类"""
    pass


class DeepSeekNLU:
    """DeepSeek 意图理解服务"""
    
    SYSTEM_PROMPT = """你是一个智能提醒助手，专门解析用户的提醒需求。

你的任务是将用户的自然语言输入转换为结构化的提醒信息。

返回 JSON 格式，包含以下字段：
{
    "title": "提醒标题（简洁描述）",
    "description": "详细描述（可选）",
    "category": "分类（rent/health/pet/finance/document/memorial/other）",
    "recurrence_type": "周期类型（once/daily/weekly/monthly/yearly）",
    "recurrence_config": {
        "interval": 1,  // 间隔（每N天/周/月/年）
        "weekdays": [],  // 周几（weekly时使用，1-7）
        "monthday": null,  // 每月几号（monthly时使用）
        "specific_date": null  // 具体日期（once/yearly时使用，YYYY-MM-DD）
    },
    "first_remind_time": "首次提醒时间（YYYY-MM-DD HH:MM:SS）",
    "advance_minutes": 0,  // 提前提醒分钟数
    "priority": "normal",  // 优先级（low/normal/high/urgent）
    "confidence": 0.95  // 识别置信度（0-1）
}

分类说明：
- rent: 房租、水电费、物业费等居住相关
- health: 吃药、体检、运动等健康相关
- pet: 宠物疫苗、洗澡、喂食等
- finance: 还款、缴费、理财到期等财务相关
- document: 证件到期、年检、续费等证件相关
- memorial: 生日、纪念日等
- other: 其他类型

周期类型说明：
- once: 单次提醒
- daily: 每天
- weekly: 每周（需指定weekdays）
- monthly: 每月（需指定monthday）
- yearly: 每年（需指定specific_date）

时间解析规则：
- "今天下午3点" -> 今天15:00
- "明天" -> 明天的当前时间
- "每周一" -> weekly, weekdays=[1]
- "每月5号" -> monthly, monthday=5
- "每年3月8日" -> yearly, specific_date="YYYY-03-08"
- "3天后" -> 3天后的当前时间

注意：
1. 如果用户没有明确时间，默认为今天的当前时间
2. 置信度低于0.7时，返回 "confidence": 0.5 并标注不确定的字段
3. 保持 JSON 格式严格正确，不要添加注释"""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL
        self.model = settings.DEEPSEEK_MODEL
    
    async def parse_intent(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        解析用户意图
        
        Args:
            user_input: 用户输入的自然语言
            context: 上下文信息（用户历史习惯等）
            
        Returns:
            解析后的结构化数据
        """
        if not self.api_key:
            raise NLUError("DeepSeek API Key 未配置")
        
        # 构建上下文提示
        context_prompt = ""
        if context:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            context_prompt = f"\n当前时间：{current_time}"
            if context.get("user_timezone"):
                context_prompt += f"\n用户时区：{context['user_timezone']}"
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"{context_prompt}\n\n用户输入：{user_input}"}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,  # 降低随机性，提高准确性
            "max_tokens": settings.DEEPSEEK_MAX_TOKENS,
            "response_format": {"type": "json_object"}  # 强制返回 JSON
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(
                "deepseek_nlu_request",
                user_input_length=len(user_input),
                has_context=context is not None,
                event="nlu_parse_start"
            )
            
            async with httpx.AsyncClient(timeout=settings.DEEPSEEK_TIMEOUT) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                parsed_data = json.loads(content)
                
                # 验证置信度
                confidence = parsed_data.get("confidence", 0.5)
                if confidence < settings.NLU_CONFIDENCE_THRESHOLD:
                    logger.warning(
                        "nlu_low_confidence",
                        confidence=confidence,
                        threshold=settings.NLU_CONFIDENCE_THRESHOLD,
                        user_input=user_input[:50],
                        event="nlu_low_confidence"
                    )
                
                logger.info(
                    "deepseek_nlu_success",
                    confidence=confidence,
                    category=parsed_data.get("category"),
                    recurrence_type=parsed_data.get("recurrence_type"),
                    tokens_used=result.get("usage", {}).get("total_tokens", 0),
                    event="nlu_parse_success"
                )
                
                return parsed_data
                
        except httpx.HTTPError as e:
            logger.error(
                "deepseek_nlu_http_error",
                error=str(e),
                status_code=getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
                event="nlu_http_error"
            )
            raise NLUError(f"DeepSeek API 请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(
                "deepseek_nlu_json_error",
                error=str(e),
                event="nlu_json_decode_error"
            )
            raise NLUError("DeepSeek 返回的 JSON 格式错误")
        except KeyError as e:
            logger.error(
                "deepseek_nlu_response_error",
                error=str(e),
                event="nlu_response_format_error"
            )
            raise NLUError("DeepSeek 响应格式异常")
        except Exception as e:
            logger.error(
                "deepseek_nlu_error",
                error=str(e),
                event="nlu_unknown_error"
            )
            raise NLUError(f"意图理解失败: {str(e)}")


class NLUService:
    """意图理解服务"""
    
    def __init__(self):
        self.deepseek = DeepSeekNLU() if settings.DEEPSEEK_ENABLED else None
    
    async def parse_reminder(self, text: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        解析提醒意图
        
        Args:
            text: 用户输入或语音识别的文本
            user_context: 用户上下文信息
            
        Returns:
            结构化的提醒数据
        """
        if not self.deepseek:
            raise NLUError("意图理解服务未启用，请配置 DEEPSEEK_API_KEY")
        
        # 清理文本
        text = text.strip()
        if not text:
            raise NLUError("输入文本为空")
        
        if len(text) > 500:
            logger.warning(
                "nlu_text_too_long",
                length=len(text),
                event="nlu_text_truncated"
            )
            text = text[:500]  # 截断过长文本
        
        # 调用 DeepSeek 解析
        parsed_data = await self.deepseek.parse_intent(text, user_context)
        
        # 后处理：验证和规范化
        validated_data = self._validate_and_normalize(parsed_data)
        
        return validated_data
    
    def _validate_and_normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证和规范化解析结果"""
        # 必填字段检查
        if not data.get("title"):
            raise NLUError("无法提取提醒标题")
        
        # 分类验证
        valid_categories = ["rent", "health", "pet", "finance", "document", "memorial", "other"]
        if data.get("category") not in valid_categories:
            data["category"] = "other"
        
        # 周期类型验证
        valid_recurrence = ["once", "daily", "weekly", "monthly", "yearly"]
        if data.get("recurrence_type") not in valid_recurrence:
            data["recurrence_type"] = "once"
        
        # 优先级验证
        valid_priorities = ["low", "normal", "high", "urgent"]
        if data.get("priority") not in valid_priorities:
            data["priority"] = "normal"
        
        # 时间验证
        if not data.get("first_remind_time"):
            # 默认为当前时间
            data["first_remind_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 提前提醒分钟数验证
        if not isinstance(data.get("advance_minutes"), int) or data["advance_minutes"] < 0:
            data["advance_minutes"] = 0
        
        return data


# 全局实例
_nlu_service: Optional[NLUService] = None


def get_nlu_service() -> NLUService:
    """获取意图理解服务实例"""
    global _nlu_service
    if _nlu_service is None:
        _nlu_service = NLUService()
    return _nlu_service
