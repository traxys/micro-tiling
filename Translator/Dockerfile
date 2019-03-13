FROM alpine:latest

RUN apk add python3 py3-pip dumb-init gnupg
RUN pip3 install pyinotify python-gnupg Flask python-etcd

WORKDIR /app
COPY . .

RUN mkdir jobs

EXPOSE 80

ENTRYPOINT [ "/usr/bin/dumb-init", "--", "/app/start.sh" ]
