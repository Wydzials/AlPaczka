FROM python:3.8-slim
RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app
RUN pip3 install -r requirements.txt
ADD . /app
EXPOSE 8000
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000", "--worker-tmp-dir", "/dev/shm", "--workers", "6", "app:app", "--certfile=cert.pem", "--keyfile=key.pem"]
