FROM python:3-slim
WORKDIR /app

ADD app.py .
ADD requirements.txt .
COPY static ./static
COPY templates ./templates

RUN python3 -m pip install -r requirements.txt

CMD "python3" "app.py"