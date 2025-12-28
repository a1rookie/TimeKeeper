"""
Attachment API Endpoints
附件上传和管理的 API 端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from datetime import datetime
import structlog

from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.attachment import AttachmentUploadResponse
from app.services.storage_service import storage_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/attachments", tags=["Attachments"])

# 允许的文件类型
ALLOWED_MIME_TYPES = {
    # 文档
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    # 图片
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    # 其他
    "text/plain",
}


@router.post("/upload", response_model=ApiResponse[AttachmentUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    file: UploadFile = File(..., description="要上传的文件"),
    current_user: User = Depends(get_current_active_user)
) -> ApiResponse[AttachmentUploadResponse]:
    """
    Upload attachment file
    上传附件文件
    
    工作流程：
    1. 验证文件类型和大小
    2. 生成唯一文件ID
    3. 保存文件到服务器（或上传到云存储）
    4. 返回文件信息
    
    Returns:
        ApiResponse[AttachmentUploadResponse]: 文件上传结果
    """
    logger.info(
        "attachment_upload_request",
        user_id=current_user.id,
        filename=file.filename,
        content_type=file.content_type
    )
    
    # 1. 验证文件类型
    if file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(
            "attachment_upload_invalid_type",
            user_id=current_user.id,
            content_type=file.content_type,
            filename=file.filename
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}"
        )
    
    # 2. 读取文件内容并验证大小
    try:
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > settings.MAX_ATTACHMENT_SIZE:
            max_mb = settings.MAX_ATTACHMENT_SIZE // (1024 * 1024)
            logger.warning(
                "attachment_upload_too_large",
                user_id=current_user.id,
                file_size=file_size,
                max_size=settings.MAX_ATTACHMENT_SIZE,
                filename=file.filename
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制（最大 {max_mb}MB）"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件为空"
            )
        
    except Exception as e:
        logger.error(
            "attachment_upload_read_failed",
            user_id=current_user.id,
            error=str(e),
            filename=file.filename
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件读取失败"
        )
    
    # 3. 保存文件（使用存储服务，按用户隔离）
    try:
        file_id, file_url = await storage_service.save_file(
            file_content=file_content,
            file_name=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            user_id=current_user.id
        )
        
        logger.info(
            "attachment_uploaded",
            user_id=current_user.id,
            file_id=file_id,
            filename=file.filename,
            file_size=file_size,
            storage_type=settings.STORAGE_TYPE
        )
        
    except Exception as e:
        logger.error(
            "attachment_save_failed",
            user_id=current_user.id,
            error=str(e),
            filename=file.filename
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件保存失败"
        )
    
    # 4. 返回文件信息
    upload_response = AttachmentUploadResponse(
        file_id=file_id,
        file_name=file.filename or "unnamed",
        file_size=file_size,
        file_type=file.content_type or "application/octet-stream",
        file_url=file_url,
        uploaded_at=datetime.now()
    )
    
    return ApiResponse[AttachmentUploadResponse].success(
        data=upload_response,
        message="文件上传成功"
    )


@router.delete("/{file_id}", response_model=ApiResponse[None])
async def delete_attachment(
    file_id: str,
    current_user: User = Depends(get_current_active_user)
) -> ApiResponse[None]:
    """
    Delete attachment file
    删除附件文件
    
    注意：实际应该检查文件所有权，这里简化处理
    
    Returns:
        ApiResponse[None]: 删除结果
    """
    logger.info(
        "attachment_delete_request",
        user_id=current_user.id,
        file_id=file_id
    )
    
    # 删除文件（使用存储服务）
    try:
        success = await storage_service.delete_file(file_id)
        
        if not success:
            logger.warning(
                "attachment_delete_not_found",
                user_id=current_user.id,
                file_id=file_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        logger.info(
            "attachment_deleted",
            user_id=current_user.id,
            file_id=file_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "attachment_delete_failed",
            user_id=current_user.id,
            file_id=file_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件删除失败"
        )
    
    return ApiResponse[None].success(message="文件已删除")


@router.get("/storage/usage", response_model=ApiResponse[dict])
async def get_storage_usage(
    current_user: User = Depends(get_current_active_user)
) -> ApiResponse[dict]:
    """
    Get user's storage usage
    获取用户存储空间使用情况
    
    Returns:
        ApiResponse[dict]: 存储使用情况 {total_files, total_size, total_size_mb}
    """
    try:
        usage = await storage_service.get_user_storage_usage(current_user.id)
        
        logger.info(
            "storage_usage_queried",
            user_id=current_user.id,
            total_files=usage['total_files'],
            total_size_mb=usage['total_size_mb']
        )
        
        return ApiResponse[dict].success(
            data=usage,
            message=f"已使用 {usage['total_size_mb']}MB 存储空间"
        )
        
    except Exception as e:
        logger.error(
            "storage_usage_query_failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询存储使用情况失败"
        )
