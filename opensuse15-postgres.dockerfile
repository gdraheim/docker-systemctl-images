FROM opensuse/leap:15.1

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.4264"

ENV PG /var/lib/pgsql/data
ARG USERNAME=testuser_OK
ARG PASSWORD=Testuser.OK
ARG LISTEN=*
ARG ALLOWS=0.0.0.0/0
EXPOSE 5432

RUN zypper install -r repo-oss -y python3
COPY files/docker/systemctl3.py /usr/bin/systemctl
RUN zypper --no-gpg-checks search -s postgresql
RUN zypper install -y postgresql-server postgresql-contrib
COPY files/docker/systemctl3.py /usr/bin/systemctl

# RUN rpm -q --list postgresql10-server
RUN ls -l /var/lib/pgsql
RUN mkdir /var/lib/pgsql/data ; chown postgres /var/lib/pgsql/data
RUN runuser -u postgres -- initdb -D /var/lib/pgsql/data
RUN sed -i -e "s/.*listen_addresses.*/listen_addresses = '${LISTEN}'/" $PG/postgresql.conf
RUN sed -i -e "s/.*host.*ident/# &/" $PG/pg_hba.conf
RUN echo "host all all ${ALLOWS} md5" >> $PG/pg_hba.conf
RUN systemctl start postgresql \
   ; echo "CREATE USER testuser_11 LOGIN ENCRYPTED PASSWORD 'Testuser.11'" | runuser -u postgres /usr/bin/psql \
   ; echo "CREATE USER ${USERNAME} LOGIN ENCRYPTED PASSWORD '${PASSWORD}'" | runuser -u postgres /usr/bin/psql \
   ; systemctl stop postgresql

RUN systemctl enable postgresql
CMD /usr/bin/systemctl
