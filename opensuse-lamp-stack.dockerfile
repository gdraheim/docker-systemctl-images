FROM opensuse:42.3

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.3.2177"

ENV WEB_CONF="/etc/apache2/conf.d/phpMyAdmin.conf"
ENV INC_CONF="/etc/phpMyAdmin/config.inc.php"
ENV INDEX_PHP="/srv/www/htdocs/index.php"

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN zypper install -r oss -y python
RUN zypper install -r oss -y apache2 apache2-utils mariadb-server mariadb-tools php5 phpMyAdmin
RUN echo "<?php phpinfo(); ?>" > ${INDEX_PHP}
RUN sed -i 's|ip 127.0.0.1|ip 172.0.0.0/8|' ${WEB_CONF}
RUN systemctl start mysql -vvv \
  ; mysqladmin -uroot password 'N0.secret' \
  ; echo "CREATE USER testuser_OK IDENTIFIED BY 'Testuser.OK'" | mysql -uroot -pN0.secret \
  ; systemctl stop mysql -vvv 
RUN sed -i -e "/'user'/s|=.*;|='testuser_OK';|" ${INC_CONF}
RUN sed -i -e "/'password'/s|=.*;|='Testuser.OK';|" ${INC_CONF}
RUN systemctl enable mysql
RUN systemctl enable apache2

EXPOSE 80
CMD /usr/bin/systemctl
