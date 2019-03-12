FROM alpine:latest

RUN apk add python3 py3-pip python3-dev build-base
RUN pip3 install Flask python-etcd grpcio protobuf

WORKDIR /app
COPY . .

EXPOSE 80

ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]
