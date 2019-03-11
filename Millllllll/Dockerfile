FROM jfloff/alpine-python:latest

RUN apk update
RUN apk add py-psycopg2
RUN pip3 install grpcio
RUN pip3 install protobuf

WORKDIR olala
COPY . .

EXPOSE 5001 3333
CMD [ "./init.sh" ]
