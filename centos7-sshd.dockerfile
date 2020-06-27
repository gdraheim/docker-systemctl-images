FROM centos:7.7.1908

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.4256"
ARG PASSWORD=Test.P@ssw0rd
EXPOSE 22

# RUN yum install -y epel-release
RUN yum search sshd
RUN yum install -y openssh-server
RUN rpm -q --list openssh-server
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN : \
  ; mkdir /etc/systemd/system/sshd-keygen.service.d \
  ; { echo "[Install]"; echo "WantedBy=multi-user.target"; } \
        > /etc/systemd/system/sshd-keygen.service.d/enabled.conf
RUN systemctl enable sshd-keygen
RUN systemctl enable sshd
#
RUN yum install -y openssh-clients
RUN rpm -q --list openssh-clients
RUN useradd -g nobody testuser
RUN echo $PASSWORD | passwd --stdin testuser
RUN date -I > /home/testuser/date.txt
CMD /usr/bin/systemctl
