FROM centos:centos7

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.3.2177"

RUN yum search tomcat
RUN yum install -y tomcat tomcat-webapps
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN systemctl enable tomcat

EXPOSE 8080
USER tomcat
CMD /usr/bin/systemctl
