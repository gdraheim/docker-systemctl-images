#! /usr/bin/env python3
""" Testcases for docker-systemctl-replacement functionality """

from __future__ import print_function

__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "1.5.7106"

# NOTE:
# The testcases 1000...4999 are using a --root=subdir environment
# The testcases 5000...9999 will start a docker container to work.

import subprocess
import os.path
import time
import datetime
import unittest
import shutil
import inspect
import types
import string
import random
import logging
import re
from fnmatch import fnmatchcase as fnmatch
from glob import glob
import json
import sys

if sys.version[0] == '3':
    basestring = str
    xrange = range

logg = logging.getLogger("TESTING")
_epel7 = False
_opensuse14 = False
_python2 = "/usr/bin/python"
_python3 = "/usr/bin/python3"
_python = ""
_systemctl_py = "files/docker/systemctl3.py"
_top_recent = "ps -eo etime,pid,ppid,args --sort etime,pid | grep '^ *0[0123]:[^ :]* ' | grep -v -e ' ps ' -e ' grep ' -e 'kworker/'"
_top_list = "ps -eo etime,pid,ppid,args --sort etime,pid"

SAVETO = "localhost:5000/systemctl"
IMAGES = "localhost:5000/systemctl/image"
CENTOS7 = "centos:7.7.1908"
CENTOS = "almalinux:9.1"
UBUNTU = "ubuntu:22.04"
OPENSUSE = "opensuse/leap:15.5"

_curl = "curl"
_curl_timeout4 = "--max-time 4"
_docker = "docker"
DOCKER_SOCKET = "/var/run/docker.sock"
PSQL_TOOL = "/usr/bin/psql"
PLAYBOOK_TOOL = "/usr/bin/ansible-playbook"
RUNTIME = "/tmp/run-"

_maindir = os.path.dirname(sys.argv[0])
_mirror = os.path.join(_maindir, "docker_mirror.py")
_password = ""

def decodes(text):
    if text is None: return None
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try:
            return text.decode(encoded)
        except:
            return text.decode("latin-1")
    return text
def sh____(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.check_call(cmd, shell=shell)
def sx____(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.call(cmd, shell=shell)
def output(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return out
def output2(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
    out, err = run.communicate()
    return decodes(out), run.returncode
def output3(cmd, shell=True):
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    run = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = run.communicate()
    return decodes(out), decodes(err), run.returncode
def background(cmd, shell=True):
    BackgroundProcess = collections.namedtuple("BackgroundProcess", ["pid", "run", "log"])
    log = open(os.devnull, "wb")
    run = subprocess.Popen(cmd, shell=shell, stdout=log, stderr=log)
    pid = run.pid
    logg.info("PID %s = %s", pid, cmd)
    return BackgroundProcess(pid, run, log)


def _lines(lines):
    if isinstance(lines, basestring):
        lines = lines.split("\n")
        if len(lines) and lines[-1] == "":
            lines = lines[:-1]
    return lines
def lines(text):
    lines = []
    for line in _lines(text):
        lines.append(line.rstrip())
    return lines
def grep(pattern, lines):
    for line in _lines(lines):
        if re.search(pattern, line.rstrip()):
            yield line.rstrip()
def greps(lines, pattern):
    return list(grep(pattern, lines))

def download(base_url, filename, into):
    if not os.path.isdir(into):
        os.makedirs(into)
    if not os.path.exists(os.path.join(into, filename)):
        curl = _curl
        sh____("cd {into} && {curl} -O {base_url}/{filename}".format(**locals()))
def text_file(filename, content):
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w")
    if content.startswith("\n"):
        x = re.match("(?s)\n( *)", content)
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                line = line[len(indent):]
            f.write(line + "\n")
    else:
        f.write(content)
    f.close()
def shell_file(filename, content):
    text_file(filename, content)
    os.chmod(filename, 0o770)
def copy_file(filename, target):
    targetdir = os.path.dirname(target)
    if not os.path.isdir(targetdir):
        os.makedirs(targetdir)
    shutil.copyfile(filename, target)
def copy_tool(filename, target):
    copy_file(filename, target)
    os.chmod(target, 0o750)

def get_caller_name():
    frame = inspect.currentframe().f_back.f_back
    return frame.f_code.co_name
def get_caller_caller_name():
    frame = inspect.currentframe().f_back.f_back.f_back
    return frame.f_code.co_name
def os_path(root, path):
    if not root:
        return path
    if not path:
        return path
    while path.startswith(os.path.sep):
        path = path[1:]
    return os.path.join(root, path)
def docname(path):
    return os.path.splitext(os.path.basename(path))[0]

class DockerSystemctlReplacementTest(unittest.TestCase):
    def caller_testname(self):
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1 + 1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix=None):
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def testport(self):
        testname = self.caller_testname()
        m = re.match("test_([0123456789]+)", testname)
        if m:
            port = int(m.group(1))
            if 5000 <= port and port <= 9999:
                return port
        seconds = int(str(int(time.time()))[-4:])
        return 6000 + (seconds % 2000)
    def testdir(self, testname=None):
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp." + testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname=None):
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp." + testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        return newdir
    def makedirs(self, path):
        if not os.path.isdir(path):
            os.makedirs(path)
    def real_folders(self):
        yield "/etc/systemd/system"
        yield "/var/run/systemd/system"
        yield "/usr/lib/systemd/system"
        yield "/lib/systemd/system"
        yield "/etc/init.d"
        yield "/var/run/init.d"
        yield "/var/run"
        yield "/etc/sysconfig"
        yield "/etc/systemd/system/multi-user.target.wants"
        yield "/usr/bin"
    def rm_zzfiles(self, root):
        for folder in self.real_folders():
            for item in glob(os_path(root, folder + "/zz*")):
                logg.info("rm %s", item)
                os.remove(item)
            for item in glob(os_path(root, folder + "/test_*")):
                logg.info("rm %s", item)
                os.remove(item)
    def root(self, testdir, real=None):
        if real: return "/"
        root_folder = os.path.join(testdir, "root")
        if not os.path.isdir(root_folder):
            os.makedirs(root_folder)
        return os.path.abspath(root_folder)
    def newpassword(self):
        if _password:
            return _password
        out = "Password."
        out += random.choice(string.ascii_uppercase)
        out += random.choice(string.ascii_lowercase)
        out += random.choice(string.ascii_lowercase)
        out += random.choice(string.ascii_lowercase)
        out += random.choice(string.ascii_lowercase)
        out += random.choice(",.-+")
        out += random.choice("0123456789")
        out += random.choice("0123456789")
        return out
    def user(self):
        import getpass
        getpass.getuser()
    def ip_container(self, name):
        docker = _docker
        cmd = "{docker} inspect {name}"
        values = output(cmd.format(**locals()))
        values = json.loads(values)
        if not values or "NetworkSettings" not in values[0]:
            logg.critical(" docker inspect %s => %s ", name, values)
        return values[0]["NetworkSettings"]["IPAddress"]
    def local_image(self, image):
        """ attach local centos-repo / opensuse-repo to docker-start enviroment.
            Effectivly when it is required to 'docker start centos:x.y' then do
            'docker start centos-repo:x.y' before and extend the original to 
            'docker start --add-host mirror...:centos-repo centos:x.y'. """
        if os.environ.get("NONLOCAL", ""):
            return image
        add_hosts = self.start_mirror(image)
        if add_hosts:
            return "{add_hosts} {image}".format(**locals())
        return image
    def local_addhosts(self, dockerfile, extras=None):
        image = ""
        for line in open(dockerfile):
            m = re.match('[Ff][Rr][Oo][Mm] *"([^"]*)"', line)
            if m:
                image = m.group(1)
                break
            m = re.match("[Ff][Rr][Oo][Mm] *(\w[^ ]*)", line)
            if m:
                image = m.group(1).strip()
                break
        logg.debug("--\n-- '%s' FROM '%s'", dockerfile, image)
        if image:
            return self.start_mirror(image, extras)
        return ""
    def start_mirror(self, image, extras=None):
        extras = extras or ""
        docker = _docker
        mirror = _mirror
        cmd = "{mirror} start {image} --add-hosts {extras}"
        out = output(cmd.format(**locals()))
        return decodes(out).strip()
    def drop_container(self, name):
        docker = _docker
        cmd = "{docker} rm --force {name}"
        sx____(cmd.format(**locals()))
    def drop_centos(self):
        self.drop_container("centos")
    def drop_ubuntu(self):
        self.drop_container("ubuntu")
    def drop_opensuse(self):
        self.drop_container("opensuse")
    def make_opensuse(self):
        self.make_container("opensuse", OPENSUSE)
    def make_ubuntu(self):
        self.make_container("ubuntu", UBUNTU)
    def make_centos(self):
        self.make_container("centos", CENTOS)
    def make_container(self, name, image):
        self.drop_container(name)
        docker = _docker
        local_image = self.local_image(image)
        cmd = "{docker} run --detach --name {name} {local_image} sleep 1000"
        sh____(cmd.format(**locals()))
        print("                 # " + local_image)
        print("  {docker} exec -it {name} bash".format(**locals()))
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    def test_1001_systemctl_testfile(self):
        """ the systemctl.py file to be tested does exist """
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        logg.info("...")
        logg.info("testname %s", testname)
        logg.info(" testdir %s", testdir)
        logg.info("and root %s", root)
        target = "/usr/bin/systemctl"
        target_folder = os_path(root, os.path.dirname(target))
        os.makedirs(target_folder)
        target_systemctl = os_path(root, target)
        shutil.copy(_systemctl_py, target_systemctl)
        self.assertTrue(os.path.isfile(target_systemctl))
        self.rm_testdir()
    def test_1002_systemctl_version(self):
        systemctl = _systemctl_py
        cmd = "{systemctl} --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "systemd 219"))
        self.assertTrue(greps(out, "via systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
    def real_1002_systemctl_version(self):
        cmd = "systemctl --version"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, r"systemd [234]\d\d"))
        self.assertFalse(greps(out, "via systemctl.py"))
        self.assertTrue(greps(out, "[+]SYSVINIT"))
    def test_1003_systemctl_help(self):
        """ the '--help' option and 'help' command do work """
        systemctl = _systemctl_py
        cmd = "{systemctl} --help"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertTrue(greps(out, "--root=PATH"))
        self.assertTrue(greps(out, "--verbose"))
        self.assertTrue(greps(out, "--init"))
        self.assertTrue(greps(out, "for more information"))
        self.assertFalse(greps(out, "reload-or-try-restart"))
        cmd = "{systemctl} help"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertEqual(end, 0)
        self.assertFalse(greps(out, "--verbose"))
        self.assertTrue(greps(out, "reload-or-try-restart"))
    def test_2007_centos7_httpd_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7 and python2, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        name = "centos7-httpd"
        dockerfile = "centos7-httpd.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2008_centos8_httpd_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 8 and python3, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using python3 on centos:8")
        testname = self.testname()
        testdir = self.testdir()
        name = "centos8-httpd"
        dockerfile = "centos8-httpd.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2047_centos7_httpd_not_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7 and python2, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
             AND in this variant it runs under User=httpd right
               there from PID-1 started implicity in --user mode
            THEN it fails."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        testname = self.testname()
        testdir = self.testdir()
        name = "centos7-httpd"
        dockerfile = "centos7-httpd-not-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname} sleep 300"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "{docker} exec {testname} systemctl start httpd --user"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit httpd.service not for --user mode"))
        cmd = "{docker} exec {testname} /usr/sbin/httpd -DFOREGROUND"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unable to open logs"))
        # self.assertTrue(greps(err, "could not bind to address 0.0.0.0:80"))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2048_centos8_httpd_not_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 8 and python3, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
             AND in this variant it runs under User=httpd right
               there from PID-1 started implicity in --user mode
            THEN it fails."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using python3 on centos:8")
        testname = self.testname()
        testdir = self.testdir()
        name = "centos7-httpd"
        dockerfile = "centos8-httpd-not-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname} sleep 300"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "{docker} exec {testname} systemctl start httpd --user"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unit httpd.service not for --user mode"))
        cmd = "{docker} exec {testname} /usr/sbin/httpd -DFOREGROUND"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 1)
        self.assertTrue(greps(err, "Unable to open logs"))
        # self.assertTrue(greps(err, "could not bind to address 0.0.0.0:80"))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2057_centos7_httpd_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7 and python2, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
             AND in this variant it runs under User=httpd right
               there from PID-1 started implicity in --user mode.
            THEN it succeeds if modified"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        name = "centos7-httpd"
        dockerfile = "centos7-httpd-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname} sleep 300"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start httpd --user"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 0)
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}:8080"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "apache.*python.*systemctl"))
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2058_centos8_httpd_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 8 and python3, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
             AND in this variant it runs under User=httpd right
               there from PID-1 started implicity in --user mode.
            THEN it succeeds if modified"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using python3 on centos:8")
        testname = self.testname()
        testdir = self.testdir()
        name = "centos8-httpd"
        dockerfile = "centos8-httpd-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname} sleep 300"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start httpd --user"
        out, err, end = output3(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s\n%s", cmd, end, out, err)
        self.assertEqual(end, 0)
        cmd = "{docker} rm -f {testname}"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}:8080"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "apache.*python.*systemctl"))
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2114_ubuntu_apache2(self):
        """ WHEN using a systemd enabled Ubuntu as the base image
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        self.skipTest("test_216 makes it through a dockerfile")
        testname = self.testname()
        testdir = self.testdir()
        saveto = SAVETO
        images = IMAGES
        basename = "ubuntu:16.04"
        savename = "ubuntu-apache2-test"
        image = self.local_image(basename)
        python_base = os.path.basename(_python or _python3)
        systemctl_py = _systemctl_py
        logg.info("%s:%s %s", testname, port, basename)
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run --detach --name={testname} {image} sleep 200"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} apt-get update"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} apt-get install -y apache2 {python_base}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {systemctl_py} {testname}:/usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'test -L /bin/systemctl || ln -sf /usr/bin/systemctl /bin/systemctl'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl enable apache2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'echo TEST_OK > /var/www/html/index.html'"
        sh____(cmd.format(**locals()))
        # .........................................
        cmd = "{docker} commit -c 'CMD [\"/usr/bin/systemctl\"]'  {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2116_ubuntu16_apache2(self):
        """ WHEN using a dockerfile for systemd enabled Ubuntu 16 with python2
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "ubuntu16-apache2.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2118_ubuntu18_apache2(self):
        """ WHEN using a dockerfile for systemd enabled Ubuntu 18 with python3
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "ubuntu18-apache2.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2122_ubuntu22_apache2(self):
        """ WHEN using a dockerfile for systemd enabled Ubuntu 22 with python3
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "ubuntu22-apache2.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2215_opensuse15_apache2_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 8 and python3, 
            THEN we can create an image with an Apache HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        name = "opensuse15-apache2"
        dockerfile = "opensuse15-apache2.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_2315_opensuse15_nginx_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 8 and python3, 
            THEN we can create an image with an NGINX HTTP service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can download the root html showing 'OK'
            because the test script has placed an index.html
            in the webserver containing that text. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "opensuse15-nginx.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 5; {curl} -o {testdir}/{testname}.txt http://{container}"
        sh____(cmd.format(**locals()))
        cmd = "grep OK {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3007_centos7_postgres_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7 and python2, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        name = "centos7-postgres"
        dockerfile = "centos7-postgres.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        testpass = "Test." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3008_centos8_postgres_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 8 and python3, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using python3 on centos:8")
        testname = self.testname()
        testdir = self.testdir()
        name = "centos8-postgres"
        dockerfile = "centos8-postgres.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        testpass = "Test." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3215_opensuse15_postgres_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Opensuse15 and python3, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "opensuse15-postgres.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        testpass = "Pass." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3318_ubuntu18_postgres_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Ubuntu 16.04 and python3, 
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
            Without a special startup.sh script or container-cmd 
            one can just start the image and in the container
            expecting that the service is started. Therefore,
            WHEN we start the image as a docker container
            THEN we can see a specific role with an SQL query
            because the test script has created a new user account 
            in the in the database with a known password. """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "ubuntu18-postgres.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        testpass = "Test." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3457_centos7_postgres_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7 and python2,
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
             AND in this variant it runs under User=postgres right
               there from PID-1 started implicity in --user mode."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        name = "centos7-postgres"
        dockerfile = "centos7-postgres-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        runtime = RUNTIME
        password = self.newpassword()
        testpass = "Pass." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        uid = "postgres"
        cmd = "{docker} exec {testname} id -u {uid}"
        out = output(cmd.format(**locals()))
        if out: uid = decodes(out).strip()
        cmd = "{docker} exec {testname} ls {runtime}{uid}/run"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'for i in 1 2 3 4 5 ; do wc -l {runtime}{uid}/run/postgresql.service.status && break; sleep 2; done'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:{runtime}{uid}/run/postgresql.service.status {testdir}/postgresql.service.status"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "postgres.*python.*systemctl"))
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3458_centos8_postgres_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 8 and python3,
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled.
             AND in this variant it runs under User=postgres right
               there from PID-1 started implicity in --user mode."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using python3 on centos:8")
        testname = self.testname()
        testdir = self.testdir()
        name = "centos8-postgres"
        dockerfile = "centos8-postgres-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        runtime = RUNTIME
        password = self.newpassword()
        testpass = "Test." + password
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --build-arg TESTPASS={testpass} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        uid = "postgres"
        cmd = "{docker} exec {testname} id -u {uid}"
        out = output(cmd.format(**locals()))
        if out: uid = decodes(out).strip()
        cmd = "{docker} exec {testname} ls {runtime}{uid}/run"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'for i in 1 2 3 4 5 ; do wc -l {runtime}{uid}/run/postgresql.service.status && break; sleep 2; done'"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:{runtime}{uid}/run/postgresql.service.status {testdir}/postgresql.service.status"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "postgres.*python.*systemctl"))
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3487_centos7_postgres_playbook(self):
        """ WHEN using a playbook for systemd-enabled CentOS 7 and python2,
            THEN we can create an image with an PostgreSql DB service 
                 being installed and enabled."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        name = "centos7-postgres"
        playbook = "centos7-postgres-docker.yml"
        savename = docname(playbook)
        saveto = SAVETO
        images = saveto + "/postgres"
        psql = PSQL_TOOL
        runtime = RUNTIME
        password = self.newpassword()
        testpass = "Pass." + password
        # WHEN
        users = "-e postgres_testuser=testuser_11 -e postgres_testpass={testpass} -e postgress_password={password}"
        cmd = "ansible-playbook {playbook} " + users + " -e tagrepo={saveto} -e tagversion={testname} -v"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        cmd = "for i in 1 2 3 4 5 6 7 8 9; do echo -n \"[$i] \"; pg_isready -h {container} && break; sleep 2; done"
        sh____(cmd.format(**locals()))
        # THEN
        login = "export PGUSER=testuser_11; export PGPASSWORD=" + testpass
        query = "SELECT rolname FROM pg_roles"
        cmd = "{login}; {psql} -h {container} -d postgres -c '{query}' > {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep testuser_ok {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3507_centos7_redis_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Centos7 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos7-redis.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}:{testname} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep PONG {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3508_centos8_redis_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Centos8 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos8-redis.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}:{testname} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep PONG {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3558_centos8_redis_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Centos8 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos8-redis-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}:{testname} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep PONG {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3715_opensuse15_redis_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Opensuse15 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "opensuse15-redis.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}:{testname} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep PONG {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3718_ubuntu18_redis_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Ubuntu18 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "ubuntu18-redis.dockerfile"
        addhosts = ""  # FIXME# self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}:{testname} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep PONG {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3768_ubuntu18_redis_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Ubuntu18 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "ubuntu18-redis-user.dockerfile"
        addhosts = ""  # FIXME# self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}:{testname} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep PONG {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        #
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3765_opensuse15_redis_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Opensuse15 and redis, 
            THEN check that redis replies to 'ping' with a 'PONG' 
            AND that AUTH works along with a USER process"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "opensuse15-redis-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}:{testname} sleep 3"
        sh____(cmd.format(**locals()))
        # cmd = "redis-cli -h {container} ping | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client redis-cli -h {container} -a {password} ping | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep PONG {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # USER
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3808_centos8_mongod_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled centos8 and mongod, 
            check that mongo can reply witha  hostInfo."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos8-mongod.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}:{testname} sleep 3"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client mongo --help"
        sh____(cmd.format(**locals()))
        # cmd = "mongo --host {container} --eval 'db.hostInfo()' | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client mongo --host {container} --eval 'db.hostInfo()' | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep 'MongoDB server version' {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3815_opensuse15_mongod_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Opensuse15 and mongod, 
            check that mongo can reply witha  hostInfo."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "opensuse15-mongod.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}:{testname} sleep 3"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client mongo --help"
        sh____(cmd.format(**locals()))
        # cmd = "mongo --host {container} --eval 'db.hostInfo()' | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client mongo --host {container} --eval 'db.hostInfo()' | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep 'MongoDB server version' {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_3818_ubuntu18_mongod_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Ubuntu18 and mongod,
            check that mongo can reply with a hostInfo."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "ubuntu18-mongod.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sx____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        cmd = "sleep 2"
        sh____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname}-client {images}:{testname} sleep 3"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client mongo --help"
        sh____(cmd.format(**locals()))
        # cmd = "mongo --host {container} --eval 'db.hostInfo()' | tee {testdir}/{testname}.txt"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec -t {testname}-client mongo --host {container} --eval 'db.hostInfo()' | tee {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep 'MongoDB server version' {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}-client"
        sh____(cmd.format(**locals()))
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5107_centos7_lamp_stack(self):
        """ Check setup of Linux/Apache/Mariadb/Php on CentOs 7 with python2"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not _epel7: self.skipTest("epel7 is dead (use --epel7 to enable test)")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        name = "centos7-lamp-stack"
        dockerfile = "centos7-lamp-stack.dockerfile"
        addhosts = self.local_addhosts(dockerfile, "--epel")
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(10):
            time.sleep(1)
            cmd = "{curl} -o {testdir}/result.txt http://{container}/phpMyAdmin/"
            out, err, end = output3(cmd.format(**locals()))
            if "503 Service Unavailable" in err:
                logg.info("[%i] ..... 503 %s", attempt, greps(err, "503 "))
                continue
            if "200 OK" in err:
                logg.info("[%i] ..... 200 %s", attempt, greps(err, "200 "))
                break
            text = open("{testdir}/result.txt".format(**locals())).read()
            if "503 Service Unavailable" in text:
                logg.info("[%i] ..... 503 %s", attempt, greps(text, "503 "))
                continue
            if "<h1>" in text:
                break
            logg.info(" %s =>%s\n%s", cmd, end, out)
            logg.info(" %s ->\n%s", cmd, text)
        cmd = "{curl} -o {testdir}/result.txt http://{container}/phpMyAdmin/"
        sh____(cmd.format(**locals()))
        cmd = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5108_centos8_lamp_stack(self):
        """ Check setup of Linux/Apache/Mariadb/Php on CentOs 8 with python3"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        name = "centos8-lamp-stack"
        dockerfile = "centos8-lamp-stack.dockerfile"
        addhosts = self.local_addhosts(dockerfile, "--epel")
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        logg.info("THEN")
        for attempt in xrange(20):
            time.sleep(1)
            cmd = "{curl} -o {testdir}/result.txt http://{container}/phpMyAdmin/"
            out, err, end = output3(cmd.format(**locals()))
            if "503 Service Unavailable" in err:
                logg.info("[%i] ..... 503 %s", attempt, greps(err, "503 "))
                continue
            if "200 OK" in err:
                logg.info("[%i] ..... 200 %s", attempt, greps(err, "200 "))
                break
            text = open("{testdir}/result.txt".format(**locals())).read()
            if "503 Service Unavailable" in text:
                logg.info("[%i] ..... 503 %s", attempt, greps(text, "503 "))
                continue
            if "<h1>" in text:
                break
            logg.info(" %s =>%s\n%s", cmd, end, out)
            logg.info(" %s ->\n%s", cmd, text)
        cmd = "{curl} -o {testdir}/result.txt http://{container}/phpMyAdmin/"
        sh____(cmd.format(**locals()))
        cmd = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5114_opensuse14_lamp_stack(self):
        """ Check setup of Linux/Apache/Mariadb/Php" on Opensuse"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not _opensuse14: self.skipTest("Opensuse 42.x is dead")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        name = "opensuse14-lamp-stack"
        dockerfile = "opensuse14-lamp-stack.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(10):
            time.sleep(1)
            cmd = "{curl} -o {testdir}/result.txt http://{container}/phpMyAdmin/"
            out, err, end = output3(cmd.format(**locals()))
            if "503 Service Unavailable" in err:
                logg.info("[%i] ..... 503 %s", attempt, greps(err, "503 "))
                continue
            if "200 OK" in err:
                logg.info("[%i] ..... 200 %s", attempt, greps(err, "200 "))
                break
            logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{curl} -o {testdir}/result.txt http://{container}/phpMyAdmin/"
        sh____(cmd.format(**locals()))
        cmd = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_5115_opensuse15_lamp_stack_php7(self):
        """ Check setup of Linux/Apache/Mariadb/Php" on Opensuse later than 15.x"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        name = "opensuse15-lamp-stack"
        dockerfile = "opensuse15-lamp-stack.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(10):
            time.sleep(1)
            cmd = "{curl} -o {testdir}/result.txt http://{container}/phpMyAdmin/"
            out, err, end = output3(cmd.format(**locals()))
            if "503 Service Unavailable" in err:
                logg.info("[%i] ..... 503 %s", attempt, greps(err, "503 "))
                continue
            if "200 OK" in err:
                logg.info("[%i] ..... 200 %s", attempt, greps(err, "200 "))
                break
            logg.info(" %s =>%s\n%s", cmd, end, out)
        cmd = "{curl} -o {testdir}/result.txt http://{container}/phpMyAdmin/"
        sh____(cmd.format(**locals()))
        cmd = "grep '<h1>.*>phpMyAdmin<' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6017_centos7_simple_vault(self):
        """ Check setup of Mock Vault in CentOS 7 """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python2
        python3 = _python3
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        dockerfile = "centos7-vault-http.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        docker = _docker
        vault = "files/vault/vault.py"
        password = self.newpassword()
        port = 8200
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        cmd = "{docker} exec {testname} /srv/vault.py write secret/mysecret value={password}"
        sh____(cmd.format(**locals()))
        cmd = "{python3} {vault} -address=http://{container}:{port} read secret/mysecret"
        sh____(cmd.format(**locals()))
        cmd = "{curl} -o {testdir}/result.txt http://{container}:{port}/v1/secret/mysecret"
        sh____(cmd.format(**locals()))
        cmd = "grep '{password}' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6107_centos7_sssl_vault(self):
        """ Check setup of Mock Vault in CentOS 7 """
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python2
        python3 = _python3
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        dockerfile = "centos7-vault-https.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        docker = _docker
        vault = "files/vault/vault.py"
        password = self.newpassword()
        port = 8200
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        time.sleep(1)
        container = self.ip_container(testname)
        cmd = "{docker} exec {testname} /srv/vault.py write secret/mysecret value={password}"
        sh____(cmd.format(**locals()))
        cmd = "{python3} {vault} -tls-skip-verify=yes -address=https://{container}:{port} read secret/mysecret"
        sh____(cmd.format(**locals()))
        cmd = "curl -k -o {testdir}/result.txt -- https://{container}:{port}/v1/secret/mysecret"
        sh____(cmd.format(**locals()))
        cmd = "grep '{password}' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6207_centos7_tomcat_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an tomcat service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos7-tomcat.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(30):
            cmd = "{curl} -o {testdir}/{testname}.txt http://{container}:8080/sample/"
            out, err, end = output3(cmd.format(**locals()))
            logg.info("(%s)=> %s\n%s", attempt, out, err)
            filename = "{testdir}/{testname}.txt".format(**locals())
            if os.path.exists(filename):
                txt = open(filename).read()
                if txt.strip(): break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/{testname}.txt http://{container}:8080/sample/"
        sh____(cmd.format(**locals()))
        cmd = "grep Hello {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    @unittest.expectedFailure
    def test_6208_centos8_tomcat_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 8, 
            THEN we can create an image with an tomcat service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using python3 on centos:8")
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos8-tomcat.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(30):
            cmd = "{curl} -o {testdir}/{testname}.txt http://{container}:8080/sample/"
            out, err, end = output3(cmd.format(**locals()))
            logg.info("(%s)=> %s\n%s", attempt, out, err)
            filename = "{testdir}/{testname}.txt".format(**locals())
            if os.path.exists(filename):
                txt = open(filename).read()
                if txt.strip(): break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/{testname}.txt http://{container}:8080/sample"
        sh____(cmd.format(**locals()))
        cmd = "grep Hello {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6307_centos7_tomcat_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an tomcat service 
                 being installed and enabled.
            In this case the container is run in --user mode."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos7-tomcat-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(30):
            cmd = "{curl} -o {testdir}/{testname}.txt http://{container}:8080/sample/"
            out, err, end = output3(cmd.format(**locals()))
            logg.info("(%s)=> %s\n%s", attempt, out, err)
            filename = "{testdir}/{testname}.txt".format(**locals())
            if os.path.exists(filename):
                txt = open(filename).read()
                if txt.strip(): break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/{testname}.txt http://{container}:8080/sample/"
        sh____(cmd.format(**locals()))
        cmd = "grep Hello {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} ps axu"
        out, end = output2(cmd.format(**locals()))
        logg.info(" %s =>%s\n%s", cmd, end, out)
        self.assertTrue(greps(out, "tomcat.*python.*systemctl"))
        self.assertFalse(greps(out, "root"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6407_centos7_cntlm_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an cntlm service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        max4 = _curl_timeout4
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos7-cntlm.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active cntlm"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "http_proxy={container}:3128 {curl} {max4} -o {testdir}/{testname}.txt http://www.google.com"
        # cmd = "sleep 5; http_proxy=127.0.0.1:3128 {curl} {max4} -o {testdir}/{testname}.txt http://www.google.com"
        sh____(cmd.format(**locals()))
        cmd = "grep '<img alt=.Google.' {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    @unittest.expectedFailure
    def test_6408_centos8_cntlm_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 8, 
            THEN we can create an image with an cntlm service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        max4 = _curl_timeout4
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos8-cntlm.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active cntlm"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "http_proxy={container}:3128 {curl} {max4} -o {testdir}/{testname}.txt http://www.google.com"
        # cmd = "sleep 5; http_proxy=127.0.0.1:3128 {curl} {max4} -o {testdir}/{testname}.txt http://www.google.com"
        sh____(cmd.format(**locals()))
        cmd = "grep '<img alt=.Google.' {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6507_centos7_cntlm_user_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an cntlm service 
                 being installed and enabled.
            In this case the container is run in --user mode."""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        max4 = _curl_timeout4
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos7-cntlm-user.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active cntlm"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "http_proxy={container}:3128 {curl} {max4} -o {testdir}/{testname}.txt http://www.google.com"
        # cmd = "http_proxy=127.0.0.1:3128 {curl} {max4} -o {testdir}/{testname}.txt http://www.google.com"
        sh____(cmd.format(**locals()))
        cmd = "grep '<img alt=.Google.' {testdir}/{testname}.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_6607_centos7_ssh_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 7, 
            THEN we can create an image with an ssh service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos7-sshd.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active sshd"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "{docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        cmd = "sshpass -p {password} scp {allows} testuser@{container}:date.txt {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        cmd = "sshpass -p {password} scp {allows} testuser@{container}:date.txt {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
        # logg.warning("centos-sshd is incomplete without .socket support in systemctl.py")
        # logg.warning("the scp call will succeed only once - the sshd is dead after that")
    def test_6608_centos8_ssh_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled CentOS 8, 
            THEN we can create an image with an ssh service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        if not python.endswith("python3"): self.skipTest("using python3 on centos:8")
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "centos8-sshd.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active sshd"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "{docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        cmd = "sleep 2; {docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        cmd = "sshpass -p {password} scp {allows} testuser@{container}:date.txt {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        cmd = "sshpass -p {password} scp {allows} testuser@{container}:date.txt {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
        # logg.warning("centos-sshd is incomplete without .socket support in systemctl.py")
        # logg.warning("the scp call will succeed only once - the sshd is dead after that")
    def test_6615_opensuse15_ssh_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled OpenSuse 15, 
            THEN we can create an image with an ssh service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "opensuse15-sshd.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active sshd"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "{docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        cmd = "sleep 2; {docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        cmd = "sshpass -p {password} scp {allows} testuser@{container}:date.txt {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        cmd = "sshpass -p {password} scp {allows} testuser@{container}:date.txt {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
        # logg.warning("centos-sshd is incomplete without .socket support in systemctl.py")
        # logg.warning("the scp call will succeed only once - the sshd is dead after that")
    def test_6618_ubuntu18_ssh_dockerfile(self):
        """ WHEN using a dockerfile for systemd-enabled Ubuntu 18, 
            THEN we can create an image with an ssh service 
                 being installed and enabled.
            Addtionally we do check an example application"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PSQL_TOOL): self.skipTest("postgres tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python3
        testname = self.testname()
        testdir = self.testdir()
        dockerfile = "ubuntu18-sshd.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        password = self.newpassword()
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --build-arg PASSWORD={password} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        container = self.ip_container(testname)
        # THEN
        for attempt in xrange(9):
            cmd = "{docker} exec {testname} /usr/bin/systemctl is-active ssh"
            out, end = output2(cmd.format(**locals()))
            logg.info("is-active => %s", out)
            time.sleep(1)
            if not end: break
        cmd = "{docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        cmd = "sleep 2; {docker} exec {testname} ps axu"
        sx____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl is-system-running"
        sx____(cmd.format(**locals()))
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        cmd = "sshpass -p {password} scp {allows} testuser@{container}:date.txt {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.txt"
        sh____(cmd.format(**locals()))
        allows = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        cmd = "sshpass -p {password} scp {allows} testuser@{container}:date.txt {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        cmd = "grep `TZ=UTC date -I` {testdir}/{testname}.date.2.txt"
        sh____(cmd.format(**locals()))
        #cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        # sh____(cmd.format(**locals()))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()

    def test_8407_centos_elasticsearch_setup(self):
        """ Check setup of ElasticSearch on CentOs via ansible docker connection"""
        # note that the test runs with a non-root 'ansible' user to reflect
        # a real deployment scenario using ansible in the non-docker world.
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        setupfile = "centos7-elasticsearch-setup.yml"
        savename = docname(setupfile)
        basename = CENTOS7
        saveto = SAVETO
        images = IMAGES
        image = self.local_image(basename)
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {image} sleep infinity"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} bash -c 'echo sslverify=false >> /etc/yum.conf'" # almalinux https
        sh____(cmd.format(**locals()))
        prepare = " --limit {testname} -e ansible_user=root"
        cmd = "ansible-playbook -i centos7-elasticsearch-setup.ini ansible-deployment-user.yml -vv" + prepare
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} grep __version__ /usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "ansible-playbook -i centos7-elasticsearch-setup.ini centos7-elasticsearch-setup.yml -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} grep __version__ /usr/bin/systemctl"
        sh____(cmd.format(**locals()))
        cmd = "{docker} commit -c 'CMD /usr/bin/systemctl' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in xrange(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        for attempt in xrange(3):
            cmd = "{docker} exec {testname} systemctl is-active elasticsearch"
            out, end = output2(cmd.format(**locals()))
            logg.info("elasticsearch {out}".format(**locals()))
            if out.strip() == "active": break
            time.sleep(1)
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_8507_centos7_elasticsearch_dockerfile(self):
        """ Check setup of ElasticSearch on CentOs via Dockerfile"""
        #### it depends on the download of the previous ansible test ####
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        base_url = "https://download.elastic.co/elasticsearch/elasticsearch"
        filename = "elasticsearch-1.7.3.noarch.rpm"
        into_dir = "Software/ElasticSearch"
        download(base_url, filename, into_dir)
        self.assertTrue(greps(os.listdir("Software/ElasticSearch"), filename))
        #
        testname = self.testname()
        testdir = self.testdir()
        root = self.root(testdir)
        port = self.testport()
        name = "centos7-elasticsearch"
        dockerfile = "centos7-elasticsearch.dockerfile"
        addhosts = self.local_addhosts(dockerfile)
        savename = docname(dockerfile)
        saveto = SAVETO
        images = IMAGES
        psql = PSQL_TOOL
        # WHEN
        cmd = "{docker} build . -f {dockerfile} {addhosts} --tag {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in xrange(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        for attempt in xrange(3):
            cmd = "{docker} exec {testname} systemctl is-active elasticsearch"
            out, end = output2(cmd.format(**locals()))
            logg.info("elasticsearch {out}".format(**locals()))
            if out.strip() == "active": break
            time.sleep(1)
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        # CHECK
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    @unittest.expectedFailure # can not find role in Ansible 2.9
    def test_8607_centos_elasticsearch_image(self):
        """ Check setup of ElasticSearch on CentOs via ansible playbook image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        playbook = "centos7-elasticsearch-image.yml"
        basename = CENTOS7  # "centos:7.3.1611"
        tagrepo = SAVETO
        tagname = "elasticsearch"
        #
        cmd = "ansible-playbook {playbook} -e base_image='{basename}' -e tagrepo={tagrepo} -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {tagrepo}/{tagname}:latest"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in xrange(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        self.rm_testdir()
    def test_8707_centos_elasticsearch_deploy(self):
        """ Check setup of ElasticSearch on CentOs via ansible docker connection"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        playbook = "centos7-elasticsearch-deploy.yml"
        savename = docname(playbook)
        basename = CENTOS7
        saveto = SAVETO
        images = IMAGES
        image = self.local_image(basename)
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {image} sleep infinity"
        sh____(cmd.format(**locals()))
        prepare = " --limit {testname} -e ansible_user=root"
        cmd = "ansible-playbook {playbook} -e container1={testname} -vv"
        sh____(cmd.format(**locals()))
        cmd = "{docker} commit -c 'CMD /usr/bin/systemctl' {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {images}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in xrange(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {saveto}/{savename}:latest"
        sx____(cmd.format(**locals()))
        cmd = "{docker} tag {images}:{testname} {saveto}/{savename}:latest"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rmi {images}:{testname}"
        sx____(cmd.format(**locals()))
        self.rm_testdir()
    def test_8807_centos_elasticsearch_docker(self):
        """ Check setup of ElasticSearch on CentOs via ansible playbook image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        playbook = "centos7-elasticsearch-docker.yml"
        basename = CENTOS7  # "centos:7.3.1611"
        tagrepo = SAVETO
        tagname = "elasticsearch"
        #
        cmd = "ansible-playbook {playbook} -e base_image='{basename}' -e tagrepo={tagrepo} -e tagversion={testname} -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {tagrepo}/{tagname}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in xrange(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        self.rm_testdir()
    def test_8907_centos_elasticsearch_docker_playbook(self):
        """ Check setup of ElasticSearch on CentOs via ansible playbook image"""
        if not os.path.exists(DOCKER_SOCKET): self.skipTest("docker-based test")
        if not os.path.exists(PLAYBOOK_TOOL): self.skipTest("ansible-playbook tools missing on host")
        docker = _docker
        curl = _curl
        python = _python or _python2
        if python.endswith("python3"): self.skipTest("no python3 on centos:7")
        testname = self.testname()
        testdir = self.testdir()
        playbook = "centos7-elasticsearch.docker.yml"
        basename = CENTOS7  # "centos:7.3.1611"
        tagrepo = SAVETO
        tagname = "elasticsearch"
        #
        cmd = "ansible-playbook {playbook} -e base_image='{basename}' -e tagrepo={tagrepo} -e tagversion={testname} -vv"
        sh____(cmd.format(**locals()))
        #
        cmd = "{docker} rm --force {testname}"
        sx____(cmd.format(**locals()))
        cmd = "{docker} run -d --name {testname} {tagrepo}/{tagname}:{testname}"
        sh____(cmd.format(**locals()))
        #
        container = self.ip_container(testname)
        logg.info("========================>>>>>>>>")
        cmd = "{docker} exec {testname} touch /var/log/systemctl.log"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl start elasticsearch -vvv"
        sh____(cmd.format(**locals()))
        # THEN
        for attempt in xrange(30):
            cmd = "{curl} http://{container}:9200/?pretty"
            out, end = output2(cmd.format(**locals()))
            logg.info("[{attempt}] ({end}): {out}".format(**locals()))
            if not end: break
            time.sleep(1)
        cmd = "{curl} -o {testdir}/result.txt http://{container}:9200/?pretty"
        sh____(cmd.format(**locals()))
        cmd = "grep 'You Know, for Search' {testdir}/result.txt"
        sh____(cmd.format(**locals()))
        # STOP
        cmd = "{docker} exec {testname} systemctl status elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} exec {testname} systemctl stop elasticsearch"
        sh____(cmd.format(**locals()))
        cmd = "{docker} cp {testname}:/var/log/systemctl.log {testdir}/systemctl.log"
        sh____(cmd.format(**locals()))
        # CHECK
        systemctl_log = open(testdir + "/systemctl.log").read()
        self.assertEqual(len(greps(systemctl_log, " ERROR ")), 0)
        self.assertTrue(greps(systemctl_log, "simple started PID"))
        self.assertTrue(greps(systemctl_log, "stop kill PID"))
        # SAVE
        cmd = "{docker} stop {testname}"
        sh____(cmd.format(**locals()))
        cmd = "{docker} rm --force {testname}"
        sh____(cmd.format(**locals()))
        self.rm_testdir()

if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n")[0])
    _o.add_option("-v", "--verbose", action="count", default=0,
                  help="increase logging level [%default]")
    _o.add_option("--with", metavar="FILE", dest="systemctl_py", default=_systemctl_py,
                  help="systemctl.py file to be tested (%default)")
    _o.add_option("--python3", metavar="EXE", default=_python3,
                  help="use another python2 execution engine [%default]")
    _o.add_option("--python2", metavar="EXE", default=_python2,
                  help="use another python execution engine [%default]")
    _o.add_option("-p", "--python", metavar="EXE", default=_python,
                  help="override the python execution engine [%default]")
    _o.add_option("-7", "--epel7", action="store_true", default=_epel7,
                  help="enable testbuilds requiring epel7 [%default]")
    _o.add_option("-m", "--mirror", metavar="EXE", default=_mirror,
                  help="override the docker_mirror.py [%default]")
    _o.add_option("-D", "--docker", metavar="EXE", default=_docker,
                  help="override docker exe or podman [%default]")
    _o.add_option("-l", "--logfile", metavar="FILE", default="",
                  help="additionally save the output log to a file [%default]")
    _o.add_option("-P", "--password", metavar="PASSWORD", default="",
                  help="use a fixed password for examples with auth [%default]")
    _o.add_option("--failfast", action="store_true", default=False,
                  help="Stop the test run on the first error or failure. [%default]")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
                  help="capture results as a junit xml file [%default]")
    opt, args = _o.parse_args()
    logging.basicConfig(level=logging.WARNING - opt.verbose * 5)
    #
    _systemctl_py = opt.systemctl_py
    _python = opt.python
    _python2 = opt.python2
    _python3 = opt.python3
    _epel7 = opt.epel7
    _mirror = opt.mirror
    _docker = opt.docker
    _password = opt.password
    #
    logfile = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
            os.remove(opt.logfile)
        logfile = logging.FileHandler(opt.logfile)
        logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(logfile)
        logg.info("log diverted to %s", opt.logfile)
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "w")
        logg.info("xml results into %s", opt.xmlresults)
    #
    # unittest.main()
    suite = unittest.TestSuite()
    if not args: args = ["test_*"]
    for arg in args:
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if "*" not in arg: arg += "*"
                if arg.startswith("_"): arg = arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # select runner
    if not logfile:
        if xmlresults:
            import xmlrunner
            Runner = xmlrunner.XMLTestRunner
            Runner(xmlresults).run(suite)
        else:
            Runner = unittest.TextTestRunner
            Runner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    else:
        Runner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner
            Runner = xmlrunner.XMLTestRunner
        Runner(logfile.stream, verbosity=opt.verbose).run(suite)
