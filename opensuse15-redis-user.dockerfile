FROM opensuse/leap:15.1

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.6.4521"
ARG PASSWORD=P@ssw0rd.7702d0fa8c57c1a2aa87a6758f6c326d7de5
EXPOSE 6379

RUN zypper install -r repo-oss -y python3
COPY files/docker/systemctl3.py /usr/bin/systemctl
RUN zypper install -r repo-oss -y redis
COPY files/docker/systemctl3.py /usr/bin/systemctl

# initial setup
RUN cp -p /etc/redis/default.conf.example /etc/redis/default.conf
RUN runuser -u redis -- touch /var/log/redis/default.log
##ensured:# RUN chown redis:redis /etc/redis/default.conf
##ensured:# RUN chown redis:redis /var/log/redis/default.log

RUN sed -i "s/^bind .*/bind 0.0.0.0/" /etc/redis/default.conf
RUN sed -i "s/^#* *requirepass .*/requirepass $PASSWORD/" /etc/redis/default.conf

RUN systemctl enable redis@default
# RUN systemctl disable kbdsettings
RUN systemctl daemon-reload

## RUN touch /var/log/systemctl.debug.log
CMD /usr/bin/systemctl  # FIXME
# CMD /usr/bin/systemctl init redis@default
USER redis

