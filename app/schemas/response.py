"""
统一响应格式 Schema
"""
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式
    
    所有接口返回格式统一为:
    {
        "code": 200,
        "message": "success",
        "data": {...}
    }
    """
    code: int = Field(200, description="状态码: 200成功, 4xx客户端错误, 5xx服务器错误")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": {}
            }
        }
    
    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "success") -> "ApiResponse[T]":
        """
        成功响应
        
        Args:
            data: 返回的数据
            message: 成功消息，默认 "success"
            
        Returns:
            ApiResponse: 统一格式的响应对象
        """
        return cls(code=200, message=message, data=data)
    
    @classmethod
    def error(cls, code: int = 400, message: str = "error", data: Optional[T] = None) -> "ApiResponse[T]":
        """
        错误响应
        
        Args:
            code: 错误状态码
            message: 错误消息
            data: 附加数据（可选）
            
        Returns:
            ApiResponse: 统一格式的响应对象
        """
        return cls(code=code, message=message, data=data)


class PageInfo(BaseModel):
    """分页信息"""
    page: int = Field(..., description="当前页码（从1开始）")
    page_size: int = Field(..., description="每页数量")
    total: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "total": 100,
                "total_pages": 5
            }
        }


class PageResponse(BaseModel, Generic[T]):
    """
    分页响应数据
    
    用于返回列表数据的分页信息
    """
    items: List[T] = Field([], description="数据列表")
    page_info: PageInfo = Field(..., description="分页信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "page_info": {
                    "page": 1,
                    "page_size": 20,
                    "total": 100,
                    "total_pages": 5
                }
            }
        }
