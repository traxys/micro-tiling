FROM alpine:latest

RUN apk add python3 py3-pip gnupg py-numpy
RUN pip3 install aiosmtpd python-gnupg python-etcd

COPY . .

EXPOSE 8025

CMD [ "python3", "smtp-serv.py" ]
