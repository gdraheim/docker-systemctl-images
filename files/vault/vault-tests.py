#! /usr/bin/python

import os
import unittest
import subprocess

def sh(cmd, shell = True):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    proc.wait()
    return proc # .stdin / .stderr / .returncode

loginfile = "~/.vault_token"

class VaultTests(unittest.TestCase):
    def test_000_clear(self):
        if os.path.exists(loginfile):
           os.remove(loginfile)
    def test_001_login(self):
        cmd = "./vault.py login foo"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
    def test_002_write(self):
        cmd = "./vault.py write secret/test/foo value=bar"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
    def test_003_read(self):
        cmd = "./vault.py read secret/test/foo -field=value"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read(), "bar")
    def test_004_read_json(self):
        cmd = "./vault.py read secret/test/foo -format=json"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read().strip(), '{"data": {"value": "bar"}}')
    def test_202_write(self):
        cmd = "./vault.py write secret/test/bar value=foo expired=next"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
    def test_203_read(self):
        cmd = "./vault.py read secret/test/bar -field=value"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read(), "foo")
    def test_204_read_json(self):
        cmd = "./vault.py read secret/test/bar -format=json"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read().strip(), '{"data": {"expired": "next", "value": "foo"}}')
    def test_204_read_json(self):
        cmd = "./vault.py read secret/test/bar -format=table"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read(), 'expired next\nvalue foo\n')
    def test_993_read_oldstyle(self): # OBSOLETE
        cmd = "./vault.py read secret/test/foo"
        done = sh(cmd)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.read(), "bar\n")

if __name__ == "__main__":
    unittest.main()
