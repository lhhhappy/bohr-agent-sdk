"""
Debug API endpoints for troubleshooting
"""
import os
import json
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from config.agent_config import agentconfig
from api.websocket import manager

async def get_runner_status():
    """
    获取所有 Runner 的状态
    """
    try:
        runner_status = {}
        
        # 获取所有 Runner 的状态
        for runner_key, runner in manager.runners.items():
            runner_status[runner_key] = {
                "exists": True,
                "type": type(runner).__name__,
                "created": True
            }
        
        # 获取所有 Runner 错误
        runner_errors = getattr(manager, '_runner_errors', {})
        for error_key, error_msg in runner_errors.items():
            runner_status[error_key] = {
                "exists": False,
                "error": error_msg,
                "created": False
            }
        
        return JSONResponse({
            "success": True,
            "runners": runner_status,
            "total_runners": len(manager.runners),
            "total_errors": len(runner_errors),
            "active_connections": len(manager.active_connections)
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

async def get_config_status():
    """
    获取配置状态
    """
    try:
        config = agentconfig.config
        
        # 获取 Agent 配置
        agent_config = config.get("agent", {})
        
        # 测试 Agent 是否可以加载
        test_result = {
            "can_load": False,
            "error": None,
            "agent_type": None
        }
        
        try:
            # 尝试加载 Agent（不传递参数）
            test_agent = agentconfig.get_agent()
            test_result["can_load"] = True
            test_result["agent_type"] = type(test_agent).__name__
        except Exception as e:
            test_result["error"] = str(e)
        
        return JSONResponse({
            "success": True,
            "config": {
                "agent_name": agent_config.get("name"),
                "agent_module": agent_config.get("module"),
                "root_agent": agent_config.get("rootAgent"),
                "config_path": str(agentconfig.config_path),
                "config_exists": agentconfig.config_path.exists()
            },
            "test_result": test_result,
            "environment": {
                "user_working_dir": os.environ.get('USER_WORKING_DIR', os.getcwd()),
                "bohr_project_id": os.environ.get('BOHR_PROJECT_ID'),
                "agent_config_path": os.environ.get('AGENT_CONFIG_PATH')
            }
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

async def get_session_status():
    """
    获取会话状态
    """
    try:
        session_info = {}
        
        # 获取每个用户的会话信息
        for user_id, session_service in manager.session_services.items():
            try:
                response = await session_service.list_sessions(
                    app_name=manager.app_name,
                    user_id=user_id
                )
                sessions = response.sessions if hasattr(response, 'sessions') else []
                session_info[user_id] = {
                    "session_count": len(sessions),
                    "sessions": [
                        {
                            "id": s.id,
                            "state": s.state if hasattr(s, 'state') else {}
                        } for s in sessions[:3]  # 只显示前3个
                    ]
                }
            except Exception as e:
                session_info[user_id] = {
                    "error": str(e)
                }
        
        return JSONResponse({
            "success": True,
            "users": len(manager.session_services),
            "session_info": session_info,
            "active_connections": [
                {
                    "user": ctx.get_user_identifier(),
                    "project_id": ctx.project_id,
                    "current_session": ctx.current_session_id,
                    "is_registered": ctx.is_registered_user()
                }
                for ctx in manager.active_connections.values()
            ]
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

async def test_agent_creation():
    """
    测试 Agent 创建过程
    """
    try:
        steps = []
        
        # Step 1: 加载配置
        steps.append({
            "step": "加载配置",
            "success": True,
            "details": {
                "config_path": str(agentconfig.config_path),
                "agent_module": agentconfig.config.get("agent", {}).get("module")
            }
        })
        
        # Step 2: 创建 Agent（不带参数）
        try:
            agent = agentconfig.get_agent()
            steps.append({
                "step": "创建 Agent (无参数)",
                "success": True,
                "details": {
                    "agent_type": type(agent).__name__,
                    "has_run_method": hasattr(agent, 'run') or hasattr(agent, '__call__')
                }
            })
        except Exception as e:
            steps.append({
                "step": "创建 Agent (无参数)",
                "success": False,
                "error": str(e)
            })
            
        # Step 3: 创建 Agent（带 project_id）
        try:
            project_id = os.environ.get('BOHR_PROJECT_ID')
            if project_id:
                agent_with_project = agentconfig.get_agent(
                    ak="",
                    app_key="",
                    project_id=int(project_id)
                )
                steps.append({
                    "step": f"创建 Agent (project_id={project_id})",
                    "success": True,
                    "details": {
                        "agent_type": type(agent_with_project).__name__
                    }
                })
        except Exception as e:
            steps.append({
                "step": f"创建 Agent (project_id={project_id})",
                "success": False,
                "error": str(e)
            })
        
        # Step 4: 检查 SessionService
        try:
            from google.adk.sessions import InMemorySessionService
            test_service = InMemorySessionService()
            steps.append({
                "step": "创建 SessionService",
                "success": True,
                "details": {
                    "service_type": type(test_service).__name__
                }
            })
        except Exception as e:
            steps.append({
                "step": "创建 SessionService",
                "success": False,
                "error": str(e)
            })
        
        # Step 5: 创建 Runner
        try:
            from google.adk import Runner
            if 'agent' in locals() and 'test_service' in locals():
                test_runner = Runner(
                    agent=agent,
                    session_service=test_service,
                    app_name="TestApp"
                )
                steps.append({
                    "step": "创建 Runner",
                    "success": True,
                    "details": {
                        "runner_type": type(test_runner).__name__
                    }
                })
        except Exception as e:
            steps.append({
                "step": "创建 Runner", 
                "success": False,
                "error": str(e)
            })
        
        all_success = all(step.get("success", False) for step in steps)
        
        return JSONResponse({
            "success": all_success,
            "steps": steps,
            "summary": {
                "total_steps": len(steps),
                "successful": sum(1 for s in steps if s.get("success", False)),
                "failed": sum(1 for s in steps if not s.get("success", False))
            }
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)