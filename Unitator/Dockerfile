FROM leafney/alpine-selenium-firefox:latest

RUN apk add python3 py-pip
RUN pip3 install pyvirtualdisplay selenium

WORKDIR /app
COPY . .

EXPOSE 1337
CMD [ "./init.sh" ]
