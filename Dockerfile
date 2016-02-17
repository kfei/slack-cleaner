FROM python:2.7

MAINTAINER kfei <kfei@kfei.net>

RUN pip install slack-cleaner

VOLUME ["/backup"]

WORKDIR /backup

ENTRYPOINT ["/bin/bash"]
