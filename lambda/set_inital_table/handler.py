import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

ddb_resource = boto3.resource("dynamodb")

PROD_MODEL_TABLE = os.environ.get("PROD_MODEL_TABLE")
PROD_MODEL_NAME = os.environ.get("PROD_MODEL_NAME")


def lambda_handler(event, context):

    # update inital in-production model info in DDB
    prod_table = ddb_resource.Table(PROD_MODEL_TABLE)

    for state in ["RI", "MD"]:
        item = prod_table.query(KeyConditionExpression=Key("state").eq(state)).get(
            "Items"
        )

        if not item:
            _ = prod_table.put_item(
                Item={
                    "state": state,
                    "model_name": PROD_MODEL_NAME,
                    "accuracy": Decimal("0.1"),
                }
            )
