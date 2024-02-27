FROM centos:8.5.2111

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 6379

COPY files/docker/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

# RUN yum install -y epel-release
RUN yum install -y redis
# RUN rpm -q --list redis

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis.conf
# default was 'bind 127.0.0.1'

RUN systemctl enable redis
CMD /usr/bin/systemctl
