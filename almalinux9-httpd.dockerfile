FROM centos:8.5.2111

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 80

COPY files/docker/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl3.py

RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl
RUN yum install -y httpd httpd-tools
COPY files/docker/systemctl3.py /usr/bin/systemctl
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN echo TEST_OK > /var/www/html/index.html

RUN systemctl enable httpd
CMD /usr/bin/systemctl
