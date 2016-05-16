# Slack the Ripper

A utility built on the [Slacker](https://github.com/os/slacker) python
project to rip (pull) slack conversation from channels, to use as a basis
for reports.

Slack channels often contain info that can be usefully reused -- as
documentation, emails, code notes, etc.  Copying, pasting, and
cleaning these comments is enough of a hassle to prompt the use of
this tool.

# Installation

Check out this repo

# Usage

```
$ virtualenv venv    # or whatever you do to manage your Python envs
$ source venv/bin/activate
$ make init
```

Create a file with your [Slack API
token](https://api.slack.com/docs/oauth-test-tokens) using the
supplied template:

```
$ cp token.yml.template token.yml
# edit token.yml
```

`token.yml` is ignored by git, you should keep your token private.

Run it from the command line, with some args:

```
python rip.py --help
```


# TODOs

This is a quick tool to gather and print out data.  There are some
things that it could use:

* Unit tests for parsing the returned data.
* Concatenating contiguous messages from same user.


# Coding

Branch off of master, submit a PR.

# License

Do whatever you want with it.