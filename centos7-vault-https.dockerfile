FROM centos:7.9.2009

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.6.4521"
EXPOSE 8200
ARG NAME=localhost

RUN yum install -y mc python
COPY files/docker/systemctl.py /usr/bin/systemctl.py
COPY files/vault/vault.py /srv/vault.py
RUN yum install -y openssl
RUN cp /usr/bin/systemctl.py /usr/bin/systemctl ; systemctl version
RUN openssl req -new -x509 -keyout /srv/$NAME.pem -out /srv/$NAME.pem -days 365 -nodes -batch

RUN { echo "[Service]" ; echo "Environment=VAULT_SSL_KEY=/srv/$NAME.pem" \
    ; echo "ExecStart=/srv/vault.py server -address=https://127.0.0.1:8200" \
    ; echo "[Install]" ; echo "WantedBy=multi-user.target" \
    ; } > /etc/systemd/system/vault.service

RUN systemctl enable vault.service
# RUN touch /var/log/systemctl.debug.log
CMD /usr/bin/systemctl.py
