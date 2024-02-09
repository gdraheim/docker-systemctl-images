FROM centos:8.1.1911

###################################################################
### WARNING: tomcat-webapps was removed from CENTOS 8 (07/2020) ###
###################################################################

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 8080

COPY files/docker/systemctl3.py /usr/bin/systemctl
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl
# RUN yum install -y dnf-plugins-core
# RUN yum config-manager --set-enabled PowerTools
# RUN yum install -y epel-release
# RUN yum repolist

RUN yum search tomcat
RUN yum install -y tomcat tomcat-webapps

RUN systemctl enable tomcat
CMD /usr/bin/systemctl
