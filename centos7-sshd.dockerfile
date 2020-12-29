FROM centos:7.9.2009

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.6.4521"
ARG PASSWORD=P@ssw0rd.21a2dc7b77dacae44b050710903477400ca1c77fa9
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
RUN TZ=UTC date -I > /home/testuser/date.txt
CMD /usr/bin/systemctl
