FROM golang:latest AS build-env

WORKDIR /src

COPY maildiranasaurus .

RUN go get github.com/flashmob/maildiranasaurus/cmd/maildiranasaurus
RUN make dependencies
RUN make maildiranasaurus

FROM alpine

WORKDIR /app

RUN apk add file
COPY --from=build-env /src/maildiranasaurus .
COPY cruxingator .

RUN mkdir /mail

EXPOSE 25

CMD [ "./init.sh" ]
