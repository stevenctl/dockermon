FROM ubuntu

RUN apt-get update &&   \
    apt-get install -y  \
        tcpdump         \
        docker.io

CMD tcpdump -i eth0