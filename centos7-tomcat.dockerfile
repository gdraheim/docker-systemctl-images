FROM centos:7.9.2009

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 8080

RUN yum search tomcat
RUN yum install -y tomcat tomcat-webapps
COPY files/docker/systemctl.py /usr/bin/systemctl

RUN systemctl enable tomcat
CMD /usr/bin/systemctl
