FROM opensuse/leap:15.1

LABEL __copyright__="(C) Guido U. Draheim, licensed under the EUPL" \
      __version__="1.5.4264"
ARG PASSWORD=P@ssw0rd.e404e3ef41d5425af5ca357dbe90e346a53fb2d0a9b8e
EXPOSE 22

RUN zypper install -r repo-oss -y python3
COPY files/docker/systemctl3.py /usr/bin/systemctl
RUN zypper --no-gpg-checks search ssh
RUN zypper install -y openssh
# RUN rpm -q --list openssh
COPY files/docker/systemctl3.py /usr/bin/systemctl

RUN systemctl enable sshd
RUN useradd -g users testuser -m
RUN echo testuser:$PASSWORD | chpasswd
RUN TZ=UTC date -I > /home/testuser/date.txt
CMD /usr/bin/systemctl
