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