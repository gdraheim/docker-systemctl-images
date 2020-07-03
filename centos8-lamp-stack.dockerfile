FROM centos:8.1.1911

###############################################################################
### WARNING: the phpmyadmin package has not been ported to EPEL 8 (07/2020) ###
###############################################################################

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.4264"

ENV WEB_CONF="/etc/httpd/conf.d/phpMyAdmin.conf"
ENV INC_CONF="/etc/phpMyAdmin/config.inc.php"
ENV INDEX_PHP="/var/www/html/index.php"
ARG USERNAME=testuser_ok
ARG PASSWORD=Testuser.OK
ARG LISTEN=172.0.0.0/8
EXPOSE 80

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl
RUN yum install -y dnf-plugins-core
RUN yum config-manager --set-enabled PowerTools
RUN yum install -y epel-release
RUN yum repolist

RUN yum install -y httpd httpd-tools mariadb-server mariadb php phpmyadmin
RUN echo "<?php phpinfo(); ?>" > ${INDEX_PHP}
RUN sed -i "s|ip 127.0.0.1|ip ${LISTEN}|" ${WEB_CONF}
RUN systemctl start mariadb -vvv \
  ; mysqladmin -uroot password 'N0.secret' \
  ; echo "CREATE USER ${USERNAME} IDENTIFIED BY '${PASSWORD}'" | mysql -uroot -pN0.secret \
  ; systemctl stop mariadb -vvv 
RUN sed -i -e "/'user'/s|=.*;|='${USERNAME}';|" \
           -e "/'password'/s|=.*;|='${PASSWORD}';|" ${INC_CONF}

RUN systemctl enable mariadb
RUN systemctl enable httpd
CMD /usr/bin/systemctl
