"""
Template API
模板系统的 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.security import get_current_user

logger = structlog.get_logger(__name__)
from app.models.user import User
from app.models.template_share import ShareType
from app.schemas.response import ApiResponse
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

@router.get("/templates/system", response_model=ApiResponse[List[ReminderTemplateResponse]])
async def list_system_templates(
    category: Optional[str] = Query(None, description="按分类筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取系统模板列表
    - 可按分类筛选
    - 按使用次数排序
    """
    template_repo = ReminderTemplateRepository(db)
    
    if category:
        templates = await template_repo.get_by_category(category)
    else:
        templates = await template_repo.get_all_active()
    
    return ApiResponse.success(data=[
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
    ])


@router.get("/templates/system/{template_id}", response_model=ApiResponse[ReminderTemplateResponse])
async def get_system_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取系统模板详情"""
    template_repo = ReminderTemplateRepository(db)
    template = await template_repo.get_by_id(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统模板不存在"
        )
    
    return ApiResponse.success(data=ReminderTemplateResponse(
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
    ))


@router.get("/templates/system/popular", response_model=ApiResponse[List[ReminderTemplateResponse]])
async def get_popular_templates(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取热门系统模板"""
    template_repo = ReminderTemplateRepository(db)
    templates = await template_repo.get_popular(limit=limit)
    
    return ApiResponse.success(data=[
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
    ])


# ==================== 用户自定义模板 ====================

@router.post("/templates/custom", response_model=ApiResponse[UserCustomTemplateResponse], status_code=status.HTTP_201_CREATED)
async def create_custom_template(
    data: UserCustomTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建用户自定义模板
    - 可以基于系统模板创建
    """
    template_repo = UserCustomTemplateRepository(db)
    
    # 检查名称是否重复
    existing = await template_repo.get_by_user_and_name(current_user.id, data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该模板名称已存在"
        )
    
    # 如果基于系统模板，增加系统模板使用次数
    if data.created_from_template_id:
        system_template_repo = ReminderTemplateRepository(db)
        system_template_repo.increment_usage(data.created_from_template_id)
    
    template = await template_repo.create(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        recurrence_type=data.recurrence_type,
        recurrence_config=data.recurrence_config,
        remind_advance_days=data.remind_advance_days,
        created_from_template_id=data.created_from_template_id
    )
    
    return ApiResponse.success(data=UserCustomTemplateResponse(
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
    ))


@router.get("/templates/custom", response_model=ApiResponse[List[UserCustomTemplateResponse]])
async def list_my_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的自定义模板列表"""
    template_repo = UserCustomTemplateRepository(db)
    templates = await template_repo.get_user_templates(current_user.id)
    
    return ApiResponse.success(data=[
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
    ])


@router.put("/templates/custom/{template_id}", response_model=ApiResponse[UserCustomTemplateResponse])
async def update_custom_template(
    template_id: int,
    data: UserCustomTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户自定义模板"""
    template_repo = UserCustomTemplateRepository(db)
    
    template = await template_repo.get_by_id(template_id)
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
    updated_template = await template_repo.update(template_id, **update_data)
    
    return ApiResponse.success(data=UserCustomTemplateResponse(
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
    ))


@router.delete("/templates/custom/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户自定义模板"""
    template_repo = UserCustomTemplateRepository(db)
    
    template = await template_repo.get_by_id(template_id)
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

@router.post("/templates/share", response_model=ApiResponse[TemplateShareResponse], status_code=status.HTTP_201_CREATED)
async def share_template(
    data: TemplateShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分享模板
    - 支持公开分享、家庭分享、链接分享
    """
    custom_template_repo = UserCustomTemplateRepository(db)
    share_repo = TemplateShareRepository(db)
    
    # 检查模板是否存在且属于当前用户
    template = await custom_template_repo.get_by_id(data.template_id)
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
        if not await member_repo.is_member(data.family_group_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不是该家庭组成员"
            )
    
    # 创建分享
    share = await share_repo.create(
        template_id=data.template_id,
        user_id=current_user.id,
        share_type=data.share_type,
        share_title=data.share_title,
        share_description=data.share_description,
        family_group_id=data.family_group_id
    )
    
    return ApiResponse.success(data=TemplateShareResponse(
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
    ))


@router.get("/templates/share/public", response_model=ApiResponse[List[TemplateShareResponse]])
async def list_public_shares(
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db)
):
    """获取公开分享的模板广场"""
    share_repo = TemplateShareRepository(db)
    shares = await share_repo.get_public_shares(limit=limit, offset=offset)
    
    return ApiResponse.success(data=[
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
    ])


@router.get("/templates/share/{share_code}", response_model=ApiResponse[TemplateShareDetail])
async def get_share_detail(
    share_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取分享详情
    - 包含完整模板信息
    """
    share_repo = TemplateShareRepository(db)
    like_repo = TemplateLikeRepository(db)
    
    share = await share_repo.get_by_share_code(share_code)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分享不存在或已失效"
        )
    
    # 检查家庭分享的权限
    if share.share_type == ShareType.FAMILY:
        member_repo = FamilyMemberRepository(db)
        if not await member_repo.is_member(share.family_group_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该家庭分享"
            )
    
    # 检查当前用户是否点赞
    is_liked = await like_repo.is_liked(share.id, current_user.id)
    
    return ApiResponse.success(data=TemplateShareDetail(
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
    ))


@router.post("/templates/share/{share_code}/use", response_model=ApiResponse[TemplateUsageResponse])
async def use_shared_template(
    share_code: str,
    data: TemplateUsageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    使用分享的模板
    - 记录使用并可选评价
    """
    share_repo = TemplateShareRepository(db)
    usage_repo = TemplateUsageRecordRepository(db)
    
    share = await share_repo.get_by_share_code(share_code)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分享不存在"
        )
    
    # 增加使用次数
    share_repo.increment_usage(share.id)
    
    # 创建使用记录
    usage = await usage_repo.create(
        template_share_id=share.id,
        user_id=current_user.id,
        feedback_rating=data.feedback_rating,
        feedback_comment=data.feedback_comment
    )
    
    return ApiResponse.success(data=TemplateUsageResponse(
        id=usage.id,
        template_share_id=usage.template_share_id,
        user_id=usage.user_id,
        feedback_rating=usage.feedback_rating,
        feedback_comment=usage.feedback_comment,
        used_at=usage.used_at
    ))


@router.post("/templates/share/{share_id}/like", status_code=status.HTTP_201_CREATED)
async def like_template(
    share_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """点赞模板"""
    share_repo = TemplateShareRepository(db)
    like_repo = TemplateLikeRepository(db)
    
    share = await share_repo.get_by_id(share_id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分享不存在"
        )
    
    # 添加点赞
    like = await like_repo.add_like(share_id, current_user.id)
    if not like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已经点赞过该模板"
        )
    
    # 增加点赞数
    share_repo.increment_like(share_id)
    
    return ApiResponse.success(data={"message": "点赞成功"})


@router.delete("/templates/share/{share_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_template(
    share_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消点赞"""
    share_repo = TemplateShareRepository(db)
    like_repo = TemplateLikeRepository(db)
    
    success = await like_repo.remove_like(share_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未点赞过该模板"
        )
    
    # 减少点赞数
    share_repo.decrement_like(share_id)
    
    return None


# ==================== 模板市场 ====================

@router.get("/marketplace", response_model=ApiResponse[List[TemplateShareDetail]])
async def get_template_marketplace(
    category: Optional[str] = Query(None, description="分类筛选"),
    sort_by: str = Query("popular", description="排序方式: popular(热门)/latest(最新)/most_used(最常用)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    模板市场 - 公开模板列表
    
    排序方式:
    - popular: 按点赞数排序
    - latest: 按创建时间排序
    - most_used: 按使用次数排序
    """
    share_repo = TemplateShareRepository(db)
    template_repo = ReminderTemplateRepository(db)
    custom_template_repo = UserCustomTemplateRepository(db)
    
    # 获取公开分享列表
    shares = await share_repo.get_public_shares(limit=limit * 2, offset=offset)
    
    # 过滤和排序
    if category:
        # 需要加载模板信息以过滤分类
        filtered_shares = []
        for share in shares:
            if share.template_id:  # 系统模板
                template = await template_repo.get_by_id(share.template_id)
                if template and template.category == category:
                    filtered_shares.append(share)
            else:  # 自定义模板
                template = await custom_template_repo.get_by_id(share.custom_template_id)
                if template and template.category == category:
                    filtered_shares.append(share)
        shares = filtered_shares
    
    # 排序
    if sort_by == "popular":
        shares = sorted(shares, key=lambda x: x.like_count, reverse=True)
    elif sort_by == "latest":
        shares = sorted(shares, key=lambda x: x.created_at, reverse=True)
    elif sort_by == "most_used":
        shares = sorted(shares, key=lambda x: x.usage_count, reverse=True)
    
    # 限制返回数量
    shares = shares[:limit]
    
    # 构建详细响应
    result = []
    for share in shares:
        if share.template_id:
            template = await template_repo.get_by_id(share.template_id)
            template_name = template.name if template else "未知模板"
            template_category = template.category if template else "other"
        else:
            template = await custom_template_repo.get_by_id(share.custom_template_id)
            template_name = template.name if template else "未知模板"
            template_category = template.category if template else "other"
        
        result.append(TemplateShareDetail(
            id=share.id,
            template_id=share.template_id,
            custom_template_id=share.custom_template_id,
            template_name=template_name,
            template_category=template_category,
            user_id=share.user_id,
            share_type=share.share_type,
            share_code=share.share_code,
            share_title=share.share_title,
            share_description=share.share_description,
            usage_count=share.usage_count,
            like_count=share.like_count,
            is_active=share.is_active,
            created_at=share.created_at
        ))
    
    return ApiResponse.success(data=result, message=f"找到 {len(result)} 个公开模板")


@router.get("/marketplace/search", response_model=ApiResponse[List[TemplateShareDetail]])
async def search_marketplace_templates(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索模板市场
    """
    share_repo = TemplateShareRepository(db)
    template_repo = ReminderTemplateRepository(db)
    custom_template_repo = UserCustomTemplateRepository(db)
    
    # 获取所有公开分享
    all_shares = await share_repo.get_public_shares(limit=500, offset=0)
    
    # 搜索匹配的模板
    matched_shares = []
    for share in all_shares:
        # 检查分享标题和描述
        if keyword.lower() in (share.share_title or "").lower() or \
           keyword.lower() in (share.share_description or "").lower():
            matched_shares.append(share)
            continue
        
        # 检查模板名称
        if share.template_id:
            template = await template_repo.get_by_id(share.template_id)
            if template and keyword.lower() in template.name.lower():
                matched_shares.append(share)
        else:
            template = await custom_template_repo.get_by_id(share.custom_template_id)
            if template and keyword.lower() in template.name.lower():
                matched_shares.append(share)
    
    # 限制返回数量
    matched_shares = matched_shares[:limit]
    
    # 构建响应
    result = []
    for share in matched_shares:
        if share.template_id:
            template = await template_repo.get_by_id(share.template_id)
            template_name = template.name if template else "未知模板"
            template_category = template.category if template else "other"
        else:
            template = await custom_template_repo.get_by_id(share.custom_template_id)
            template_name = template.name if template else "未知模板"
            template_category = template.category if template else "other"
        
        result.append(TemplateShareDetail(
            id=share.id,
            template_id=share.template_id,
            custom_template_id=share.custom_template_id,
            template_name=template_name,
            template_category=template_category,
            user_id=share.user_id,
            share_type=share.share_type,
            share_code=share.share_code,
            share_title=share.share_title,
            share_description=share.share_description,
            usage_count=share.usage_count,
            like_count=share.like_count,
            is_active=share.is_active,
            created_at=share.created_at
        ))
    
    return ApiResponse.success(data=result, message=f"找到 {len(result)} 个匹配模板")


@router.get("/marketplace/categories", response_model=ApiResponse[List[dict]])
async def get_marketplace_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    获取模板市场分类统计
    """
    share_repo = TemplateShareRepository(db)
    template_repo = ReminderTemplateRepository(db)
    custom_template_repo = UserCustomTemplateRepository(db)
    
    # 获取所有公开分享
    all_shares = await share_repo.get_public_shares(limit=1000, offset=0)
    
    # 统计各分类数量
    category_stats = {}
    for share in all_shares:
        if share.template_id:
            template = await template_repo.get_by_id(share.template_id)
            category = template.category if template else "other"
        else:
            template = await custom_template_repo.get_by_id(share.custom_template_id)
            category = template.category if template else "other"
        
        if category not in category_stats:
            category_stats[category] = 0
        category_stats[category] += 1
    
    # 转换为列表
    result = [
        {"category": cat, "count": count}
        for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return ApiResponse.success(data=result)
