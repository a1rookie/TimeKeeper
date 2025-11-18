"""
Voice Input Model
语音输入记录模型
"""
from typing import Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class VoiceInput(Base):
    """语音输入记录表"""
    __tablename__ = "voice_inputs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="记录ID")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment="用户ID")
    audio_url: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="音频文件URL")
    recognized_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="识别文本")
    parsed_result: Mapped[Dict[str, Any] | None] = mapped_column(type_=JSON, nullable=True, comment="解析结果(JSON)")
    is_successful: Mapped[bool] = mapped_column(default=False, comment="是否成功")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), comment="创建时间")
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="voice_inputs")
