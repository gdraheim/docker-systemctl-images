FROM centos:8.5.2111

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 27017
ARG MONGODB=4.4

COPY files/docker/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN { echo '[mongodb]' \
    ; echo 'name=MongoDB Repository' \
    ; echo 'baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/'${MONGODB}'/x86_64/' \
    ; echo 'gpgcheck=0' ; echo 'enabled=1' \
    ; } > /etc/yum.repos.d/mongodb.repo
# RUN yum makecache
RUN yum install -y mongodb-org-server mongodb-org-shell
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN sed -i "s|^  bindIp:.*|  bindIp: 0.0.0.0|" /etc/mongod.conf

RUN systemctl enable mongod

RUN touch /var/log/systemctl.debug.log
CMD /usr/bin/systemctl
