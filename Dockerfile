FROM amlight/kytos:latest
MAINTAINER Italo Valcy <italo@amlight.net>

ARG branch_kytos_sdx=main

RUN --mount=source=.,target=/src/kytos-sdx,type=bind \
    python3 -m pip install -e /src/kytos-sdx
