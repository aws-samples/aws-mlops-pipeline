import os

XGBOOST_IMAGE = os.environ.get("XGBOOST_IMAGE")


def lambda_handler(event, context):

    print(event)

    config = dict(event)

    bucket = config["bucket"]
    state = config["state"]
    job_name = config["job_name"]

    config["train_preprocessing"] = {
        "processing_job_name": f"train-preprocessing-{job_name}",
        "entry_point": ["python", "preprocessing.py"],
        "countainer_arguments": [
            "--train_inference",
            "train",
            "--state",
            state,
        ],
        "instance_count": 1,
        "instance_type": "ml.t3.medium",
        "volume_size_in_gb": 1,
        "input_s3_path": f"s3://{bucket}/training/raw/{state}/",
        "output_s3_path": f"s3://{bucket}/training/processed/{job_name}/preprocessed/{state}/",
    }

    config["training"] = {
        "training_job_name": f"training-{job_name}",
        "training_image": XGBOOST_IMAGE,
        "entry_point": ["python", "preprocessing.py"],
        "instance_count": 1,
        "instance_type": "ml.m5.large",
        "volume_size_in_gb": 1,
        "input_s3_path": config["train_preprocessing"]["output_s3_path"],
        "output_s3_path": f"s3://{bucket}/training/processed/{job_name}/xgboost/{state}/",
    }

    config["model"] = {
        "image": XGBOOST_IMAGE,
        "model_data_url": config["training"]["output_s3_path"]
        + config["training"]["training_job_name"]
        + "/output/model.tar.gz",
        "model_name": f"xgboost-{job_name}",
    }

    return config
