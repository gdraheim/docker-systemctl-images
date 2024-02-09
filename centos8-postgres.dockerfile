FROM centos:8.5.2111

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.8065"

ENV PG /var/lib/pgsql/data
ARG USERNAME=testuser_OK
ARG PASSWORD=P@ssw0rd.bca446713c7498e62850722da36bd680
ARG TESTUSER=testuser_11
ARG TESTPASS=P@ssw0rd.390baab0b82d21f7a831476df0f632aa
ARG LISTEN=*
ARG ALLOWS=0.0.0.0/0
EXPOSE 5432

COPY files/docker/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl3.py

RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl
RUN yum install -y postgresql-server postgresql-contrib
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
