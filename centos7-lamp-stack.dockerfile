FROM centos:7.9.2009

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"

ENV WEB_CONF="/etc/httpd/conf.d/phpMyAdmin.conf"
ENV INC_CONF="/etc/phpMyAdmin/config.inc.php"
ENV INDEX_PHP="/var/www/html/index.php"
ARG USERNAME=testuser_ok
ARG PASSWORD=P@ssw0rd.1b89e38af6966558c1a1714e15828b9bfea996f91e6f
ARG TESTPASS=P@ssw0rd.rwCh2gAEqgMXBUHwKtDQVD1oP2croTMLgtKr.9fUidQ.
ARG LISTEN=172.0.0.0/8
EXPOSE 80

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y epel-release           psmisc
RUN echo 'sslverify=false' >> /etc/yum.conf
RUN cat /etc/yum.repos.d/epel.repo
RUN curl 'https://mirrors.fedoraproject.org/metalink?repo=epel-7&arch=x86_64'
RUN yum repolist
RUN yum install -y httpd httpd-tools mariadb-server mariadb php phpmyadmin
RUN echo "<?php phpinfo(); ?>" > ${INDEX_PHP}
RUN sed -i "s|ip 127.0.0.1|ip ${LISTEN}|" ${WEB_CONF}
RUN systemctl start mariadb -vvv \
  ; mysqladmin -uroot password ${TESTPASS} \
  ; echo "CREATE USER ${USERNAME} IDENTIFIED BY '${PASSWORD}'" | mysql -uroot -p${TESTPASS} \
  ; systemctl stop mariadb -vvv 
RUN sed -i -e "/'user'/s|=.*;|='${USERNAME}';|" \
           -e "/'password'/s|=.*;|='${PASSWORD}';|" ${INC_CONF}

RUN systemctl enable mariadb
RUN systemctl enable httpd
CMD /usr/bin/systemctl
