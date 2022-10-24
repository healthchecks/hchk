# healthchecks.io CLI

[![Not Maintained](https://img.shields.io/badge/Maintenance%20Level-Not%20Maintained-yellow.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)

A CLI interface to healthchecks.io. This project **is not maintained**, and I currently
have no plans to develop it further. For alternative, better, and actively maintained
CLI tools, please see [Third-Party Resources](https://healthchecks.io/docs/resources/)
on Healthchecks.io.

# Installation

Run:

    $ pip install hchk


# Usage

See available commands:

    $ hchk --help

Create your healthchecks.io API key in your
[settings page](https://healthchecks.io/accounts/profile/).

Save the API key on your target system. Your API key will be saved
in a plain text configuration file `$HOME/.hchk`

    $ hchk setkey YOUR_API_KEY

Create a check with custom name, tags, period and grace time, and then ping
it:

    $ hchk ping -n "My New Check" -t "web prod" -p 600 -g 60

The check will be created if it does not exist, and its ping URL
will be saved in `$HOME/.hchk`.

