import click
import os
import requests
import sys

try:
    # Python 3
    from configparser import RawConfigParser
except ImportError:
    # Python 2
    from ConfigParser import RawConfigParser

CHECK_ARGS = ("name", "tags", "period", "grace")
INI_PATH = os.path.join(os.path.expanduser("~"), ".hchk")


def get_config():
    config = RawConfigParser()
    if os.path.exists(INI_PATH):
        config.read(INI_PATH)
    return config


def save_config(config):
    with open(INI_PATH, 'w') as f:
        config.write(f)


def get_option(config, section, option):
    if not config.has_option(section, option):
        return ""
    return config.get(section, option)


def get_ping_url(check, recreate=False):
    config = get_config()
    for code in config.sections():
        if code == "hchk":
            continue

        match = True
        for key in CHECK_ARGS:
            if get_option(config, code, key) != check[key]:
                match = False

        if match and recreate:
            config.remove_section(code)

        if match and config.has_option(code, "ping_url"):
            return config.get(code, "ping_url")

    # The check doesn't exist, let's create it
    url = "https://healthchecks.io/api/v1/checks/"
    payload = {}
    if check["name"]:
        payload["name"] = check["name"]
    if check["tags"]:
        payload["tags"] = check["tags"]
    if check["period"]:
        payload["timeout"] = int(check["period"])
    if check["grace"]:
        payload["grace"] = int(check["grace"])

    if check["api_key"]:
        payload["api_key"] = check["api_key"]
    elif config.has_option("hchk", "api_key"):
        payload["api_key"] = config.get("hchk", "api_key")

    r = requests.post(url, json=payload).json()
    if "error" in r:
        raise ValueError(r["error"])

    code = r["ping_url"].split("/")[-1]
    config.add_section(code)
    config.set(code, "ping_url", r["ping_url"])
    for key in CHECK_ARGS:
        config.set(code, key, check[key])

    save_config(config)
    return r["ping_url"]


@click.group()
def cli():
    """A CLI interface to healthchecks.io"""

    pass


@cli.command()
@click.option('--api-key', '-k', help='API key for authentication')
@click.option('--name', '-n', default="", help='Name for the new check')
@click.option('--tags', '-t', default="",
              help='Space-delimited list of tags for the new check')
@click.option('--period', '-p', default="", help='Period, a number of seconds')
@click.option('--grace', '-g', default="",
              help='Grace time, a number of seconds')
def ping(**kwargs):
    """Create a check if neccessary, then ping it."""

    url = get_ping_url(kwargs)
    r = requests.get(url)
    if r.status_code == 400:
        # Let's try and recreate it:
        url = get_ping_url(kwargs, recreate=True)
        r = requests.get(url)

    if r.status_code != 200:
        tmpl = "Could not ping %s, received HTTP status %d\n"
        sys.stderr.write(tmpl % (url, r.status_code))
        sys.exit(1)


@cli.command()
@click.argument('api_key')
def setkey(api_key):
    """Save API key in $HOME/.hchk"""

    config = get_config()
    if not config.has_section("hchk"):
        config.add_section("hchk")

    config.set("hchk", "api_key", api_key)
    save_config(config)

    print("API key saved!")
