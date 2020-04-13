FROM opensuse:42.3

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.4147"

ENV WEB_CONF="/etc/apache2/conf.d/phpMyAdmin.conf"
ENV INC_CONF="/etc/phpMyAdmin/config.inc.php"
ENV INDEX_PHP="/srv/www/htdocs/index.php"
ARG USERNAME=testuser_ok
ARG PASSWORD=Testuser.OK
ARG LISTEN=172.0.0.0/8
EXPOSE 80

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN zypper install -r oss -y python
RUN zypper install -r oss -y apache2 apache2-utils mariadb-server mariadb-tools php5 phpMyAdmin

RUN echo "<?php phpinfo(); ?>" > ${INDEX_PHP}
RUN sed -i "s|ip 127.0.0.1|ip ${LISTEN}|" ${WEB_CONF}
RUN systemctl start mysql -vvv \
  ; mysqladmin -uroot password 'N0.secret' \
  ; echo "CREATE USER ${USERNAME} IDENTIFIED BY '${PASSWORD}'" | mysql -uroot -pN0.secret \
  ; systemctl stop mysql -vvv 
RUN sed -i -e "/'user'/s|=.*;|='${USERNAME}';|" \
           -e "/'password'/s|=.*;|='${PASSWORD}';|" ${INC_CONF}

RUN systemctl enable mysql
RUN systemctl enable apache2
CMD /usr/bin/systemctl
