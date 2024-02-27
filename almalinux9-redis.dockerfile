FROM almalinux:9.3

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 6379

COPY files/docker/systemctl3.py /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl
RUN echo sslverify=false >> /etc/yum.conf

# RUN yum install -y epel-release
RUN yum install -y redis
# RUN rpm -q --list redis; exit 1

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/redis.conf
# default was 'bind 127.0.0.1'

RUN systemctl enable redis
CMD /usr/bin/systemctl
