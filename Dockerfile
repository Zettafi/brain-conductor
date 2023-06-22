FROM python:3.11-slim
LABEL authors="Adam Englander"
EXPOSE 80
WORKDIR /home/app

# This should match the number of virtual cores you will dedicate
ENV WORKERS=2
ENV LOG_LEVEL=ERROR

ADD . .

RUN ["pip", "install", "."]

ENTRYPOINT python -m hypercorn --bind 0.0.0.0:80 --workers $WORKERS --access-logfile - --error-logfile - asgi:app:app
