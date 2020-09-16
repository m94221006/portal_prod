FROM ubuntu:xenial

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y build-essential libssl-dev libffi-dev && \
    apt-get install -y python3.6 python3.6-dev python3-pip && \
    apt-get install -y vim

WORKDIR /app
COPY ./requirements.txt .
RUN rm -f /usr/bin/python && ln -s /usr/bin/python3.6 /usr/bin/python
RUN rm -f /usr/bin/python3 && ln -s /usr/bin/python3.6 /usr/bin/python3

RUN pip3 install -r requirements.txt

ADD ./backend /app/backend
ADD ./docker /app/docker






