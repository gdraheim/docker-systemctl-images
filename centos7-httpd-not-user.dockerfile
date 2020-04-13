FROM centos:7.7.1908

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.4147"
EXPOSE 80

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y httpd httpd-tools
COPY files/docker/systemctl.py /usr/bin/systemctl

RUN echo TEST_OK > /var/www/html/index.html

RUN systemctl enable httpd
CMD /usr/bin/systemctl
USER apache
# but can not be run in --user mode
