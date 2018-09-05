FROM centos:7.5.1804

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.0.2177"

RUN mkdir /srv/ElasticSearch
COPY Software/ElasticSearch /srv/ElasticSearch
RUN ls -l /srv/ElasticSearch
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y httpd java # required
RUN yum install -y httpd which # TODO: missing requirement of elasticsearch
RUN yum install -y /srv/ElasticSearch/*.rpm
RUN systemctl enable elasticsearch
RUN touch /var/log/systemctl.log

EXPOSE 9200
CMD /usr/bin/systemctl
