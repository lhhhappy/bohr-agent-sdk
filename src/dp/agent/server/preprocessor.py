def merge(d1, d2):
    for k in d2.keys():
        if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
            merge(d1[k], d2[k])
        else:
            d1[k] = d2[k]


def bohrium_preprocessor(default_image, default_machine_type):
    def preprocess(executor, storage, kwargs):
        modified_executor = {
            "type": "dispatcher",
            "machine": {
                "batch_type": "Bohrium",
                "context_type": "Bohrium",
                "remote_profile": {
                    "input_data": {
                        "image_name": default_image,
                        "job_type": "container",
                        "platform": "ali",
                        "scass_type": default_machine_type,
                    },
                },
            },
        }
        if executor and executor.get("type") == "dispatcher" and executor.get(
                "machine", {}).get("context_type") == "Bohrium":
            merge(modified_executor, executor)
        modified_storage = {
            "type": "bohrium",
        }
        if storage and storage.get("type") == "bohrium":
            merge(modified_storage, storage)
        return modified_executor, modified_storage, kwargs
    return preprocess
