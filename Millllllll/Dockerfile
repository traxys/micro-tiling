FROM alpine:latest

RUN apk add python python3 py3-pip py-pip build-base python3-dev
RUN pip3 install grpcio protobuf python-etcd
RUN pip install supervisor supervisor-stdout

WORKDIR olala
COPY . .

ENV DATABASE_HOST=localhost
ENV DATABASE_PORT=2379

RUN mkdir -p /olala/gopher/files

EXPOSE 5001 3333

ENTRYPOINT [ "supervisord", "-c", "/olala/supervisord.conf" ]
