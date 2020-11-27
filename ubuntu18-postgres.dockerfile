FROM "ubuntu:18.04"

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.4264"

ENV PG /var/lib/postgresql/10/main
ENV CNF_FILE /etc/postgresql/10/main/postgresql.conf
ENV HBA_FILE /etc/postgresql/10/main/pg_hba.conf
ENV LOG_FILE /var/log/postgresql/postgresql-10-main.log
ENV POSTGRES postgresql@10-main
ARG USERNAME=testuser_OK
ARG PASSWORD=Testuser.OK
ARG LISTEN=*
ARG ALLOWS=0.0.0.0/0
EXPOSE 5432

RUN apt-get update
RUN apt-get install -y python3
COPY files/docker/systemctl3.py /usr/bin/systemctl
RUN test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl

RUN apt-cache search postgres
RUN apt-get install -y postgresql postgresql-contrib
COPY files/docker/systemctl3.py /usr/bin/systemctl

RUN pg_conftool show all
RUN sed -i -e "s/.*listen_addresses.*/listen_addresses = '${LISTEN}'/" $CNF_FILE
RUN sed -i -e "s/.*host.*ident/# &/" $HBA_FILE
RUN echo "host all all ${ALLOWS} md5" >> $HBA_FILE
# RUN systemctl start $POSTGRES -vvvv ; cat $LOG_FILE

RUN systemctl start $POSTGRES \
   ; echo "CREATE USER testuser_11 LOGIN ENCRYPTED PASSWORD 'Testuser.11'" | runuser -u postgres /usr/bin/psql \
   ; echo "CREATE USER ${USERNAME} LOGIN ENCRYPTED PASSWORD '${PASSWORD}'" | runuser -u postgres /usr/bin/psql \
   ; systemctl stop $POSTGRES

RUN systemctl enable $POSTGRES
RUN rm -f /etc/init.d/postgresql /etc/init.d/sysstat /etc/init.d/cron
CMD /usr/bin/systemctl -1
