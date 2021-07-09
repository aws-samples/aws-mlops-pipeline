from datetime import datetime
import os
import json

import boto3

sfn_client = boto3.client("stepfunctions")

TRAINING_STATE_MACHINE = os.environ.get("TRAINING_STATE_MACHINE")
INFERENCE_STATE_MACHINE = os.environ.get("INFERENCE_STATE_MACHINE")
PERFORMANCE_STATE_MACHINE = os.environ.get("PERFORMANCE_STATE_MACHINE")


def state_machine_start_execution(state_machines_arn, name, sf_input):
    sfn_client.start_execution(
        stateMachineArn=state_machines_arn,
        name=name,
        input=json.dumps(sf_input),
    )


def lambda_handler(event, context):

    print(event)

    if event.get("Records"):
        s3_objects = [
            {
                "bucket": record["s3"]["bucket"]["name"],
                "key": record["s3"]["object"]["key"],
            }
            for record in event["Records"]
            if record.get("s3")
        ]

        if not s3_objects:
            print("No S3 object find in the event!")
            return

        bucket = s3_objects[0]["bucket"]
        key = s3_objects[0]["key"]

        tok = key.split("/")

        if len(tok) != 4:
            print(f"S3 object prefix {key} is not matching the required format!")
            return

        use_case = tok[0]
        data_type = tok[1]
        state = tok[2]

        if data_type != "raw":
            print("Incorrect data type. Only raw data could trigger the state machine!")
            return

        if use_case in ["training", "inference"]:

            current_time = datetime.now().strftime("%Y-%m-%d-%H-%M")

            job_name = f"{state}-{current_time}"

            state_machine_input = {
                "Comment": "Automatically triggered by S3 event",
                "bucket": bucket,
                "use_case": use_case,
                "state": state,
                "job_name": job_name,
            }

            state_machine_start_execution(
                TRAINING_STATE_MACHINE
                if use_case == "training"
                else INFERENCE_STATE_MACHINE,
                job_name,
                state_machine_input,
            )

            print("State machine successfully triggered")

    elif event.get("source") == "aws.states":

        event_input = json.loads(event.get("detail").get("input"))
        event_output = json.loads(event.get("detail").get("output"))

        state = event_input.get("state")

        if event_output.get("use_case") == "inference":
            print("Only training workflow receives event from state machine!")
            return

        state_machine_type = (
            event.get("detail")
            .get("stateMachineArn")
            .split(":")[-1]
            .split("-")[-1]
            .lower()
        )

        current_time = datetime.now().strftime("%Y-%m-%d-%H-%M")

        job_name = f"{state}-{current_time}"

        state_machine_input = event_input

        state_machine_input[
            "Comment"
        ] = "Automatically triggered by State Machine event"

        if state_machine_type == "training":
            state_machine_input["model_name"] = event_output["model"]["model_name"]

        state_machine_start_execution(
            INFERENCE_STATE_MACHINE
            if state_machine_type == "training"
            else PERFORMANCE_STATE_MACHINE,
            job_name,
            state_machine_input,
        )

        print("State machine successfully triggered")

    else:
        return
