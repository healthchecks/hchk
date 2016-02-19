import click
import json
import os
import pkg_resources
import requests
import sys
import time

try:
    # Python 3
    from configparser import RawConfigParser
except ImportError:
    # Python 2
    from ConfigParser import RawConfigParser

CHECK_ARGS = ("name", "tags", "period", "grace")
INI_PATH = os.path.join(os.path.expanduser("~"), ".hchk")
VERSION = pkg_resources.get_distribution("hchk").version
UA = "hchk/%s" % VERSION


class Api(object):
    def __init__(self, api_key):
        self.api_key = api_key

    def create_check(self, check):
        payload = {"api_key": self.api_key}
        if check.get("name"):
            payload["name"] = check["name"]
        if check.get("tags"):
            payload["tags"] = check["tags"]
        if check.get("period"):
            payload["timeout"] = int(check["period"])
        if check.get("grace"):
            payload["grace"] = int(check["grace"])

        url = "https://healthchecks.io/api/v1/checks/"
        data = json.dumps(payload)
        r = requests.post(url, data=data, headers={"User-Agent": UA})
        parsed = r.json()
        if "error" in r:
            raise ValueError(r["error"])

        return parsed["ping_url"]


class Check(dict):
    def matches_spec(self, spec):
        for key in CHECK_ARGS:
            if self.get(key) != spec.get(key):
                return False

        return True

    def create(self, api):
        self["ping_url"] = api.create_check(self)

    def ping(self):
        """Run HTTP GET to self["ping_url"].

        On errors, retry with exponential backoff.

        """

        retries = 0
        while True:
            status = 0
            try:
                r = requests.get(self["ping_url"], timeout=10,
                                 headers={"User-Agent": UA})
                status = r.status_code
            except requests.exceptions.ConnectionError:
                sys.stderr.write("Connection error\n")
            except requests.exceptions.Timeout:
                sys.stderr.write("Connection timed out\n")
            else:
                if status not in (200, 400):
                    sys.stderr.write("Received HTTP status %d\n" % status)

            # 200 is success, 400 is most likely "check does not exist"
            if status in (200, 400):
                return status

            # In any other case, let's retry with exponential backoff:
            delay, retries = 2 ** retries, retries + 1
            if retries >= 5:
                sys.stderr.write("Exceeded max retries, giving up\n")
                return 0

            sys.stderr.write("Will retry after %ds\n" % delay)
            time.sleep(delay)


class Config(RawConfigParser):
    def __init__(self):
        # RawConfigParser is old-style class, so don't use super()
        RawConfigParser.__init__(self)
        self.read(INI_PATH)

    def save(self):
        with open(INI_PATH, 'w') as f:
            self.write(f)

    def find(self, spec):
        for section in self.sections():
            if not self.has_option(section, "ping_url"):
                continue

            candidate = Check(self.items(section))
            if candidate.matches_spec(spec):
                candidate["_section"] = section
                return candidate

    def save_check(self, check):
        # First, remove all checks with similar specs
        while True:
            other = self.find(check)
            if other is None:
                break

            self.remove_section(other["_section"])

        # Then save this check
        code = check["ping_url"].split("/")[-1]
        self.add_section(code)
        self.set(code, "ping_url", check["ping_url"])
        for key in CHECK_ARGS:
            if check.get(key):
                self.set(code, key, check[key])

        self.save()

    def get_api_key(self):
        if not self.has_option("hchk", "api_key"):
            return None

        return self.get("hchk", "api_key")


@click.group()
def cli():
    """A CLI interface to healthchecks.io"""

    pass


@cli.command()
@click.option('--name', '-n', help='Name for the new check')
@click.option('--tags', '-t',
              help='Space-delimited list of tags for the new check')
@click.option('--period', '-p', help='Period, a number of seconds')
@click.option('--grace', '-g', help='Grace time, a number of seconds')
def ping(**kwargs):
    """Create a check if neccessary, then ping it."""

    config = Config()
    api_key = config.get_api_key()
    if api_key is None:
        msg = """API key is not set. Please set it with

    hchk setkey YOUR_API_KEY

"""
        sys.stderr.write(msg)
        sys.exit(1)

    api = Api(api_key)

    spec = {}
    for key in CHECK_ARGS:
        if kwargs.get(key):
            spec[key] = kwargs[key]

    check = config.find(spec)
    if check is None:
        check = Check(spec)
        check.create(api)
        config.save_check(check)

    status = check.ping()
    if status == 400:
        check.create(api)
        config.save_check(check)
        status = check.ping()

    if status != 200:
        sys.exit(1)


@cli.command()
@click.argument('api_key')
def setkey(api_key):
    """Save API key in $HOME/.hchk"""

    config = Config()
    if not config.has_section("hchk"):
        config.add_section("hchk")

    config.set("hchk", "api_key", api_key)
    config.save()

    print("API key saved!")
