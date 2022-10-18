FROM python:3.7-slim AS base
WORKDIR /home/auto-tool
ENV phone=''
ENV password=''
COPY user.py user.py
COPY requirements.txt requirements.txt
CMD pip install -r requirements.txt
CMD python user.py