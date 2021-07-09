FROM python:3.7-slim-buster

COPY sagemaker /

RUN pip3 install -r ./requirements.txt
