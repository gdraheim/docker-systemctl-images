FROM centos:7.7.1908

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.4264"
EXPOSE 6379

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y epel-release
RUN yum install -y redis
# RUN rpm -q --list redis
COPY files/docker/systemctl.py /usr/bin/systemctl

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis.conf
# default was 'bind 127.0.0.1'

RUN systemctl enable redis
CMD /usr/bin/systemctl
