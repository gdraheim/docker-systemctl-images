FROM almalinux:9.3

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
ARG PORT=8080
EXPOSE $PORT

COPY files/docker/systemctl3.py /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl
RUN echo sslverify=false >> /etc/yum.conf
RUN yum install -y httpd httpd-tools procps
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN echo TEST_OK > /var/www/html/index.html
RUN sed -i "s|^Listen .*|Listen $PORT|" /etc/httpd/conf/httpd.conf

RUN : \
  ; mkdir /usr/lib/systemd/system/httpd.service.d \
  ; { echo "[Service]" ; echo "User=apache"; } \
    > /usr/lib/systemd/system/httpd.service.d/usermode.conf
RUN : \
  ; chown -R apache /etc/httpd \
  ; chown -R apache /usr/share/httpd \
  ; chown -R apache /run/httpd \
  ; : chown -R apache /var/log/httpd \
  ; rm /etc/httpd/logs \
  ; mkdir /var/www/logs \
  ; ln -s /var/www/logs /etc/httpd \
  ; chown -R apache /var/www

RUN systemctl enable httpd
CMD /usr/bin/systemctl
USER apache
