"""
Attachment Schemas
附件相关的 Pydantic 模型
"""

from pydantic import BaseModel, Field
from datetime import datetime


class AttachmentUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str = Field(..., description="文件唯一ID")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="MIME类型")
    file_url: str = Field(..., description="文件访问URL")
    uploaded_at: datetime = Field(..., description="上传时间")


class AttachmentInfo(BaseModel):
    """附件信息（用于提醒中的附件字段）"""
    file_id: str = Field(..., description="文件ID")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="MIME类型")
    file_url: str = Field(..., description="访问URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_name": "合同.pdf",
                "file_size": 1024000,
                "file_type": "application/pdf",
                "file_url": "https://cdn.example.com/files/550e8400.pdf"
            }
        }
