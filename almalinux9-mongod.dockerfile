FROM almalinux:9.3

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 27017
ARG MONGODB=7.0

COPY files/docker/systemctl3.py /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl
RUN echo sslverify=false >> /etc/yum.conf

RUN { echo '[mongodb]' \
    ; echo 'name=MongoDB Repository' \
    ; echo 'baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/'${MONGODB}'/x86_64/' \
    ; echo 'gpgcheck=0' ; echo 'enabled=1' \
    ; } > /etc/yum.repos.d/mongodb.repo
# RUN yum makecache
# RUN yum search mongo; exit 1
RUN yum install -y mongodb-org-server mongodb-mongosh
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN sed -i "s|^  bindIp:.*|  bindIp: 0.0.0.0|" /etc/mongod.conf

RUN systemctl enable mongod

RUN touch /var/log/systemctl.debug.log
CMD /usr/bin/systemctl
