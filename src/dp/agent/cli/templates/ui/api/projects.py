# Projects API using bohrium-open-sdk
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Request
from bohrium_open_sdk import OpenSDK

from server.utils import get_ak_info_from_request

router = APIRouter()


def make_client_from_request(request: Request) -> OpenSDK:
    """Parse AccessKey/AppKey from request headers and create SDK client"""
    access_key, app_key = get_ak_info_from_request(request.headers)
    if not access_key:
        raise ValueError("未找到 AccessKey")
    if not app_key:
        raise ValueError("未找到 AppKey")
    return OpenSDK(access_key=access_key, app_key=app_key)


def normalize_project(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize project structure for frontend:
    - id: item['project_id'] or item['id']
    - name: item['project_name'] or item['name']
    Set default values for missing fields
    """
    pid = item.get("project_id", item.get("id"))
    name = item.get("project_name", item.get("name"))
    return {
        "id": pid,
        "name": name,
        "creatorName": item.get("creatorName", ""),
        "createTime": item.get("createTime", ""),
        "projectRole": item.get("projectRole", 0),
    }


async def verify_user_project(access_key: str, app_key: str, project_id: int) -> bool:
    """
    Use bohrium-open-sdk to verify if project_id belongs to current user
    """
    if not access_key or not app_key or not project_id:
        return False

    try:
        client = OpenSDK(access_key=access_key, app_key=app_key)
        res = client.user.list_project()
        if res.get("code") != 0:
            return False

        items: List[Dict[str, Any]] = res.get("data", {}).get("items", []) or []
        user_project_ids = [it.get("project_id", it.get("id")) for it in items]

        # Compatible with string/integer ID
        user_project_ids_int: List[int] = []
        for pid in user_project_ids:
            try:
                user_project_ids_int.append(int(pid))
            except Exception:
                pass

        return int(project_id) in user_project_ids_int

    except Exception as e:
        return False


@router.get("/api/projects")
async def get_projects(request: Request) -> Dict[str, Any]:
    """Get user's project list using SDK"""
    try:
        client = make_client_from_request(request)
        user_info = client.user.get_info()
        # Response data contains: user_id, name, org_id
        response = f"Get userid success,the user_id is: {user_info['data']['user_id']}"
        print(response)
        res = client.user.list_project()
        if res.get("code") != 0:
            return {
                "success": False,
                "error": res.get("error", "获取项目列表失败"),
                "projects": [],
            }

        items: List[Dict[str, Any]] = res.get("data", {}).get("items", []) or []
        projects = [normalize_project(it) for it in items]

        return {"success": True, "projects": projects}

    except ValueError as ve:
        return {"success": False, "error": str(ve), "projects": []}
    except Exception as e:
        return {"success": False, "error": str(e), "projects": []}


@router.get("/api/projects/{project_id}/verify")
async def verify_project(project_id: int, request: Request) -> Dict[str, Any]:
    """Verify if specific project_id belongs to current user"""
    try:
        access_key, app_key = get_ak_info_from_request(request.headers)

        if not access_key or not app_key:
            return {
                "success": False,
                "error": "未找到 AccessKey 或 AppKey",
                "valid": False,
            }

        is_valid = await verify_user_project(access_key, app_key, project_id)

        if not is_valid:
            return {
                "success": True,
                "valid": False,
                "error": "该项目不属于当前用户",
            }

        # Find specific project info and return
        client = OpenSDK(access_key=access_key, app_key=app_key)
        res = client.user.list_project()
        if res.get("code") != 0:
            return {
                "success": False,
                "error": res.get("error", "获取项目列表失败"),
                "valid": False,
            }

        items: List[Dict[str, Any]] = res.get("data", {}).get("items", []) or []
        project_info: Optional[Dict[str, Any]] = None
        for it in items:
            raw_id = it.get("project_id", it.get("id"))
            try:
                if int(raw_id) == int(project_id):
                    project_info = normalize_project(it)
                    break
            except Exception:
                continue

        return {"success": True, "valid": True, "project": project_info or {"id": project_id}}

    except ValueError as ve:
        return {"success": False, "error": str(ve), "valid": False}
    except Exception as e:
        return {"success": False, "error": str(e), "valid": False}