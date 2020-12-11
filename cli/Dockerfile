FROM python:3.8-slim
RUN mkdir /cli
WORKDIR /cli
ADD requirements.txt /cli
RUN pip3 install -r requirements.txt
ADD . /cli
CMD ["python3", "cli.py"]
