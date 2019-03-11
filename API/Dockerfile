FROM golang:latest as build-env

RUN mkdir /app
WORKDIR /app

COPY go.mod .
COPY go.sum .

RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /go/bin/app

FROM scratch

COPY --from=build-env /go/bin/app /go/bin/app
COPY --from=build-env /app /app

WORKDIR /app

EXPOSE 8080

ENTRYPOINT [ "/go/bin/app" ]
