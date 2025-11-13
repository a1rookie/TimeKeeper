"""
SMS Log Model
短信日志模型 - 用于审计、防刷和数据分析
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index
from sqlalchemy.sql import func
from app.core.database import Base


class SmsLog(Base):
    """短信发送日志表"""
    __tablename__ = "sms_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    phone = Column(String(20), nullable=False, index=True, comment="接收手机号")
    purpose = Column(String(20), nullable=False, index=True, comment="用途: register, reset, verify")
    code = Column(String(10), nullable=False, comment="验证码（加密或脱敏存储）")
    ip_address = Column(String(50), comment="请求IP地址")
    user_agent = Column(Text, comment="用户代理")
    
    # 发送状态
    status = Column(String(20), nullable=False, default="pending", comment="状态: pending, sent, failed")
    provider = Column(String(20), comment="短信提供商: aliyun, noop")
    error_message = Column(Text, comment="错误信息")
    
    # 验证状态
    is_verified = Column(Boolean, default=False, comment="是否已验证")
    verified_at = Column(DateTime(timezone=True), comment="验证时间")
    verify_attempts = Column(Integer, default=0, comment="尝试验证次数")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="创建时间")
    sent_at = Column(DateTime(timezone=True), comment="发送时间")
    expires_at = Column(DateTime(timezone=True), index=True, comment="过期时间")
    
    # 索引优化
    __table_args__ = (
        Index('idx_phone_purpose_created', 'phone', 'purpose', 'created_at'),
        Index('idx_ip_created', 'ip_address', 'created_at'),
    )
