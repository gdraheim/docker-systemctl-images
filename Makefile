F= files/docker/systemctl.py
B= 2016
FOR=today

version1:
	@ grep -l __version__ */*.??* */*/*.??* | { while read f; do echo $$f; done; } 

version:
	@ grep -l __version__ */*.??* */*/*.??* *.py *.cfg *.dockerfile | { while read f; do : \
	; Y=`date +%Y -d "$(FOR)"` ; X=$$(expr $$Y - $B); D=`date +%W%u -d "$(FOR)"` ; sed -i \
	-e "/^ *version =/s/[.]-*[0123456789][0123456789][0123456789]*/.$$X$$D/" \
	-e "/^ *__version__/s/[.]-*[0123456789][0123456789][0123456789]*\"/.$$X$$D\"/" \
	-e "/^ *__version__/s/[.]\\([0123456789]\\)\"/.\\1.$$X$$D\"/" \
	-e "/^ *__copyright__/s/(C) [0123456789]*-[0123456789]*/(C) $B-$$Y/" \
	-e "/^ *__copyright__/s/(C) [0123456789]* /(C) $$Y /" \
	$$f; done; }
	@ grep ^__version__ files/*/*.??*

help:
	python files/docker/systemctl.py help
copy cp:
	cp -v ../docker-systemctl-replacement/files/docker/systemctl.py files/docker/systemctl.py
	cp -v ../docker-systemctl-replacement/files/docker/systemctl3.py files/docker/systemctl3.py
	cp -v ../docker-systemctl-replacement/docker_mirror.py .
	cp -v ../docker-systemctl-replacement/docker_mirror.pyi .
2: copy

alltests: CH CP UA DJ
.PHONY: tests
tests: alltests

CH centos-httpd.dockerfile: ; ./testbuilds.py test_701
CP centos-postgres.dockerfile: ; ./testbuilds.py test_702
UA ubuntu-apache2.dockerfile: ; ./testbuilds.py test_721
DJ docker-jenkins: ; ./testbuilds.py test_90*

check: ;  ./testbuilds.py -vv 
check3: ; ./testbuilds.py -vv "test_[178]"
test_%: ; ./testbuilds.py $@ -vv -P `date +Pass.%d.%m` $X
real_%: ; ./testbuilds.py $@ -vv -P `date +Pass.%d.%m` $X

3: tmp/systemctl3.py
tmp/systemctl.py tmp/systemctl3.py : files/docker/systemctl.py
	test -d tmp || mkdir tmp
	cp files/docker/systemctl.py $@
	sed -i -e "s|/usr/bin/python|/usr/bin/python3|" $@

op opensuse: ; ./testbuilds.py make_opensuse
ub ubuntu:   ; ./testbuilds.py make_ubuntu
ce centos:   ; ./testbuilds.py make_centos

clean:
	- rm -rf tmp/tmp.test_*

############################ CHECK
AUTOPEP8=autopep8
%.py.pep8: %.py
	$(AUTOPEP8) $(@:.pep8=) --in-place
	git --no-pager diff $(@:.pep8=)

pep style: 
	$(MAKE) testbuilds.py.pep8

############################ XTRA

-include Makefile.qtest
