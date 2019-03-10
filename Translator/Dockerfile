FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7

RUN apk add gnupg
RUN pip install pyinotify python-gnupg 

COPY . /app
