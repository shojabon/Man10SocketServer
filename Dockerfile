FROM python:3.9-slim-buster

WORKDIR /man10shopv3

COPY . .
RUN pip3 install -r requirements.txt

CMD [ "python3", "main.py"]