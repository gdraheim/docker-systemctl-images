FROM centos:8.1.1911

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.4264"
EXPOSE 27017

COPY files/docker/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN { echo '[mongodb-org-4.4]' \
    ; echo 'name=MongoDB Repository' \
    ; echo 'baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/4.4/x86_64/' \
    ; echo 'gpgcheck=0' ; echo 'enabled=1' \
    ; } > /etc/yum.repos.d/mongodb-org-4.4.repo
RUN yum install -y mongodb-org
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN sed -i "s|^  bindIp:.*|  bindIp: 0.0.0.0|" /etc/mongod.conf

RUN systemctl enable mongod

RUN touch /var/log/systemctl.debug.log
CMD /usr/bin/systemctl
