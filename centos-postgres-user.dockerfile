FROM centos:7.5.1804

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.4.3325"

ENV PG /var/lib/pgsql/data
ARG USERNAME=testuser_OK
ARG PASSWORD=Testuser.OK
ARG LISTEN=*
ARG ALLOWS=0.0.0.0/0
EXPOSE 5432

COPY files/docker/systemctl.py /usr/bin/systemctl
RUN yum install -y postgresql-server postgresql-utils
COPY files/docker/systemctl.py /usr/bin/systemctl

RUN postgresql-setup initdb
RUN sed -i -e "s/.*listen_addresses.*/listen_addresses = '${LISTEN}'/" $PG/postgresql.conf
RUN sed -i -e "s/.*host.*ident/# &/" $PG/pg_hba.conf
RUN echo "host all all ${ALLOWS} md5" >> $PG/pg_hba.conf
RUN systemctl start postgresql \
   ; echo "CREATE USER testuser_11 LOGIN ENCRYPTED PASSWORD 'Testuser.11'" | runuser -u postgres /usr/bin/psql \
   ; echo "CREATE USER ${USERNAME} LOGIN ENCRYPTED PASSWORD '${PASSWORD}'" | runuser -u postgres /usr/bin/psql \
   ; systemctl stop postgresql

RUN systemctl enable postgresql
CMD /usr/bin/systemctl
USER postgres
# postgresql.service does already contain a "User=" entry
