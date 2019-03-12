FROM alpine:latest

RUN apk add python python3 py3-pip py-pip build-base python3-dev
RUN pip3 install grpcio protobuf python-etcd
RUN pip install supervisor

WORKDIR olala
COPY . .

EXPOSE 5001 3333
ENTRYPOINT [ "supervisord", "--nodaemon", "--configuration", "/olala/supervisord.conf" ]
