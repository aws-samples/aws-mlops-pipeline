import os
import boto3

PROD_MODEL_TABLE = os.environ.get("PROD_MODEL_TABLE")
HIST_MODEL_TABLE = os.environ.get("HIST_MODEL_TABLE")


def lambda_handler(event, context):

    print(event)

    config = dict(event)

    bucket = config["bucket"]
    state = config["state"]
    job_name = config["job_name"]
    new_model_name = config["model_name"]

    config["performance_comparison"] = {
        "processing_job_name": f"performance-{job_name}",
        "entry_point": ["python", "performance_comparison.py"],
        "countainer_arguments": [
            "--new_model_name",
            new_model_name,
            "--prod_table",
            PROD_MODEL_TABLE,
            "--hist_table",
            HIST_MODEL_TABLE,
            "--region_name",
            boto3.session.Session().region_name,
        ],
        "instance_count": 1,
        "instance_type": "ml.t3.medium",
        "volume_size_in_gb": 1,
        "input_truth_path": f"s3://{bucket}/holdout/raw/{state}/",
        "input_result_path": f"s3://{bucket}/holdout/processed/{job_name}/transform/{state}/",
    }

    return config
