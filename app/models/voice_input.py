"""
VoiceInput Model
语音输入记录模型
"""

from sqlalchemy import Column, BigInteger, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class VoiceInput(Base):
    """VoiceInput table - 语音输入记录表"""
    __tablename__ = "voice_inputs"
    
    id = Column(BigInteger, primary_key=True, index=True, comment="记录ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    audio_url = Column(String(255), nullable=True, comment="音频URL")
    recognized_text = Column(Text, nullable=True, comment="识别文本")
    parsed_result = Column(JSON, nullable=True, comment="解析结果JSON")
    is_successful = Column(Boolean, default=False, comment="是否成功")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # Relationships
    user = relationship("User", back_populates="voice_inputs")
