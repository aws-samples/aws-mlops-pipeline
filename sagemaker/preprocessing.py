import os
import argparse

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
    parser.add_argument("--train_inference", type=str)
    parser.add_argument("--state", type=str)
    args, _ = parser.parse_known_args()

    print(f"This is a {args.train_inference} preprocessing job for state {args.state}")

    prefix = "/opt/ml/processing"
    input_path = os.path.join(prefix, "input")
    output_path = os.path.join(prefix, "output")

    # load dataset
    data = load_data(input_path)

    # preprocesse dataset
    data = data.drop(
        [
            "State",
            "Area Code",
            "Phone",
            "Day Charge",
            "Eve Charge",
            "Night Charge",
            "Intl Charge",
        ],
        axis=1,
    )
    data = pd.get_dummies(data)

    # drop label column if it's inference workflow preprocessing job
    if args.train_inference == "train":
        data = pd.concat(
            [
                data["Churn?_True."],
                data.drop(["Churn?_False.", "Churn?_True."], axis=1),
            ],
            axis=1,
        )
    elif (
        args.train_inference == "inference"
    ):  # Drop label columns for inference raw data
        data = data.drop(["Churn?_False.", "Churn?_True."], axis=1)

    # save processed dataset
    data.to_csv(os.path.join(output_path, "processed.csv"), header=False, index=False)
