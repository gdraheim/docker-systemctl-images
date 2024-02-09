FROM centos:7.9.2009

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.8065"
EXPOSE 8200
ARG NAME=localhost

RUN yum install -y mc python
COPY files/docker/systemctl.py /usr/bin/systemctl.py
COPY files/vault/vault.py /srv/vault.py
RUN yum install -y openssl
RUN openssl req -new -x509 -keyout /srv/$NAME.pem -out /srv/$NAME.pem -days 365 -nodes -batch

RUN { echo "[Service]" ; echo "Environment=VAULT_SSL_KEY=/srv/$NAME.pem" \
    ; echo "ExecStart=/srv/vault.py server -address=https://127.0.0.1:8200" \
    ; } > /etc/systemd/system/vault.service

CMD ["/usr/bin/systemctl.py", "init", "vault.service"]
