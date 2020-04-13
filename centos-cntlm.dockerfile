FROM centos:7.7.1908

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.4.4147"
ARG ALLOWS=172.0.0.0/8
EXPOSE 3128

RUN yum install -y epel-release
RUN yum search cntlm
RUN yum install -y cntlm 
COPY files/docker/systemctl.py /usr/bin/systemctl
RUN : \
  ; sed -i -e "s/^Listen.*/Listen 0.0.0.0:3128/" /etc/cntlm.conf \
  ; sed -i -e "/Deny/a\\" -e "Allow 127.0.0.1" /etc/cntlm.conf \
  ; sed -i -e "/Deny/a\\" -e "Allow ${ALLOWS}" /etc/cntlm.conf \
  ; sed -i -e "/NoProxy/a\\" -e "NoProxy ${ALLOWS}, www.google.com" /etc/cntlm.conf \
  ; :
RUN : \
  ; mkdir /etc/systemd/system/cntlm.service.d \
  ; { echo "[Service]"; echo "PIDFile=/run/cntlm/cntlmd.pid"; } \
        > /etc/systemd/system/cntlm.service.d/pidfile.conf

RUN systemctl enable cntlm
CMD /usr/bin/systemctl
