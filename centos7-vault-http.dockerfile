FROM centos:7.9.2009

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.6.4521"
EXPOSE 8200

COPY files/vault/vault.py /srv/vault.py

CMD ["/srv/vault.py","server","-address=http://127.0.0.1:8200"]
