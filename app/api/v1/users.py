"""
User API Endpoints
用户相关的 API 端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_active_user
)
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    User registration
    用户注册
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号已被注册"
        )
    
    # Create new user
    new_user = User(
        phone=user_data.phone,
        nickname=user_data.nickname or user_data.phone[-4:],  # Default nickname
        hashed_password=get_password_hash(user_data.password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    User login
    用户登录
    """
    # Find user
    user = db.query(User).filter(User.phone == user_data.phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    
    # Create access token
    access_token = create_access_token(data={"user_id": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user info
    获取当前用户信息
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user
    更新当前用户信息
    """
    # Update user fields
    update_fields = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_fields.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user
