FROM "ubuntu:18.04"

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 6379

RUN apt-get update
RUN apt-get install -y python3
COPY files/docker/systemctl3.py /usr/bin/systemctl

RUN apt-cache search redis
RUN apt-get install -y redis-server
COPY files/docker/systemctl3.py /usr/bin/systemctl

# RUN dpkg-query -L redis-server
RUN chown redis /var/log # FIXME /var/log/journal(/redis.service.log)

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/redis.conf
# default was 'bind 127.0.0.1'

RUN systemctl enable redis
#FIXME# CMD /usr/bin/systemctl
CMD /usr/bin/systemctl init redis
USER redis
