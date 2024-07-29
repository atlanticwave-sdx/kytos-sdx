FROM amlight/kytos:latest
MAINTAINER Italo Valcy <italo@amlight.net>

ARG branch_kytos_sdx=main

COPY . /src/kytos-sdx
RUN python3 -m pip install -e /src/kytos-sdx
