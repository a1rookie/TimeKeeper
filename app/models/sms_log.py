"""
SMS Log Model
短信日志模型 - 用于审计、防刷和数据分析
"""
from datetime import datetime
from sqlalchemy import String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SmsLog(Base):
    """短信发送日志表"""
    __tablename__ = "sms_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="日志ID")
    phone: Mapped[str] = mapped_column(String(20), index=True, comment="接收手机号")
    purpose: Mapped[str] = mapped_column(String(20), index=True, comment="用途: register, reset, verify")
    code: Mapped[str] = mapped_column(String(10), comment="验证码（加密或脱敏存储）")
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="请求IP地址")
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True, comment="用户代理")
    
    # 发送状态
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="状态: pending, sent, failed")
    provider: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="短信提供商: aliyun, noop")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    
    # 验证状态
    is_verified: Mapped[bool] = mapped_column(default=False, comment="是否已验证")
    verified_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="验证时间")
    verify_attempts: Mapped[int] = mapped_column(default=0, comment="尝试验证次数")
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True, comment="创建时间")
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="发送时间")
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True, index=True, comment="过期时间")
    
    # 索引优化
    __table_args__ = (
        Index('idx_phone_purpose_created', 'phone', 'purpose', 'created_at'),
        Index('idx_ip_created', 'ip_address', 'created_at'),
    )
