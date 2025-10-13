import logging
import traceback
from typing import Any

import mcp
from mcp.types import TextContent
from pydantic import BaseModel


def get_logger(name, level="INFO",
               format="%(asctime)s - %(levelname)s - %(message)s"):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level.upper()))
    handler.setFormatter(logging.Formatter(format))
    logger.addHandler(handler)
    return logger


class JobResult(BaseModel):
    result: Any
    job_info: dict


class Tool(mcp.server.fastmcp.tools.Tool):
    """
    Workaround MCP server cannot print traceback
    Add job info to first unstructured content
    """
    async def run(self, *args, **kwargs):
        try:
            kwargs["convert_result"] = False
            result = await super().run(*args, **kwargs)
            if isinstance(result, JobResult):
                job_info = result.job_info
                result = self.fn_metadata.convert_result(result.result)
                if isinstance(result, tuple) and len(result) == 2:
                    unstructured_content, _ = result
                else:
                    unstructured_content = result
                if len(unstructured_content) == 0:
                    unstructured_content.append(
                        TextContent(type="text", text="null"))
                unstructured_content[0].job_info = job_info
            else:
                result = self.fn_metadata.convert_result(result)
            return result
        except Exception as e:
            traceback.print_exc()
            raise e
