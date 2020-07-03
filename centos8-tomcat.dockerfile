FROM centos:8.1.1911

###################################################################
### WARNING: tomcat-webapps was removed from CENTOS 8 (07/2020) ###
###################################################################

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.4256"
EXPOSE 8080

RUN yum search tomcat
RUN yum install -y tomcat tomcat-webapps
COPY files/docker/systemctl3.py /usr/bin/systemctl
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl

RUN systemctl enable tomcat
CMD /usr/bin/systemctl
