FROM centos:7.9.2009

LABEL __copyright__="(C) Guido Draheim, licensed under the EUPL" \
      __version__="1.6.4521"
EXPOSE 9200
ARG VERSION=6.8

RUN mkdir /srv/ElasticSearch
COPY Software/ElasticSearch /srv/ElasticSearch
RUN ls -l /srv/ElasticSearch
COPY files/docker/systemctl.py /usr/bin/systemctl

RUN yum install -y httpd java # required
RUN yum install -y httpd which # TODO: missing requirement of elasticsearch
RUN yum install -y /srv/ElasticSearch/elasticsearch-$VERSION*.rpm
RUN sed -i -e "s/.*network.host:.*/network.host: 0.0.0.0/"  /etc/elasticsearch/elasticsearch.yml
RUN touch /var/log/systemctl.log

RUN systemctl enable elasticsearch
CMD /usr/bin/systemctl
