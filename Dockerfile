# syntax=docker/dockerfile:1

FROM python:3.7.13-slim-buster

WORKDIR /medication

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
EXPOSE 6500
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]