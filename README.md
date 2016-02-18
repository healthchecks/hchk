# healthchecks.io CLI

A CLI interface to healthchecks.io


# Installation

If you don't use `pipsi`, you're missing out.
Here are [installation instructions](https://github.com/mitsuhiko/pipsi#readme).

Simply run:

    $ pipsi install .


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

