FROM alpine:latest

RUN apk add python3 py3-pip python3-dev build-base dumb-init
RUN pip3 install Flask python-etcd grpcio protobuf

WORKDIR /app
COPY . .

EXPOSE 80

ENTRYPOINT [ "/usr/bin/dumb-init", "--", "/app/start.sh" ]
