#! /usr/bin/python
""" testing vault.py, the script that mimics a minimized
    version of HashiCorp Vault's client tool 'vault' """

import os
import sys
import unittest
import subprocess
import logging
from fnmatch import fnmatchcase as fnmatch

def sh(cmd, shell = True):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    proc.wait()
    return proc # .stdin / .stderr / .returncode

loginfile = "~/.vault_token"
_vault_py = "./vault.py"
_python = "python"

def vault():
    return "%s %s " % (_python, _vault_py)

class VaultTests(unittest.TestCase):
    def test_000_clear(self):
        """ reset test data """
        if os.path.exists(loginfile):
           os.remove(loginfile)
    def test_001_login(self):
        """ any 'login' possible """
        cmd = vault() + "login foo"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
    def test_002_write(self):
        """ do 'write' any value """
        cmd = vault() + "write secret/test/foo value=bar"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
    def test_003_read(self):
        """ do 'read' that value """
        cmd = vault() + "read secret/test/foo -field=value"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read(), "bar")
    def test_004_read_json(self):
        """ do 'read' that value as json """
        cmd = vault() + "read secret/test/foo -format=json"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read().strip(), '{"data": {"value": "bar"}}')
    def test_202_write(self):
        """ do 'write' with expired """
        cmd = vault() + "write secret/test/bar value=foo expired=next"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
    def test_203_read(self):
        """ do 'read' that value """
        cmd = vault() + "read secret/test/bar -field=value"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read(), "foo")
    def test_204_read_json(self):
        """ do 'read' that value as json and find 'expired' """
        cmd = vault() + "read secret/test/bar -format=json"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read().strip(), '{"data": {"expired": "next", "value": "foo"}}')
    def test_204_read_json(self):
        """ do 'read' that value as table """
        cmd = vault() + "read secret/test/bar -format=table"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read(), 'expired next\nvalue foo\n')
    def test_993_read_oldstyle(self): # OBSOLETE
        """ do 'read' a value even without -field=value (some extra) """
        cmd = vault() + "read secret/test/foo"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read(), "bar\n")

if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [options] test*",
       epilog=__doc__.strip().split("\n")[0])
    _o.add_option("-v","--verbose", action="count", default=0,
       help="increase logging level [%default]")
    _o.add_option("--with", metavar="FILE", dest="vault_py", default=_vault_py,
       help="systemctl.py file to be tested (%default)")
    _o.add_option("-p","--python", metavar="EXE", default=_python,
       help="use another python execution engine [%default]")
    _o.add_option("-l","--logfile", metavar="FILE", default="",
       help="additionally save the output log to a file [%default]")
    _o.add_option("--xmlresults", metavar="FILE", default=None,
       help="capture results as a junit xml file [%default]")
    opt, args = _o.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    _vault_py = opt.vault_py
    _python = opt.python
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
    # unittest.main()
    suite = unittest.TestSuite()
    if not args: args = [ "test_*" ]
    for arg in args:
        for classname in sorted(globals()):
            if not classname.endswith("Tests"):
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
            result = Runner(xmlresults).run(suite)
        else:
            Runner = unittest.TextTestRunner
            result = Runner(verbosity=opt.verbose).run(suite)
    else:
        Runner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner
            Runner = xmlrunner.XMLTestRunner
        result = Runner(logfile.stream, verbosity=opt.verbose).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
