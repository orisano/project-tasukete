#!/usr/bin/env python
# coding:utf-8
from __future__ import absolute_import, division, print_function

import argparse
import collections
import re
import shlex
import subprocess

NOTFOUND_COM = "notfound@notfound.com"


def git_command(cmd):
    args = shlex.split("git {}".format(cmd))
    return subprocess.check_output(args).decode("utf-8").rstrip()


def git_blame(filename, rev=None, range_=None):
    if not rev:
        rev = "HEAD"
    base_cmd = "blame {rev} {filename}".format(rev=rev, filename=filename)
    opt = []
    opt.append("-e")
    if range_:
        opt.append("-L {},{}".format(range_[0], range_[1]))

    try:
        output = git_command(" ".join([base_cmd] + opt)).split("\n")
        return [parse_blame(line) for line in output]
    except:
        return []


def git_rev_list(rev=None):
    if not rev:
        rev = "HEAD"
    output = git_command("rev-list {}".format(rev))
    return output.split("\n")


def git_config(prop):
    output = git_command("config {}".format(prop))
    return output


def parse_blame(line):
    obj = re.match(r"^.*?\((.*?)\).*$", line)
    email, _date, _time, _timezone, lineno = re.match(
        r"^<(\S+)>\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$", obj.group(1)
    ).groups()
    return {"email": email, "lineno": int(lineno)}


def clamp(x, min_, max_):
    return min(max(x, min_), max_)


def safe_slice(list_, start, end):
    # [start, end)
    size = len(list_)
    start = clamp(start, 0, size - 1)
    end = clamp(end, start, size)
    return list_[start:end]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("line", type=int)
    parser.add_argument("-n", "--neighbor", type=int, default=10)
    parser.add_argument("-r", "--recent", type=int, default=10)
    args = parser.parse_args()

    line = args.line - 1
    neighbor = args.neighbor

    me = git_config("user.email")
    revs = safe_slice(git_rev_list(), 0, args.recent)

    users = []
    for rev in revs:
        commiter = git_blame(args.filename, rev=rev)
        users += safe_slice(commiter, line - neighbor, line + neighbor + 1)

    helpers = [user["email"] for user in users if user["email"] != me]

    if helpers:
        print(collections.Counter(helpers).most_common(1)[0][0])
    else:
        print(NOTFOUND_COM)


if __name__ == "__main__":
    main()
