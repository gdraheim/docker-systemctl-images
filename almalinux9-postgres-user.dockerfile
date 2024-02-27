FROM almalinux:9.3

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.8065"

ENV PG /var/lib/pgsql/data
ARG USERNAME=testuser_OK
ARG PASSWORD=P@ssw0rd.b653db8c755f29eb5754860e5e77
ARG TESTUSER=testuser_11
ARG TESTPASS=P@ssw0rd.a68a359519169eda6db6ed2d01fb
ARG LISTEN=*
ARG ALLOWS=0.0.0.0/0
EXPOSE 5432

COPY files/docker/systemctl3.py /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl
RUN echo sslverify=false >> /etc/yum.conf
RUN yum install -y postgresql-server postgresql-contrib procps
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

RUN yum install -y glibc-minimal-langpack
RUN export LC_ALL=en_US.UTF-8 ; LANG=en_US.UTF-8; postgresql-setup --initdb
RUN sed -i -e "s/.*listen_addresses.*/listen_addresses = '${LISTEN}'/" $PG/postgresql.conf
RUN sed -i -e "s/.*host.*ident/# &/" $PG/pg_hba.conf
RUN echo "host all all ${ALLOWS} md5" >> $PG/pg_hba.conf
RUN systemctl start postgresql \
   ; echo "CREATE USER ${TESTUSER} LOGIN ENCRYPTED PASSWORD '${TESTPASS}'" | runuser -u postgres /usr/bin/psql \
   ; echo "CREATE USER ${USERNAME} LOGIN ENCRYPTED PASSWORD '${PASSWORD}'" | runuser -u postgres /usr/bin/psql \
   ; systemctl stop postgresql

RUN systemctl enable postgresql
CMD /usr/bin/systemctl
USER postgres
# postgresql.service does already contain a "User=" entry
