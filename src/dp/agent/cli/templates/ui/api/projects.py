"""
项目列表 API
"""
import logging
import aiohttp
from fastapi import APIRouter, Request, HTTPException
from typing import List, Dict, Any

from server.utils import get_ak_info_from_request

logger = logging.getLogger(__name__)

router = APIRouter()

BOHRIUM_API_BASE = "https://openapi.dp.tech/openapi/v1"


@router.get("/api/projects")
async def get_projects(request: Request) -> Dict[str, Any]:
    """获取用户的项目列表"""
    try:
        # 从请求中获取 AK
        access_key, _ = get_ak_info_from_request(request.headers)
        
        if not access_key:
            return {
                "success": False,
                "error": "未找到 AccessKey",
                "projects": []
            }
        
        # 调用 Bohrium API
        headers = {
            "AccessKey": access_key,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BOHRIUM_API_BASE}/project/list",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                data = await response.json()
                
                if data.get("code") != 0:
                    logger.error(f"获取项目列表失败: {data}")
                    return {
                        "success": False,
                        "error": data.get("error", "获取项目列表失败"),
                        "projects": []
                    }
                
                # 提取项目信息
                projects = []
                items = data.get("data", {}).get("items", [])
                for item in items:
                    projects.append({
                        "id": item["id"],
                        "name": item["name"],
                        "creatorName": item.get("creatorName", ""),
                        "createTime": item.get("createTime", ""),
                        "projectRole": item.get("projectRole", 0)
                    })
                
                return {
                    "success": True,
                    "projects": projects
                }
                
    except aiohttp.ClientTimeout:
        logger.error("请求超时")
        return {
            "success": False,
            "error": "请求超时",
            "projects": []
        }
    except Exception as e:
        logger.error(f"获取项目列表时发生错误: {e}")
        return {
            "success": False,
            "error": str(e),
            "projects": []
        }


@router.get("/api/projects/{project_id}/verify")
async def verify_project(project_id: int, request: Request) -> Dict[str, Any]:
    """验证特定的 project_id 是否属于当前用户
    
    Args:
        project_id: 要验证的项目 ID
        request: FastAPI 请求对象
        
    Returns:
        包含验证结果的字典
    """
    try:
        # 从请求中获取 AK
        access_key, _ = get_ak_info_from_request(request.headers)
        
        if not access_key:
            return {
                "success": False,
                "error": "未找到 AccessKey",
                "valid": False
            }
        
        # 调用 Bohrium API 获取项目列表
        headers = {
            "AccessKey": access_key,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BOHRIUM_API_BASE}/project/list",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                data = await response.json()
                
                if data.get("code") != 0:
                    logger.error(f"获取项目列表失败: {data}")
                    return {
                        "success": False,
                        "error": data.get("error", "获取项目列表失败"),
                        "valid": False
                    }
                
                # 检查 project_id 是否在用户的项目列表中
                items = data.get("data", {}).get("items", [])
                user_project_ids = [item["id"] for item in items]
                
                is_valid = project_id in user_project_ids
                
                # 如果找到项目，返回项目详情
                project_info = None
                if is_valid:
                    for item in items:
                        if item["id"] == project_id:
                            project_info = {
                                "id": item["id"],
                                "name": item["name"],
                                "creatorName": item.get("creatorName", ""),
                                "createTime": item.get("createTime", ""),
                                "projectRole": item.get("projectRole", 0)
                            }
                            break
                
                return {
                    "success": True,
                    "valid": is_valid,
                    "project": project_info
                }
                
    except aiohttp.ClientTimeout:
        logger.error("请求超时")
        return {
            "success": False,
            "error": "请求超时",
            "valid": False
        }
    except Exception as e:
        logger.error(f"验证项目时发生错误: {e}")
        return {
            "success": False,
            "error": str(e),
            "valid": False
        }