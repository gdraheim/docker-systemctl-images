FROM centos:8.1.1911

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.7106"
ARG PASSWORD=P@ssw0rd.788daa5d938373fe628f1dbe8d0c319c5606c4d3e857eb7
EXPOSE 22

# RUN yum install -y epel-release
RUN yum install -y passwd
RUN yum search sshd
RUN yum install -y openssh-server
RUN rpm -q --list openssh-server

COPY files/docker/systemctl3.py /usr/bin/systemctl3.py
RUN sed -i -e "s|/usr/bin/python3|/usr/libexec/platform-python|" /usr/bin/systemctl3.py
RUN cp /usr/bin/systemctl3.py /usr/bin/systemctl

# > systemctl cat sshd
# Wants=sshd-keygen.target

RUN systemctl enable sshd-keygen.target --force
RUN systemctl enable sshd
RUN rm -vf /run/nologin

#
RUN yum install -y openssh-clients
RUN rpm -q --list openssh-clients
RUN useradd -g nobody testuser
RUN echo $PASSWORD | passwd --stdin testuser
RUN TZ=UTC date -I > /home/testuser/date.txt
CMD /usr/bin/systemctl
