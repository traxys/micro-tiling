FROM alpine:latest

RUN apk add python3 py3-pip build-base python3-dev
RUN pip3 install uvicorn quart python-etcd requests

WORKDIR /app
COPY . .

EXPOSE 8000

RUN chmod +x run.sh

CMD [ "./run.sh" ]
