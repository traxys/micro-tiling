FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7

RUN apk add gnupg py3-psycopg2
RUN pip install pyinotify python-gnupg
RUN pip install python-etcd

COPY . /app
