# hadolint ignore=DL3007
FROM amlight/kytos:latest

ARG branch_kytos_sdx=main

COPY . /src/kytos-sdx
RUN python3 -m pip install --no-cache-dir -e /src/kytos-sdx
