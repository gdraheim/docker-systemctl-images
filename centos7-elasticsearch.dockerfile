FROM centos:7.7.1908

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.5.4147"
EXPOSE 9200

RUN mkdir /srv/ElasticSearch
COPY Software/ElasticSearch /srv/ElasticSearch
RUN ls -l /srv/ElasticSearch
COPY files/docker/systemctl.py /usr/bin/systemctl

RUN yum install -y httpd java # required
RUN yum install -y httpd which # TODO: missing requirement of elasticsearch
RUN yum install -y /srv/ElasticSearch/*.rpm
RUN touch /var/log/systemctl.log

RUN systemctl enable elasticsearch
CMD /usr/bin/systemctl
