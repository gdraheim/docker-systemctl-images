#! /bin/bash
here=`dirname "$0"`
exec ansible-playbook $here/elasticsearch.playbook.yml -e base_image="centos:7.4.1708" -v $options


