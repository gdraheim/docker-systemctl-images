FROM centos:7.9.2009

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.4264"

ENV PG /var/lib/pgsql/data
ARG USERNAME=testuser_OK
ARG PASSWORD=P@ssw0rd.e78728245ccd67701da110fba33f7b
ARG TESTUSER=testuser_11
ARG TESTPASS=P@ssw0rd.4dc5892aeb685f2df254d4f23c5041
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
   ; echo "CREATE USER ${TESTUSER} LOGIN ENCRYPTED PASSWORD '${TESTPASS}'" | runuser -u postgres /usr/bin/psql \
   ; echo "CREATE USER ${USERNAME} LOGIN ENCRYPTED PASSWORD '${PASSWORD}'" | runuser -u postgres /usr/bin/psql \
   ; systemctl stop postgresql

RUN systemctl enable postgresql
CMD /usr/bin/systemctl
