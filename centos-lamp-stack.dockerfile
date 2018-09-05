FROM centos:7.5.1804

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.0.2177"

ENV WEB_CONF="/etc/httpd/conf.d/phpMyAdmin.conf"
ENV INC_CONF="/etc/phpMyAdmin/config.inc.php"
ENV INDEX_PHP="/var/www/html/index.php"

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y epel-release
RUN yum repolist
RUN yum install -y httpd httpd-tools mariadb-server mariadb php phpmyadmin
RUN echo "<?php phpinfo(); ?>" > ${INDEX_PHP}
RUN sed -i 's|ip 127.0.0.1|ip 172.0.0.0/8|' ${WEB_CONF}
RUN systemctl start mariadb -vvv \
  ; mysqladmin -uroot password 'N0.secret' \
  ; echo "CREATE USER testuser_OK IDENTIFIED BY 'Testuser.OK'" | mysql -uroot -pN0.secret \
  ; systemctl stop mariadb -vvv 
RUN sed -i -e "/'user'/s|=.*;|='testuser_OK';|" ${INC_CONF}
RUN sed -i -e "/'password'/s|=.*;|='Testuser.OK';|" ${INC_CONF}
RUN systemctl enable mariadb
RUN systemctl enable httpd

EXPOSE 80
CMD /usr/bin/systemctl
