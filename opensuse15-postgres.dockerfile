FROM opensuse/leap:15.1

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.7106"

ENV PG /var/lib/pgsql/data
ARG USERNAME=testuser_OK
ARG PASSWORD=P@ssw0rd.013c864e44b8840ea76ec985dad7f09f
ARG TESTUSER=testuser_11
ARG TESTPASS=P@ssw0rd.49f40a217bf71f309d619e27a18cf6a2
ARG LISTEN=*
ARG ALLOWS=0.0.0.0/0
EXPOSE 5432

RUN zypper install -r repo-oss -y python3
COPY files/docker/systemctl3.py /usr/bin/systemctl
RUN zypper --no-gpg-checks search -s postgresql
RUN zypper install -y postgresql-server postgresql-contrib
COPY files/docker/systemctl3.py /usr/bin/systemctl

## NOTE that PG=/var/lib/pgsql/data is created on the first 'start'
RUN systemctl start postgresql \
   ; echo "CREATE USER ${TESTUSER} LOGIN ENCRYPTED PASSWORD '${TESTPASS}'" | runuser -u postgres /usr/bin/psql \
   ; echo "CREATE USER ${USERNAME} LOGIN ENCRYPTED PASSWORD '${PASSWORD}'" | runuser -u postgres /usr/bin/psql \
   ; systemctl stop postgresql
RUN sed -i -e "s/.*listen_addresses.*/listen_addresses = '${LISTEN}'/" $PG/postgresql.conf
RUN sed -i -e "s/.*host.*ident/# &/" $PG/pg_hba.conf
RUN echo "host all all ${ALLOWS} md5" >> $PG/pg_hba.conf

RUN systemctl enable postgresql
CMD /usr/bin/systemctl
