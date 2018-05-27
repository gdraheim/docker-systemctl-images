# docker systemctl images

This project will use the docker-systemctl-replacement script
to build realistic images of common software into a systemd
controlled distribution.

See https://github.com/gdraheim/docker-systemctl-replacement

## History

Using a ansible and a dockerfile to build images of common
software did even exist before the testsuite.py of the
original docker-systemctl-replacement project was created.
Just a couple of Makefile lines were used start and stop
the necessary containers and images.

In version 1.0 of docker-systemctl-replacement these parts
were integrated into the testsuite.py where they were now
named test_6xxx (later test_7xxx) for the dockerfile based
tests and test_9xxxx for the ansible based test scenarios.
When moving to version 1.3 of docker-systemctl-replacement
these parts were cut out into a separate project on github
named docker-systemctl-images.

In the docker-systemctl-replacement project the resulting
images were just temporary while docker-systemctl-images
will keep the results. These may be used directly for
further usage in other projects. The tests on the images
are still performed and in general they run before the
output image is tagged on its 'savename'. As such the
script is not called testbuilds.py

## Overview

The main targets are webservers and databases as being
the basis of other projects. The big free distros like 
centos and ubuntu are generally the most common target
here.

The original author of docker-systemctl-replacement is
commonly using the systemctl.py script along with
ansible as the software deployments but allow to 
provision on a real machine or a docker container. The
first example here is a Jenkins setup.

## The author

Guido Draheim is working as a freelance consultant for
multiple big companies in Germany. This project is related 
to the current surge of DevOps topics which often use docker 
as a lightweight replacement for cloud containers or even 
virtual machines. It makes it easier to test deployments
in the standard build pipelines of development teams.


