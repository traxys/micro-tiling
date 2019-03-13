FROM golang:alpine

RUN apk add python3 py3-pip dumb-init git
RUN pip3 install python-etcd
RUN go get -u github.com/EnsicoinDevs/ensicoincoin-cli

WORKDIR /app
COPY . .

EXPOSE 2442

ENTRYPOINT [ "/usr/bin/dumb-init", "--", "/app/start.sh" ]
