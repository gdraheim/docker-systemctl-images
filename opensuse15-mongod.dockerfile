FROM opensuse/leap:15.1

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.7106"
EXPOSE 27017

RUN zypper install -r repo-oss -y python3
COPY files/docker/systemctl3.py /usr/bin/systemctl

RUN zypper addrepo "https://repo.mongodb.org/zypper/suse/15/mongodb-org/4.4/x86_64/" mongodb
RUN zypper --no-gpg-checks install -y mongodb-org
COPY files/docker/systemctl3.py /usr/bin/systemctl

RUN sed -i "s|^  bindIp:.*|  bindIp: 0.0.0.0|" /etc/mongod.conf

RUN systemctl enable mongod

RUN touch /var/log/systemctl.debug.log
CMD /usr/bin/systemctl
