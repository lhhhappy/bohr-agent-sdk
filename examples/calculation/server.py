import os
import time
from pathlib import Path
from typing import Literal, Optional, TypedDict

from dp.agent.server import CalculationMCPServer
mcp = CalculationMCPServer("Demo")


def preprocess(executor, storage, kwargs):
    # set default input
    if executor is not None and executor.get("type") == "dispatcher" and \
            executor.get("machine", {}).get("batch_type") == "Bohrium":
        machine = executor["machine"] = executor.get("machine", {})
        remote_profile = machine["remote_profile"] = machine.get(
            "remote_profile", {})
        input_data = remote_profile["input_data"] = remote_profile.get(
            "input_data", {})
        input_data["image_name"] = input_data.get(
            "image_name", "registry.dp.tech/dptech/ubuntu:22.04-py3.10")
        input_data["job_type"] = input_data.get("job_type", "container")
        input_data["platform"] = input_data.get("platform", "ali")
        input_data["scass_type"] = input_data.get("scass_type", "c2_m4_cpu")
    return executor, storage, kwargs


@mcp.tool(preprocess_func=preprocess)
def run_dp_train(
    training_data: Path,
    validation_data: Optional[Path] = None,
    model_type: Literal["se_e2_a", "dpa2", "dpa3"] = "dpa3",
    rcut: float = 9.0,
    rcut_smth: float = 8.0,
    sel: int = 120,
    numb_steps: int = 1000000,
    decay_steps: int = 5000,
    start_lr: float = 0.001,
) -> TypedDict("results", {
    "model": Path,
    "log": Path,
    "lcurve": Path
}):
    """Train a Deep Potential (DP) model on user-provided training data
    Args:
        training_data (Path): The training data in DeePMD npy format.
        validation_data (Path): The validation data in DeePMD npy format
            (optional).
        model_type (str): The model type, allowed model types includes
            "se_e2_a", "dpa2" and "dpa3", the default value is "dpa3".
        rcut (float): The cutoff radius for neighbor searching of the model,
            the default value is 9.0.
        rcut_smth (float): The smooth cutoff radius of the model, the default
            value is 8.0.
        sel (int): The maximum possible number of neighbors in the cutoff
            radius, the default value is 120.
        numb_steps (int): Number of training steps, the default value is
            1000000.
        decay_steps (int): The learning rate is decaying every this number of
            training steps, the default value is 5000.
        start_lr (float): The learning rate at the start of the training, the
            default value is 0.001.
    Returns:
        model (Path): The output DP model.
        log (Path): The training log.
        lcurve (Path): The learning curve of the training process.
    """
    print("training_data", training_data)
    print("validation_data", validation_data)
    print("model_type", model_type)
    print("rcut", rcut)
    print("rcut_smth", rcut_smth)
    print("sel", sel)
    print("numb_steps", numb_steps)
    print("decay_steps", decay_steps)
    print("start_lr", start_lr)
    print("Running DP Train")
    time.sleep(4)
    with open("model.pt", "w") as f:
        f.write("This is model.")
    os.makedirs("logs", exist_ok=True)
    with open("logs/log.txt", "w") as f:
        f.write("This is log.")
    with open("lcurve.out", "w") as f:
        f.write("This is lcurve.")
    return {
        "model": Path("model.pt"),
        "log": Path("logs"),
        "lcurve": Path("lcurve.out"),
    }


if __name__ == "__main__":
    mcp.run(transport="sse")
