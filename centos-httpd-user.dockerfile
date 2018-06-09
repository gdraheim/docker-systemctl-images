FROM centos:centos7

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.3.2177"

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y httpd httpd-tools
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN systemctl enable httpd
RUN echo TEST_OK > /var/www/html/index.html

RUN sed -i 's|^Listen .*|Listen 8080|' /etc/httpd/conf/httpd.conf
RUN sed -i "/Type=notify/a\\User=apache" /usr/lib/systemd/system/httpd.service

RUN chown -R apache /etc/httpd
RUN chown -R apache /usr/share/httpd
RUN chown -R apache /run/httpd
# RUN chown -R apache /var/log/httpd
RUN rm /etc/httpd/logs
RUN mkdir /var/www/logs
RUN ln -s /var/www/logs /etc/httpd

RUN chown -R apache /var/www

EXPOSE 8080
USER apache
CMD /usr/bin/systemctl
