"""
Template API
模板系统的 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.template_share import ShareType
from app.schemas.template import (
    ReminderTemplateResponse,
    UserCustomTemplateCreate,
    UserCustomTemplateUpdate,
    UserCustomTemplateResponse,
    TemplateShareCreate,
    TemplateShareResponse,
    TemplateShareDetail,
    TemplateUsageCreate,
    TemplateUsageResponse,
    TemplateLikeResponse
)
from app.repositories.reminder_template_repository import ReminderTemplateRepository
from app.repositories.user_custom_template_repository import UserCustomTemplateRepository
from app.repositories.template_share_repository import TemplateShareRepository
from app.repositories.template_usage_record_repository import TemplateUsageRecordRepository
from app.repositories.template_like_repository import TemplateLikeRepository
from app.repositories.family_member_repository import FamilyMemberRepository

router = APIRouter()


# ==================== 系统模板 ====================

@router.get("/templates/system", response_model=List[ReminderTemplateResponse])
def list_system_templates(
    category: Optional[str] = Query(None, description="按分类筛选"),
    db: Session = Depends(get_db)
):
    """
    获取系统模板列表
    - 可按分类筛选
    - 按使用次数排序
    """
    template_repo = ReminderTemplateRepository(db)
    
    if category:
        templates = template_repo.get_by_category(category)
    else:
        templates = template_repo.get_all_active()
    
    return [
        ReminderTemplateResponse(
            id=t.id,
            name=t.name,
            category=t.category,
            description=t.description,
            default_recurrence_type=t.default_recurrence_type,
            default_recurrence_config=t.default_recurrence_config,
            default_remind_advance_days=t.default_remind_advance_days,
            usage_count=t.usage_count,
            is_active=t.is_active,
            created_at=t.created_at
        ) for t in templates
    ]


@router.get("/templates/system/{template_id}", response_model=ReminderTemplateResponse)
def get_system_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """获取系统模板详情"""
    template_repo = ReminderTemplateRepository(db)
    template = template_repo.get_by_id(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统模板不存在"
        )
    
    return ReminderTemplateResponse(
        id=template.id,
        name=template.name,
        category=template.category,
        description=template.description,
        default_recurrence_type=template.default_recurrence_type,
        default_recurrence_config=template.default_recurrence_config,
        default_remind_advance_days=template.default_remind_advance_days,
        usage_count=template.usage_count,
        is_active=template.is_active,
        created_at=template.created_at
    )


@router.get("/templates/system/popular", response_model=List[ReminderTemplateResponse])
def get_popular_templates(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取热门系统模板"""
    template_repo = ReminderTemplateRepository(db)
    templates = template_repo.get_popular(limit=limit)
    
    return [
        ReminderTemplateResponse(
            id=t.id,
            name=t.name,
            category=t.category,
            description=t.description,
            default_recurrence_type=t.default_recurrence_type,
            default_recurrence_config=t.default_recurrence_config,
            default_remind_advance_days=t.default_remind_advance_days,
            usage_count=t.usage_count,
            is_active=t.is_active,
            created_at=t.created_at
        ) for t in templates
    ]


# ==================== 用户自定义模板 ====================

@router.post("/templates/custom", response_model=UserCustomTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_custom_template(
    data: UserCustomTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建用户自定义模板
    - 可以基于系统模板创建
    """
    template_repo = UserCustomTemplateRepository(db)
    
    # 检查名称是否重复
    existing = template_repo.get_by_user_and_name(current_user.id, data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该模板名称已存在"
        )
    
    # 如果基于系统模板，增加系统模板使用次数
    if data.created_from_template_id:
        system_template_repo = ReminderTemplateRepository(db)
        system_template_repo.increment_usage(data.created_from_template_id)
    
    template = template_repo.create(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        recurrence_type=data.recurrence_type,
        recurrence_config=data.recurrence_config,
        remind_advance_days=data.remind_advance_days,
        created_from_template_id=data.created_from_template_id
    )
    
    return UserCustomTemplateResponse(
        id=template.id,
        user_id=template.user_id,
        name=template.name,
        description=template.description,
        recurrence_type=template.recurrence_type,
        recurrence_config=template.recurrence_config,
        remind_advance_days=template.remind_advance_days,
        created_from_template_id=template.created_from_template_id,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.get("/templates/custom", response_model=List[UserCustomTemplateResponse])
def list_my_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的自定义模板列表"""
    template_repo = UserCustomTemplateRepository(db)
    templates = template_repo.get_user_templates(current_user.id)
    
    return [
        UserCustomTemplateResponse(
            id=t.id,
            user_id=t.user_id,
            name=t.name,
            description=t.description,
            recurrence_type=t.recurrence_type,
            recurrence_config=t.recurrence_config,
            remind_advance_days=t.remind_advance_days,
            created_from_template_id=t.created_from_template_id,
            created_at=t.created_at,
            updated_at=t.updated_at
        ) for t in templates
    ]


@router.put("/templates/custom/{template_id}", response_model=UserCustomTemplateResponse)
def update_custom_template(
    template_id: int,
    data: UserCustomTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户自定义模板"""
    template_repo = UserCustomTemplateRepository(db)
    
    template = template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改该模板"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    updated_template = template_repo.update(template_id, **update_data)
    
    return UserCustomTemplateResponse(
        id=updated_template.id,
        user_id=updated_template.user_id,
        name=updated_template.name,
        description=updated_template.description,
        recurrence_type=updated_template.recurrence_type,
        recurrence_config=updated_template.recurrence_config,
        remind_advance_days=updated_template.remind_advance_days,
        created_from_template_id=updated_template.created_from_template_id,
        created_at=updated_template.created_at,
        updated_at=updated_template.updated_at
    )


@router.delete("/templates/custom/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户自定义模板"""
    template_repo = UserCustomTemplateRepository(db)
    
    template = template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该模板"
        )
    
    template_repo.delete(template_id)
    return None


# ==================== 模板分享 ====================

@router.post("/templates/share", response_model=TemplateShareResponse, status_code=status.HTTP_201_CREATED)
def share_template(
    data: TemplateShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分享模板
    - 支持公开分享、家庭分享、链接分享
    """
    custom_template_repo = UserCustomTemplateRepository(db)
    share_repo = TemplateShareRepository(db)
    
    # 检查模板是否存在且属于当前用户
    template = custom_template_repo.get_by_id(data.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权分享该模板"
        )
    
    # 如果是家庭分享，检查家庭组权限
    if data.share_type == ShareType.FAMILY:
        if not data.family_group_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="家庭分享需要指定家庭组ID"
            )
        
        member_repo = FamilyMemberRepository(db)
        if not member_repo.is_member(data.family_group_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不是该家庭组成员"
            )
    
    # 创建分享
    share = share_repo.create(
        template_id=data.template_id,
        user_id=current_user.id,
        share_type=data.share_type,
        share_title=data.share_title,
        share_description=data.share_description,
        family_group_id=data.family_group_id
    )
    
    return TemplateShareResponse(
        id=share.id,
        template_id=share.template_id,
        user_id=share.user_id,
        share_type=share.share_type,
        share_code=share.share_code,
        share_title=share.share_title,
        share_description=share.share_description,
        family_group_id=share.family_group_id,
        usage_count=share.usage_count,
        like_count=share.like_count,
        is_active=share.is_active,
        created_at=share.created_at,
        owner_nickname=current_user.nickname,
        template_name=template.name
    )


@router.get("/templates/share/public", response_model=List[TemplateShareResponse])
def list_public_shares(
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取公开分享的模板广场"""
    share_repo = TemplateShareRepository(db)
    shares = share_repo.get_public_shares(limit=limit, offset=offset)
    
    return [
        TemplateShareResponse(
            id=s.id,
            template_id=s.template_id,
            user_id=s.user_id,
            share_type=s.share_type,
            share_code=s.share_code,
            share_title=s.share_title,
            share_description=s.share_description,
            family_group_id=s.family_group_id,
            usage_count=s.usage_count,
            like_count=s.like_count,
            is_active=s.is_active,
            created_at=s.created_at,
            owner_nickname=s.user.nickname if s.user else None,
            template_name=s.template.name if s.template else None
        ) for s in shares
    ]


@router.get("/templates/share/{share_code}", response_model=TemplateShareDetail)
def get_share_detail(
    share_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取分享详情
    - 包含完整模板信息
    """
    share_repo = TemplateShareRepository(db)
    like_repo = TemplateLikeRepository(db)
    
    share = share_repo.get_by_share_code(share_code)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分享不存在或已失效"
        )
    
    # 检查家庭分享的权限
    if share.share_type == ShareType.FAMILY:
        member_repo = FamilyMemberRepository(db)
        if not member_repo.is_member(share.family_group_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该家庭分享"
            )
    
    # 检查当前用户是否点赞
    is_liked = like_repo.is_liked(share.id, current_user.id)
    
    return TemplateShareDetail(
        id=share.id,
        template_id=share.template_id,
        user_id=share.user_id,
        share_type=share.share_type,
        share_code=share.share_code,
        share_title=share.share_title,
        share_description=share.share_description,
        family_group_id=share.family_group_id,
        usage_count=share.usage_count,
        like_count=share.like_count,
        is_active=share.is_active,
        created_at=share.created_at,
        owner_nickname=share.user.nickname if share.user else None,
        template_name=share.template.name if share.template else None,
        template=UserCustomTemplateResponse(
            id=share.template.id,
            user_id=share.template.user_id,
            name=share.template.name,
            description=share.template.description,
            recurrence_type=share.template.recurrence_type,
            recurrence_config=share.template.recurrence_config,
            remind_advance_days=share.template.remind_advance_days,
            created_from_template_id=share.template.created_from_template_id,
            created_at=share.template.created_at,
            updated_at=share.template.updated_at
        ) if share.template else None,
        is_liked=is_liked
    )


@router.post("/templates/share/{share_code}/use", response_model=TemplateUsageResponse)
def use_shared_template(
    share_code: str,
    data: TemplateUsageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    使用分享的模板
    - 记录使用并可选评价
    """
    share_repo = TemplateShareRepository(db)
    usage_repo = TemplateUsageRecordRepository(db)
    
    share = share_repo.get_by_share_code(share_code)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分享不存在"
        )
    
    # 增加使用次数
    share_repo.increment_usage(share.id)
    
    # 创建使用记录
    usage = usage_repo.create(
        template_share_id=share.id,
        user_id=current_user.id,
        feedback_rating=data.feedback_rating,
        feedback_comment=data.feedback_comment
    )
    
    return TemplateUsageResponse(
        id=usage.id,
        template_share_id=usage.template_share_id,
        user_id=usage.user_id,
        feedback_rating=usage.feedback_rating,
        feedback_comment=usage.feedback_comment,
        used_at=usage.used_at
    )


@router.post("/templates/share/{share_id}/like", status_code=status.HTTP_201_CREATED)
def like_template(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """点赞模板"""
    share_repo = TemplateShareRepository(db)
    like_repo = TemplateLikeRepository(db)
    
    share = share_repo.get_by_id(share_id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分享不存在"
        )
    
    # 添加点赞
    like = like_repo.add_like(share_id, current_user.id)
    if not like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已经点赞过该模板"
        )
    
    # 增加点赞数
    share_repo.increment_like(share_id)
    
    return {"message": "点赞成功"}


@router.delete("/templates/share/{share_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_template(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消点赞"""
    share_repo = TemplateShareRepository(db)
    like_repo = TemplateLikeRepository(db)
    
    success = like_repo.remove_like(share_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未点赞过该模板"
        )
    
    # 减少点赞数
    share_repo.decrement_like(share_id)
    
    return None
