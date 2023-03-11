#! /usr/bin/python
""" This program mimics the minimal behaviour of Hashicorp Vault's
 client tool 'vault'. When no -addr option (VAULT_ADDR) is given
 then it reads/writes ~/.config/vaultdata.ini - and when running 
 as a http `vault.py server` then these data value are provided."""

from __future__ import print_function

import sys
import ssl
import base64
import string
import os.path
import logging
try:
    import ConfigParser as configparser
except:
    import configparser # Python  3.0
try:
    import json # Python 2.6
except:
    json = None
try:
    import BaseHTTPServer
except:
    import http.server as BaseHTTPServer # Python 3.0
try:
    import urllib2
except:
    import urllib.request as urllib2 # Python 3.0

logg = logging.getLogger("vault")

DATAFILE = os.environ.get("VAULT_DATAFILE", "~/.config/vaultdata.ini")
LOGINFILE = os.environ.get("VAULT_LOGINFILE", "~/.vault_token")

VAULT_TOKEN=os.environ.get("VAULT_TOKEN", "")
VAULT_ADDR=os.environ.get("VAULT_ADDR", "0.0.0.0:8200")
VAULT_CACERT=os.environ.get("VAULT_CACERT", "")
VAULT_CAPATH=os.environ.get("VAULT_CAPATH", "")
VAULT_SKIP_VERIFY=os.environ.get("VAULT_SKIP_VERIFY", "")
VAULT_FORMAT=None
VAULT_FIELD=None
VAULT_DEV_MODE=None
VERBOSE=1
VAULT_SSL_KEY=os.environ.get("VAULT_SSL_KEY", "")

def decode(text):
    if text.startswith("{B64}:"):
        data = text[len("{B64}:"):]
        return base64.b64decode(data).decode("utf-8")
    if text.startswith("{B}:"):
        data = text[len("{B}:"):]
        return base64.b64decode(data[::-1].replace("$","=")).decode("utf-8")
    return text
def encode(text, using="B"):
    if using in ["B64"]:
        data = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return "{%s}:%s" % (using, data)
    if using in ["B"]:
        data = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return "{%s}:%s" % (using, data[::-1].replace("=","$"))
    return text

def remote_address(address):
    if not address.strip():
        return False
    if address.startswith("0."):
        return False
    # if address.startswith("127."):
    #     return False
    if address.startswith("local"):
        return False
    return True

class VaultError(Exception):
    pass

class Vault:
    def run(self, op, key = None, values = {}):
        if op in ["login"]:
            self.do_login(key)
        elif op in ["write"]:
            self.do_write(key, values)
        elif op in ["read"]:
            self.do_read(key)
        elif op in ["list"]:
            self.do_list(key)
        elif op in ["help"]:
            self.do_help()
        elif op in ["server"]:
            self.do_server()
        elif op in ["config"]:
            self.do_config()
        else:
            logg.error("no such op %s", op)
            raise VaultError("no such command")
    def do_login(self, key):
        """ vault login [-address={addr}] token """
        if key is None:
            logg.error("login op is missing token")
            raise VaultError("login without token")
        loginfile = os.path.expanduser(LOGINFILE)
        loginfiledir = os.path.dirname(loginfile)
        if not os.path.isdir(loginfiledir):
            os.makedirs(loginfiledir)
        with open(loginfile, "w") as out:
            out.write(key)

    def do_write(self, key, values):
        """ vault write [-address={addr}] key/name value=data """
        if key is None:
            logg.error("write op is missing key")
            raise VaultError("write without key")
        if not values:
            logg.error("write op is missing values")
            raise VaultError("write without values")
        if "value" not in values:
            logg.error("write op is missing value=setting")
            raise VaultError("write without value=setting")
        configfile = os.path.expanduser(DATAFILE)
        configdir = os.path.dirname(configfile)
        if not os.path.isdir(configdir):
            os.makedirs(configdir)
        config = configparser.ConfigParser()
        if os.path.exists(configfile):
            config.read(configfile)
        section, name = key.rsplit("/",1)
        if not config.has_section(section):
            config.add_section(section)
        for nam, val in values.items():
            if nam != "value":
                config.set(section, name + "." + nam, val)
        if "value" in values:
            val = values["value"]
            if val.startswith("@"):
                filename = val[1:]
                if not os.path.exists(filename):
                    logg.error("filename value=%s does not exist", val)
                    raise VaultError("write filename value does not exist")
                try:
                    newval = open(filename).read()
                except IOError as e:
                    logg.error("filename value=%s not readable: %s", val, e)
                    raise VaultError("write filename value not readable")
                val = newval
            config.set(section, name, encode(val))
        with open(configfile, "w") as out:
            config.write(out)

    def do_read(self, key):
        """ vault read [-address={addr}] key/name """
        if key is None:
            logg.error("read op is missing key")
            raise VaultError("read without key")
        if remote_address(VAULT_ADDR):
            values = self.read_remote(key)
        else:
            values = self.read_local(key)
        self.show(values)
    def read_local(self, key):
        configfile = os.path.expanduser(DATAFILE)
        configdir = os.path.dirname(configfile)
        if not os.path.exists(configfile):
            logg.error("no config file %s", configfile)
            raise VaultError("read missing config file")
        logg.debug("datafile=%s", configfile)
        config = configparser.ConfigParser()
        config.read(configfile)
        section, name = key.rsplit("/",1)
        if not config.has_section(section):
            logg.error("no such section %s", section)
            raise VaultError("data section not found")
        if not config.has_option(section, name):
            logg.error("no such entry %s/%s", section, name)
            raise VaultError("data entry not found")
        #
        values = {}
        for nam, val in config.items(section):
            if nam == name:
                values["value"] = decode(val)
            elif nam.startswith(name + "."):
                values[nam[len(name)+1:]] = decode(val)
        return values
    def read_remote(self, key):
        token = ""
        loginfile = os.path.expanduser(LOGINFILE)
        if os.path.exists(loginfile):
            token = open(loginfile).read().strip()
        addr=VAULT_ADDR
        if "://" not in addr:
            addr = "https://"+addr
        key_url = addr+"/v1/"+key
        req = urllib2.Request(key_url)
        if token:
            req.add_header("X-Vault-Token", token)
            logg.debug(" curl -sSL -H 'X-Vault-Token: %s' %s", token, key_url)
        else:
            logg.debug(" curl -sSL %s", key_url)
        ctx = None
        if VAULT_SKIP_VERIFY in ["y", "yes", "true", "True"]:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            logg.debug("tls-skip-verify: ignore ssl cert validation")
        resp = urllib2.urlopen(req, context=ctx)
        content = resp.read()
        values = json.loads(content)
        logg.debug("response %s", values)
        return values["data"]
    def show(self, values, format = None, field = None):
        format = format or VAULT_FORMAT
        field = field or VAULT_FIELD
        if field:
            if field not in values:
                logg.error("no such field %s/%s %s", section, name, field)
                raise VaultError("requested field not found")
            sys.stdout.write(values[field])
        else:
            if format in ["table",""]:
                for name in sorted(values):
                    print (name, values[name])
            elif format in ["json",""]:
                print (json.dumps({ "data": values }))
            else:
                print (values["value"])
    def do_list(self, key):
        """ vault list [-address={addr}] key """
        if key is None:
            logg.error("list op is missing key")
            raise VaultError("list without key")
        configfile = os.path.expanduser(DATAFILE)
        configdir = os.path.dirname(configfile)
        if not os.path.exists(configfile):
            logg.error("no config file %s", configfile)
            raise VaultError("list missing config file")
        config = configparser.ConfigParser()
        config.read(configfile)
        for section in config.sections():
            if section.startswith(key + "/"):
                print (section)
    def do_help(self):
        global __doc__
        docstring = __doc__
        print (docstring or " mimics Hashicorp Vault's client tool 'vault'")
        after = [ "do_read" ]
        addr = VAULT_ADDR
        for fu in sorted(dir(self)):
            if fu in after: continue
            if fu.startswith("do_"):
                doc = getattr(getattr(self, fu), "__doc__")
                defaults = "vault " + fu[3:] 
                print ((doc and doc.strip() or defaults).format(**locals()))
        for fu in sorted(dir(self)):
            if fu not in after: continue
            if fu.startswith("do_"):
                doc = getattr(getattr(self, fu), "__doc__")
                defaults = "vault " + fu[3:] 
                print ((doc and doc.strip() or defaults).format(**locals()))
    def do_config(self):
        values = self.configs()
        self.show(values)
    def configs(self):
        loginfile = os.path.expanduser(LOGINFILE)
        configfile = os.path.expanduser(DATAFILE)
        configdir = os.path.dirname(configfile)
        values = { 
            "configdir": configdir, 
            "value": configfile,
            "loginfile": loginfile,
        }
        return values
    def do_server(self):
        """ vault server [-address={addr}] [-dev] """
        server_class=BaseHTTPServer.HTTPServer
        # hndler_class=BaseHTTPServer.BaseHTTPRequestHandler
        handler_class = VaultRequestHandler
        port = 8200
        addr = VAULT_ADDR
        if addr and "://" not in addr:
            if VAULT_SSL_KEY:
                addr = "https://"+addr
            else:
                addr = "http://"+addr
        if addr and ":" in addr:
            port = int(addr.rsplit(":",1)[1])
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        if VAULT_ADDR.startswith("https:"):
            if not VAULT_SSL_KEY:
                raise VaultError("server as https: but no VAULT_SSL_KEY given")
            httpd.socket = ssl.wrap_socket (httpd.socket, certfile=VAULT_SSL_KEY, server_side=True) 
            logg.warning("https listen on %s", port)
        else:
            logg.warning("http listen on %s", port)
        httpd.serve_forever()

class VaultRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/v1/secret"):
            key = self.path[len("/v1/"):]
            try:
                values = Vault().read_local(key)
                content = json.dumps({ "data": values })
                logg.info("FOUND %s = %s", key, content)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(404, str(e))
        elif self.path.startswith("/v1/config"):
            if True:
                values = Vault().configs()
                content = json.dumps({ "data": values })
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(content)
        else:
            self.send_error(505, "do not know how to handle " + self.path)

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    key=None
    values={}
    op = None
    bad_args = []
    bad_opts = []
    for arg in sys.argv[1:]:
        if arg.startswith("-"):
            if arg in ["-h", "--help"]:
                Vault().do_help()
                sys.exit(0)
            elif arg.startswith("-address="):
                VAULT_ADDR=arg[len("-address="):].strip()
            elif arg.startswith("-ca-cert="):
                VAULT_CAPATH=arg[len("-ca-cert="):].strip()
            elif arg.startswith("-ca-path="):
                VAULT_CAPATH=arg[len("-ca-path="):].strip()
            elif arg.startswith("-tls-skip-verify="):
                VAULT_SKIP_VERIFY="yes"
            elif arg.startswith("-format="):
                VAULT_FORMAT=arg[len("-format="):].strip()
            elif arg.startswith("-field="):
                VAULT_FIELD=arg[len("-field="):].strip()
            elif arg in ["-dev"]:
                VAULT_DEV_MODE="yes"
            elif arg in ["-v", "-vv", "-vvv"]:
                VERBOSE=len(arg)
            else:
                bad_opts.append(arg)
        else:
            if op is None:
                op=arg
                continue
            elif key is None:
                key=arg
                continue
            elif "=" in arg:
                nam, val = arg.split("=", 1)
                values[nam] = val
                continue
            else:
                bad_args.append(arg)
    logging.basicConfig(level=max(0, logging.WARNING - 10 * VERBOSE))
    if bad_args:
        logg.error("no such argument: %s", " ".join(bad_args))
        sys.exit(1)
    if bad_opts:
        logg.error("no such option: %s", " ".join(bad_opts))
        sys.exit(1)
    try:
        Vault().run(op, key, values)
    except VaultError:
        sys.exit(1)
