import os

import boto3
from boto3.dynamodb.conditions import Key

ddb_resource = boto3.resource("dynamodb")

PROD_MODEL_TABLE = os.environ.get("PROD_MODEL_TABLE")


def lambda_handler(event, context):

    print(event)

    config = dict(event)

    bucket = config["bucket"]
    state = config["state"]
    job_name = config["job_name"]
    use_case = config["use_case"]

    prod_table = ddb_resource.Table(PROD_MODEL_TABLE)

    # fetch model name for transform job
    model_name = (
        prod_table.query(KeyConditionExpression=Key("state").eq(state)).get("Items")[0][
            "model_name"
        ]
        if use_case == "inference"
        else config["model_name"]
    )

    config["preprocessing"] = {
        "processing_job_name": f"{use_case}-inf-preprocessing-{job_name}",
        "entry_point": ["python", "preprocessing.py"],
        "countainer_arguments": [
            "--train_inference",
            "inference",
            "--state",
            state,
        ],
        "instance_count": 1,
        "instance_type": "ml.t3.medium",
        "volume_size_in_gb": 1,
        "input_s3_path": f"s3://{bucket}/inference/raw/{state}/"
        if use_case == "inference"
        else f"s3://{bucket}/holdout/raw/{state}/",
        "output_s3_path": f"s3://{bucket}/inference/processed/{job_name}/preprocessed/{state}/"
        if use_case == "inference"
        else f"s3://{bucket}/holdout/processed/{job_name}/preprocessed/{state}/",
    }

    config["transform"] = {
        "transform_job_name": f"{use_case}-transform-{job_name}",
        "model_name": model_name,
        "instance_count": 1,
        "instance_type": "ml.m5.large",
        "input_s3_path": config["preprocessing"]["output_s3_path"],
        "output_s3_path": f"s3://{bucket}/inference/processed/{job_name}/transform/{state}/"
        if use_case == "inference"
        else f"s3://{bucket}/holdout/processed/{job_name}/transform/{state}/",
    }

    return config
