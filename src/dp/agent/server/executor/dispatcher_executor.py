import importlib
import inspect
import json
import logging
import os
import sys
import time
from pathlib import Path

import jsonpickle
from dpdispatcher import Machine, Resources, Task, Submission

from .base_executor import BaseExecutor
from .... import __path__
config = {
    "username": os.environ.get("BOHRIUM_USERNAME", ""),
    "password": os.environ.get("BOHRIUM_PASSWORD", ""),
    "project_id": os.environ.get("BOHRIUM_PROJECT_ID", ""),
}
logger = logging.getLogger(__name__)


def get_source_code(fn):
    source_lines, start_line = inspect.getsourcelines(fn)
    source_file = inspect.getsourcefile(fn)
    with open(source_file, "r", encoding="utf-8") as fd:
        pre_lines = fd.readlines()[:start_line-1]
    return "".join(pre_lines + source_lines) + "\n"


class DispatcherExecutor(BaseExecutor):
    def __init__(
        self,
        machine=None,
        resources=None,
        python_packages=None,
        python_executable="python3",
    ):
        """Use DPDispatcher to execute the tool
        Refer to https://docs.deepmodeling.com/projects/dpdispatcher.

        Args:
            machine: The machine configuration of DPDispatcher
            resources: The resources configuration of DPDispatcher
            python_packages: Additional python packages uploaded to runtime
                environment
            python_executable: Python executable path for running the tool
        """
        self.machine = machine or {}
        self.resources = resources or {}
        self.python_packages = python_packages or []
        self.python_packages.extend(__path__)
        self.python_packages.extend(jsonpickle.__path__)
        self.python_executable = python_executable
        self.set_defaults()

    def set_defaults(self):
        self.machine["local_root"] = "."
        if self.machine.get("context_type") == "Bohrium":
            remote_profile = self.machine["remote_profile"]
            if "email" not in remote_profile:
                remote_profile["email"] = config["username"]
            if "password" not in remote_profile:
                remote_profile["password"] = config["password"]
            if "program_id" not in remote_profile:
                remote_profile["program_id"] = int(config["project_id"])
        if "group_size" not in self.resources:
            self.resources["group_size"] = 1
        if "envs" not in self.resources:
            self.resources["envs"] = {}
        self.resources["envs"]["DP_AGENT_RUNNING_MODE"] = "1"

    def submit(self, fn, kwargs):
        script = ""
        fn_name = fn.__name__
        module_name = fn.__module__
        import_func_line = None
        if module_name in ["__main__", "__mp_main__"]:
            module = sys.modules[module_name]
            if hasattr(module, "__file__"):
                self.python_packages.append(module.__file__)
                name = os.path.splitext(os.path.basename(module.__file__))[0]
                import_func_line = "from %s import %s\n" % (name, fn_name)
            else:
                script += get_source_code(fn)
        else:
            package_name = module_name.split('.')[0]
            module = importlib.import_module(package_name)
            if hasattr(module, "__path__"):
                self.python_packages.extend(module.__path__)
            elif hasattr(module, "__file__"):
                self.python_packages.append(module.__file__)
            import_func_line = "from %s import %s\n" % (module_name, fn_name)

        script += "import asyncio, jsonpickle\n\n"
        script += "if __name__ == \"__main__\":\n"
        script += "    kwargs = jsonpickle.loads(r'''%s''')\n" % \
            jsonpickle.dumps(kwargs)
        script += "    try:\n"
        if import_func_line is not None:
            script += "        " + import_func_line
        if inspect.iscoroutinefunction(fn):
            script += "        results = asyncio.run(%s(**kwargs))\n" % fn_name
        else:
            script += "        results = %s(**kwargs)\n" % fn_name
        script += "    except Exception as e:\n"
        script += "        with open('err', 'w') as f:\n"
        script += "            f.write(str(e))\n"
        script += "        raise e\n"
        script += "    with open('results.txt', 'w') as f:\n"
        script += "        f.write(jsonpickle.dumps(results))\n"
        with open("script.py", "w") as f:
            f.write(script)

        forward_files = ["script.py"]
        for package in self.python_packages:
            target = os.path.basename(package)
            if os.path.abspath(package) != os.path.abspath(target):
                if os.path.islink(target):
                    os.remove(target)
                os.symlink(package, target)
            if target not in forward_files:
                forward_files.append(target)
        for value in kwargs.values():
            if isinstance(value, Path):
                forward_files.append(str(value))

        task = {
            "task_work_path": "./",
            "outlog": "log",
            "errlog": "log",
            "command": self.python_executable + " script.py",
            "forward_files": forward_files,
        }

        if self.machine.get("context_type") == "Bohrium":
            self.machine["remote_profile"]["input_data"]["job_name"] = fn_name
        # ensure submitting a new job
        self.resources["envs"]["SUBMISSION_TIMESTAMP"] = str(time.time())

        machine = Machine.load_from_dict(self.machine)
        resources = Resources.load_from_dict(self.resources)
        task = Task.load_from_dict(task)
        submission = Submission(
            work_base='.', machine=machine, resources=resources,
            task_list=[task])
        submission.run_submission(exit_on_submit=True)
        res = {"job_id": submission.submission_hash}
        if self.machine.get("context_type") == "Bohrium":
            job_id = submission.belonging_jobs[0].job_id
            bohr_job_id, bohr_group_id = job_id.split(":job_group_id:")
            extra_info = {
                "bohr_job_id": bohr_job_id,
                "bohr_group_id": bohr_group_id,
                "job_link": "https://bohrium.dp.tech/jobs/detail/%s" %
                bohr_job_id,
            }
            logger.info(extra_info)
            res["extra_info"] = extra_info
        return res

    def query_status(self, job_id):
        machine = Machine.load_from_dict(self.machine)
        content = machine.context.read_file(job_id + ".json")
        submission = Submission.deserialize(
            submission_dict=json.loads(content))
        submission.update_submission_state()
        if not submission.check_all_finished():
            return "Running"
        try:
            submission.run_submission(exit_on_submit=True)
        except Exception as e:
            logger.error(e)
            return "Failed"
        if os.path.isfile("results.txt"):
            return "Succeeded"
        else:
            return "Failed"

    def terminate(self, job_id):
        machine = Machine.load_from_dict(self.machine)
        content = machine.context.read_file(job_id + ".json")
        submission = Submission.deserialize(
            submission_dict=json.loads(content))
        submission.remove_unfinished_tasks()

    def get_results(self, job_id):
        if os.path.isfile("results.txt"):
            with open("results.txt", "r") as f:
                return jsonpickle.loads(f.read())
        elif os.path.isfile("err"):
            with open("err", "r") as f:
                err_msg = f.read()
            raise RuntimeError(err_msg)
        return {}
