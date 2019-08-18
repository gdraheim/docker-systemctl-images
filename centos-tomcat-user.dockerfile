FROM centos:7.5.1804

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.4.3325"
EXPOSE 8080

RUN yum search tomcat
RUN yum install -y tomcat tomcat-webapps
COPY files/docker/systemctl.py /usr/bin/systemctl

RUN systemctl enable tomcat
CMD /usr/bin/systemctl
USER tomcat
# tomcat.service does already contain a "User=" entry
