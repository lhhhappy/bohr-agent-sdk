import asyncio
import inspect
import jsonpickle
import os
import psutil
import uuid
from multiprocessing import Process

from .base_executor import BaseExecutor


def wrapped_fn(fn, **kwargs):
    pid = os.getpid()
    try:
        if inspect.iscoroutinefunction(fn):
            result = asyncio.run(fn(**kwargs))
        else:
            result = fn(**kwargs)
    except Exception as e:
        with open("err", "w") as f:
            f.write(str(e))
        raise e
    with open("%s.txt" % pid, "w") as f:
        f.write(jsonpickle.dumps(result))


class LocalExecutor(BaseExecutor):
    def __init__(self):
        pass

    def submit(self, fn, kwargs):
        os.environ["DP_AGENT_RUNNING_MODE"] = "1"
        p = Process(target=wrapped_fn, kwargs={"fn": fn, **kwargs})
        p.start()
        return {"job_id": str(p.pid)}

    def query_status(self, job_id):
        try:
            p = psutil.Process(int(job_id))
            if p.status() not in ["zombie", "dead"]:
                return "Running"
        except psutil.NoSuchProcess:
            pass

        if os.path.isfile("%s.txt" % job_id):
            return "Succeeded"
        else:
            return "Failed"

    def terminate(self, job_id):
        try:
            p = psutil.Process(int(job_id))
            p.terminate()
        except Exception:
            pass

    def get_results(self, job_id):
        if os.path.isfile("%s.txt" % job_id):
            with open("%s.txt" % job_id, "r") as f:
                return jsonpickle.loads(f.read())
        elif os.path.isfile("err"):
            with open("err", "r") as f:
                err_msg = f.read()
            raise RuntimeError(err_msg)
        return {}

    async def async_run(self, fn, kwargs, context, trace_id):
        if inspect.iscoroutinefunction(fn):
            result = await fn(**kwargs)
        else:
            result = fn(**kwargs)
        return {
            "job_id": str(uuid.uuid4()),
            "result": result,
        }
