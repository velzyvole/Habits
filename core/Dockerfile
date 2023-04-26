FROM --platform=linux/amd64 python:3.9.9-slim-buster
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN apt-get update -y
RUN apt-get install gcc -y
RUN pip install -r requirements.txt
COPY . /code
