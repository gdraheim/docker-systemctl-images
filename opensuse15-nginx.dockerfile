FROM opensuse/leap:15.1

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.4264"
EXPOSE 80

RUN zypper install -r repo-oss -y python3
COPY files/docker/systemctl3.py /usr/bin/systemctl
RUN zypper install -r repo-oss -y nginx 
COPY files/docker/systemctl3.py /usr/bin/systemctl

RUN echo TEST_OK > /srv/www/htdocs/index.html

RUN systemctl enable nginx
CMD /usr/bin/systemctl
