FROM golang:alpine

RUN apk add python3 py3-pip gnupg py-numpy dumb-init git
RUN pip3 install aiosmtpd python-gnupg python-etcd
RUN go get -u github.com/EnsicoinDevs/ensicoincoin-cli

WORKDIR /app
COPY . .

EXPOSE 8025

ENTRYPOINT [ "/usr/bin/dumb-init", "--", "/app/start.sh" ]
