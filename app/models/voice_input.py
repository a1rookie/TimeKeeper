"""
Voice Input Model
语音输入记录模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class VoiceInput(Base):
    """语音输入记录表"""
    __tablename__ = "voice_inputs"
    
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    audio_url = Column(String(255), comment="音频文件URL")
    recognized_text = Column(Text, comment="识别文本")
    parsed_result = Column(JSON, comment="解析结果(JSON)")
    is_successful = Column(Boolean, default=False, comment="是否成功")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # Relationships
    user = relationship("User", back_populates="voice_inputs")
