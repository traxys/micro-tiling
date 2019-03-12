FROM alpine:latest

RUN apk add python py-pip curl unzip dbus-x11 ttf-freefont firefox-esr xvfb py-pip curl dbus-x11 ttf-freefont firefox-esr xvfb python3 py-pip py-psycopg2 dumb-init
RUN pip3 install pyvirtualdisplay selenium pyvirtualdisplay python-etcd

WORKDIR /app
COPY . .

RUN cp geckodriver /usr/local/bin
RUN chmod +x /usr/local/bin/geckodriver

EXPOSE 1337

ENTRYPOINT [ "/usr/bin/dumb-init", "--", "/app/start.sh" ]
