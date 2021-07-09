import boto3
from boto3.dynamodb.conditions import Key

import os
import argparse
from decimal import Decimal

import pandas as pd


def load_files(file_list, inputpath):
    """
    function to load the data from potentially multiple files into one pandas DataFrame
    """
    df = None

    # loop through files and append
    for i, file in enumerate(file_list):
        path = f"{inputpath}/{file}"
        print(path)
        df_i = pd.read_csv(path)
        if i == 0:
            df = df_i
        else:
            df = pd.concat([df, df_i], axis=0, ignore_index=True)
    return df


def load_data(inputpath):
    """
    simple function to load data
    """

    print(inputpath)
    files = os.listdir(inputpath)
    print(files)
    df = load_files(files, inputpath)

    return df


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--new_model_name", type=str)
    parser.add_argument("--prod_table", type=str)
    parser.add_argument("--hist_table", type=str)
    parser.add_argument("--region_name", type=str)
    args, _ = parser.parse_known_args()

    print("Received arguments {}".format(args))

    prefix = "/opt/ml/processing"
    input_truth_path = os.path.join(prefix, "input/truth")
    input_result_path = os.path.join(prefix, "input/result")

    # load ground truth dataset
    truth = load_data(input_truth_path)
    truth = pd.get_dummies(truth["Churn?"])

    # load prediction result
    result = pd.read_csv(
        os.path.join(input_result_path, "processed.csv.out"),
        header=None,
        names=["predict"],
    ).round()

    concat = pd.concat([truth["True."], result], axis=1)

    # calculate correct prediction
    accuracy = len(concat[concat["True."] == concat["predict"]]) / len(concat)

    # save the newly trained model info in historical model DDB table
    ddb_resource = boto3.resource("dynamodb", region_name=args.region_name)
    state = args.new_model_name.split("-")[1]
    hist_table = ddb_resource.Table(args.hist_table)
    _ = hist_table.put_item(
        Item={
            "model_name": args.new_model_name,
            "state": state,
            "accuracy": Decimal(str(accuracy)),
        }
    )

    # fetch in-production model performance
    prod_table = ddb_resource.Table(args.prod_table)
    item = prod_table.query(KeyConditionExpression=Key("state").eq(state)).get("Items")[
        0
    ]
    prod_model_name = item["model_name"]
    prod_model_acc = item["accuracy"]

    # update in-production model info if newly trained model has better performance
    if accuracy > prod_model_acc:
        _ = prod_table.put_item(
            Item={
                "state": state,
                "model_name": args.new_model_name,
                "accuracy": Decimal(str(accuracy)),
            }
        )
