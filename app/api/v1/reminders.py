"""
Reminder API Endpoints
提醒相关的 API 端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import List, Optional
import structlog

from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.reminder import (
    ReminderCreate, 
    ReminderUpdate, 
    ReminderResponse,
    QuickReminderCreate
)
from app.schemas.reminder_completion import (
    ReminderCompletionCreate,
    ReminderCompletionResponse
)
from app.repositories import get_reminder_repository, get_reminder_completion_repository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.reminder_completion_repository import ReminderCompletionRepository
from app.services.push_task_service import create_push_task_for_reminder
from app.services.asr_service import get_asr_service, ASRError
from app.services.nlu_service import get_nlu_service, NLUError
from app.core.database import get_db
from app.core.recurrence import calculate_next_occurrence
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.post("/", response_model=ApiResponse[ReminderResponse], status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new reminder
    创建新提醒
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为创建的提醒
    """
    logger.info(
        "reminder_create_request",
        user_id=current_user.id,
        title=reminder_data.title,
        category=reminder_data.category,
        recurrence_type=reminder_data.recurrence_type,
        event="reminder_create_start"
    )
    
    # 使用Repository创建提醒
    new_reminder = await reminder_repo.create(
        user_id=current_user.id, 
        title=reminder_data.title,
        description=reminder_data.description,
        category=reminder_data.category,
        recurrence_type=reminder_data.recurrence_type,
        first_remind_time=reminder_data.first_remind_time,
        recurrence_config=reminder_data.recurrence_config,
        remind_channels=reminder_data.remind_channels,
        advance_minutes=reminder_data.advance_minutes,
        priority=reminder_data.priority,
        amount=reminder_data.amount,
        location=reminder_data.location,
        attachments=reminder_data.attachments
    )
    
    logger.info(
        "reminder_created",
        reminder_id=new_reminder.id,
        user_id=current_user.id,
        title=new_reminder.title,
        event="reminder_create_success"
    )
    
    return ApiResponse.success(data=new_reminder, message="创建成功")


@router.get("/", response_model=ApiResponse[List[ReminderResponse]])
async def get_reminders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository)
):
    """
    Get user's reminders
    获取用户的提醒列表
    
    Returns:
        ApiResponse[List[ReminderResponse]]: 统一响应格式，data 为提醒列表
    """
    reminders = await reminder_repo.get_user_reminders(
        user_id=current_user.id, 
        skip=skip,
        limit=limit,
        is_active=is_active
    )
    return ApiResponse.success(data=reminders)


@router.get("/{reminder_id}", response_model=ApiResponse[ReminderResponse])
async def get_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository)
):
    """
    Get reminder by ID
    获取提醒详情
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为提醒详情
    """
    reminder = await reminder_repo.get_by_id(reminder_id, current_user.id) 
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    return ApiResponse.success(data=reminder)


@router.put("/{reminder_id}", response_model=ApiResponse[ReminderResponse])
async def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository)
):
    """
    Update reminder
    更新提醒
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为更新后的提醒
    """
    reminder = await reminder_repo.get_by_id(reminder_id, current_user.id) 
    
    if not reminder:
        logger.warning(
            "reminder_update_not_found",
            reminder_id=reminder_id,
            user_id=current_user.id,
            event="reminder_update_not_found"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # Update fields
    update_data = reminder_data.model_dump(exclude_unset=True)
    logger.info(
        "reminder_update_request",
        reminder_id=reminder_id,
        user_id=current_user.id,
        updated_fields=list(update_data.keys()),
        event="reminder_update_start"
    )
    
    updated_reminder = await reminder_repo.update(reminder, **update_data)
    
    logger.info(
        "reminder_updated",
        reminder_id=reminder_id,
        user_id=current_user.id,
        event="reminder_update_success"
    )
    
    return ApiResponse.success(data=updated_reminder, message="更新成功")


@router.delete("/{reminder_id}", response_model=ApiResponse[None])
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository)
):
    """
    Delete reminder
    删除提醒
    
    Returns:
        ApiResponse[None]: 统一响应格式，data 为空
    """
    reminder = await reminder_repo.get_by_id(reminder_id, current_user.id) 
    
    if not reminder:
        logger.warning(
            "reminder_delete_not_found",
            reminder_id=reminder_id,
            user_id=current_user.id,
            event="reminder_delete_not_found"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    logger.info(
        "reminder_delete_request",
        reminder_id=reminder_id,
        user_id=current_user.id,
        title=reminder.title,
        event="reminder_delete_start"
    )
    
    await reminder_repo.delete(reminder)
    
    logger.info(
        "reminder_deleted",
        reminder_id=reminder_id,
        user_id=current_user.id,
        event="reminder_delete_success"
    )
    
    return ApiResponse.success(message="删除成功")


@router.post("/{reminder_id}/complete", response_model=ApiResponse[ReminderResponse])
async def complete_reminder(
    reminder_id: int,
    completion_data: Optional[ReminderCompletionCreate] = None,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    completion_repo: ReminderCompletionRepository = Depends(get_reminder_completion_repository),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark reminder as completed
    标记提醒为已完成
    
    业务逻辑：
    1. 标记提醒为已完成
    2. 记录完成记录到 reminder_completions 表
    3. 计算下次提醒时间
    4. 创建新的推送任务
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为更新后的提醒
    """
    # 1. 获取提醒
    reminder = await reminder_repo.get_by_id(reminder_id, current_user.id) 
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 2. 标记完成
    reminder = await reminder_repo.mark_completed(reminder, current_user.id) 
    
    # 3. 记录完成记录
    note = completion_data.note if completion_data else None
    await completion_repo.create(
        reminder_id=reminder.id, 
        user_id=current_user.id, 
        scheduled_time=reminder.next_remind_time, 
        note=note,
        status="completed"
    )
    
    # 4. 如果是周期性提醒，计算下次提醒时间
    if reminder.recurrence_type != "once": 
        next_time = calculate_next_occurrence(
            reminder.next_remind_time, 
            reminder.recurrence_type, 
            reminder.recurrence_config 
        )
        
        # 更新下次提醒时间，并重置完成状态
        reminder.next_remind_time = next_time 
        reminder.last_remind_time = reminder.completed_at 
        reminder.is_completed = False 
        reminder.completed_at = None 
        await db.commit()
        await db.refresh(reminder)
        
        # 5. 创建新的推送任务
        await create_push_task_for_reminder(db, reminder) 
    
    return ApiResponse.success(data=reminder, message="已标记为完成")


@router.post("/{reminder_id}/uncomplete", response_model=ApiResponse[ReminderResponse])
async def uncomplete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    completion_repo: ReminderCompletionRepository = Depends(get_reminder_completion_repository)
):
    """
    Mark reminder as uncompleted
    取消提醒完成状态
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为更新后的提醒
    """
    # 1. 获取提醒
    reminder = await reminder_repo.get_by_id(reminder_id, current_user.id) 
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 2. 取消完成状态
    reminder = await reminder_repo.mark_uncompleted(reminder)
    
    # 3. 删除最新的完成记录
    await completion_repo.delete_latest(reminder_id)
    
    return ApiResponse.success(data=reminder, message="已取消完成状态")


@router.get("/{reminder_id}/completions", response_model=ApiResponse[List[ReminderCompletionResponse]])
async def get_reminder_completions(
    reminder_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    completion_repo: ReminderCompletionRepository = Depends(get_reminder_completion_repository)
):
    """
    Get reminder completion history
    获取提醒完成历史记录
    
    Returns:
        ApiResponse[List[ReminderCompletionResponse]]: 统一响应格式，data 为完成记录列表
    """
    # 验证提醒所有权
    reminder = await reminder_repo.get_by_id(reminder_id, current_user.id) 
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在"
        )
    
    # 获取完成记录
    completions = await completion_repo.get_by_reminder(reminder_id, skip, limit)
    return ApiResponse.success(data=completions)


@router.post("/voice", response_model=ApiResponse[ReminderResponse], status_code=status.HTTP_201_CREATED)
async def create_voice_reminder(
    audio_file: UploadFile = File(..., description="音频文件（支持 PCM/WAV/MP3 等格式）"),
    user_id: Optional[int] = Form(None, description="用户ID（可选，从token获取）"),
    family_id: Optional[int] = Form(None, description="家庭ID（可选）"),
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    db: AsyncSession = Depends(get_db)
):
    """
    Create reminder from voice input
    从语音输入创建提醒
    
    工作流程：
    1. 接收音频文件
    2. 使用 ASR 服务（科大讯飞/百度）进行语音识别
    3. 使用 NLU 服务（DeepSeek-V3）进行意图理解
    4. 创建提醒记录
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为创建的提醒
    """
    # 记录请求
    logger.info(
        "voice_reminder_request",
        user_id=current_user.id,
        filename=audio_file.filename,
        content_type=audio_file.content_type,
        event="voice_reminder_start"
    )
    
    try:
        # 读取音频数据
        audio_data = await audio_file.read()
        audio_size = len(audio_data)
        
        logger.info(
            "voice_reminder_audio_received",
            audio_size=audio_size,
            event="audio_received"
        )
        
        # 1. 语音识别（ASR）
        try:
            asr_service = get_asr_service()
            text, provider = await asr_service.recognize(audio_data)
            
            logger.info(
                "voice_reminder_asr_complete",
                text=text[:100],  # 只记录前100字符
                text_length=len(text),
                provider=provider,
                audio_size=audio_size,
                event="asr_complete"
            )
        except ASRError as e:
            logger.error(
                "voice_reminder_asr_failed",
                error=str(e),
                audio_size=audio_size,
                event="asr_failed"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"语音识别失败: {str(e)}"
            )
        
        # 2. 意图理解（NLU）
        try:
            nlu_service = get_nlu_service()
            user_context = {
                "user_timezone": "Asia/Shanghai",  # 可从用户配置读取
                "user_id": current_user.id
            }
            parsed_intent = await nlu_service.parse_reminder(text, user_context)
            
            logger.info(
                "voice_reminder_nlu_complete",
                confidence=parsed_intent.get("confidence"),
                category=parsed_intent.get("category"),
                recurrence_type=parsed_intent.get("recurrence_type"),
                event="nlu_complete"
            )
        except NLUError as e:
            logger.error(
                "voice_reminder_nlu_failed",
                error=str(e),
                text=text[:100],
                event="nlu_failed"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"意图理解失败: {str(e)}"
            )
        
        # 3. 构建 ReminderCreate 对象
        reminder_data = ReminderCreate(
            title=parsed_intent["title"],
            description=parsed_intent.get("description"),
            category=parsed_intent.get("category", "other"),
            recurrence_type=parsed_intent.get("recurrence_type", "once"),
            recurrence_config=parsed_intent.get("recurrence_config", {}),
            first_remind_time=parsed_intent["first_remind_time"],
            advance_minutes=parsed_intent.get("advance_minutes", 0),
            priority=parsed_intent.get("priority", 1),
            amount=parsed_intent.get("amount"),
            location=parsed_intent.get("location"),
            attachments=parsed_intent.get("attachments")
        )
        
        # 4. 创建提醒（使用依赖注入的 reminder_repo）
        new_reminder = await reminder_repo.create(
            user_id=int(user_id) if user_id else int(current_user.id),  
            title=reminder_data.title,
            description=reminder_data.description,
            category=reminder_data.category,
            first_remind_time=reminder_data.first_remind_time,
            recurrence_type=reminder_data.recurrence_type,
            recurrence_config=reminder_data.recurrence_config,
            remind_channels=reminder_data.remind_channels,
            advance_minutes=reminder_data.advance_minutes,
            priority=reminder_data.priority,
            amount=reminder_data.amount,
            location=reminder_data.location,
            attachments=reminder_data.attachments
        )
        
        logger.info(
            "voice_reminder_created",
            reminder_id=new_reminder.id,
            user_id=new_reminder.user_id,
            title=new_reminder.title,
            confidence=parsed_intent.get("confidence"),
            provider=provider,
            event="voice_reminder_success"
        )
        
        return ApiResponse.success(
            data=ReminderResponse.model_validate(new_reminder),
            message=f"语音提醒创建成功（识别置信度: {parsed_intent.get('confidence', 'N/A')}）"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "voice_reminder_error",
            error=str(e),
            user_id=current_user.id,
            event="voice_reminder_error"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建语音提醒失败: {str(e)}"
        )


@router.post("/quick", response_model=ApiResponse[ReminderResponse], status_code=status.HTTP_201_CREATED)
async def create_quick_reminder(
    quick_data: QuickReminderCreate,
    current_user: User = Depends(get_current_active_user),
    reminder_repo: ReminderRepository = Depends(get_reminder_repository),
    db: AsyncSession = Depends(get_db)
):
    """
    Create reminder from template
    从模板快速创建提醒
    
    支持两种模板类型：
    1. 系统模板（template_id 格式: "system_<id>"）
    2. 用户自定义模板（template_id 格式: "custom_<id>"）
    
    自定义数据可覆盖模板默认值：
    - title: 提醒标题
    - description: 提醒描述
    - first_remind_time: 首次提醒时间（必填）
    - advance_minutes: 提前提醒分钟数
    - priority: 优先级
    
    Returns:
        ApiResponse[ReminderResponse]: 统一响应格式，data 为创建的提醒
    """
    logger.info(
        "quick_reminder_request",
        template_id=quick_data.template_id,
        user_id=current_user.id,
        has_custom_data=bool(quick_data.custom_data),
        event="quick_reminder_start"
    )
    
    try:
        # 解析模板类型和ID
        template_parts = quick_data.template_id.split("_", 1)
        if len(template_parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模板ID格式错误，应为 system_<id> 或 custom_<id>"
            )
        
        template_type, template_id_str = template_parts
        
        try:
            template_id = int(template_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模板ID必须为数字"
            )
        
        # 获取模板
        template = None
        if template_type == "system":
            from app.repositories.reminder_template_repository import ReminderTemplateRepository
            template_repo = ReminderTemplateRepository(db)
            template = await template_repo.get_by_id(template_id)
            
            if not template or not template.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="系统模板不存在或已禁用"
                )
            
            # 增加使用次数
            await template_repo.increment_usage(template_id)
            
        elif template_type == "custom":
            from app.repositories.user_custom_template_repository import UserCustomTemplateRepository
            custom_template_repo = UserCustomTemplateRepository(db)
            template = await custom_template_repo.get_by_id(template_id)
            
            if not template or not template.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="自定义模板不存在或已禁用"
                )
            
            # 验证权限（仅创建者或家庭成员可使用）
            template_user_id = int(template.user_id)  
            user_id = int(current_user.id)  
            if template_user_id != user_id:
                # 检查是否为共享模板
                from app.repositories.template_share_repository import TemplateShareRepository
                share_repo = TemplateShareRepository(db)
                can_use = await share_repo.can_user_access_template(template_id, user_id)
                
                if not can_use:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权使用此模板"
                    )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模板类型错误，必须为 system 或 custom"
            )
        
        logger.info(
            "quick_reminder_template_loaded",
            template_id=quick_data.template_id,
            template_name=template.name,
            template_type=template_type,
            event="template_loaded"
        )
        
        # 构建提醒数据（优先使用自定义数据）
        custom_data = quick_data.custom_data or {}
        
        # 首次提醒时间必须提供
        if "first_remind_time" not in custom_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供 first_remind_time（首次提醒时间）"
            )
        
        from app.models.reminder import ReminderCategory
        
        template_name = str(template.name)  
        template_desc = str(template.description) if hasattr(template, 'description') and template.description else None  
        template_category_str = str(template.category)  
        template_category = ReminderCategory(template_category_str)
        
        reminder_data = ReminderCreate(
            title=custom_data.get("title", template_name),
            description=custom_data.get("description", template_desc),
            category=template_category,
            recurrence_type=custom_data.get(
                "recurrence_type",
                getattr(template, "default_recurrence_type", "once")
            ),
            recurrence_config=custom_data.get(
                "recurrence_config",
                getattr(template, "default_recurrence_config", {})
            ),
            first_remind_time=custom_data["first_remind_time"],
            advance_minutes=custom_data.get(
                "advance_minutes",
                getattr(template, "default_remind_advance_days", 0) * 24 * 60
            ),
            priority=custom_data.get("priority", 1),
            remind_channels=custom_data.get("remind_channels", ["app"]),
            amount=custom_data.get("amount"),
            location=custom_data.get("location"),
            attachments=custom_data.get("attachments")
        )
        
        # 创建提醒（使用依赖注入的 reminder_repo）
        user_id = int(current_user.id)  
        
        new_reminder = await reminder_repo.create(
            user_id=user_id,
            title=reminder_data.title,
            description=reminder_data.description,
            category=reminder_data.category,
            first_remind_time=reminder_data.first_remind_time,
            recurrence_type=reminder_data.recurrence_type,
            recurrence_config=reminder_data.recurrence_config,
            remind_channels=reminder_data.remind_channels,
            advance_minutes=reminder_data.advance_minutes,
            priority=reminder_data.priority,
            amount=reminder_data.amount,
            location=reminder_data.location,
            attachments=reminder_data.attachments
        )
        
        logger.info(
            "quick_reminder_created",
            reminder_id=new_reminder.id,
            template_id=quick_data.template_id,
            template_name=template.name,
            user_id=current_user.id,
            event="quick_reminder_success"
        )
        
        return ApiResponse.success(
            data=ReminderResponse.model_validate(new_reminder),
            message=f"从模板「{template.name}」创建提醒成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "quick_reminder_error",
            error=str(e),
            template_id=quick_data.template_id,
            user_id=current_user.id,
            event="quick_reminder_error"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"从模板创建提醒失败: {str(e)}"
        )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="模板功能待实现"
    )
