from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import json
import time
import datetime
import os
import sys
import getpass
from os.path import expanduser
from subprocess import Popen, PIPE, STDOUT
import subprocess as sb
import stat
import tempfile
import pwd

import bit.config as config
import bit.bit as bit
import bit.owncloud as oc
import bit.rsync as rsync

def git_target(github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None,usepw=None):
    url=github_address.split("//")[-1]
    if not gitssh:
        git="https://%s:%s@%s/%s/%s.git" %(github_user,github_pass,url,github_organization,github_repo)
    else:
        git="git@%s:%s/%s.git" %(url,github_organization,github_repo)
    if usepw:
        git2="https://%s@%s/%s/%s.git" %(github_user,url,github_organization,github_repo)
        return git, git2
    else:
        return git

def git_clone(local_name,github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None):
    git, git2 =git_target(github_address,github_organization,github_repo,github_user=github_user,github_pass=github_pass,gitssh=gitssh,usepw=True)
    if not os.path.exists(local_name):
        os.makedirs(local_name)
    cwd = os.getcwd()
    os.chdir(local_name)
    out=sb.call(['git','init'])
    out=sb.call(['git','config','remote.origin.url',git2])
    out=sb.call(['git','config','branch.master.remote','origin'])
    out=sb.call(['git','config','branch.master.merge','refs/heads/master'])
    out=sb.call(['git','pull', git])
    os.chdir(cwd)
    return out

def git_fetch(github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None):
    git=git_target(github_address,github_organization,github_repo,github_user=github_user,github_pass=github_pass,gitssh=gitssh)
    call=["git","fetch",git]
    out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    print(out.communicate()[0].rstrip())
    out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass

def git_merge(message):
    call=["git","merge","FETCH_HEAD","-m",message]
    out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    print(out.communicate()[0].rstrip())
    out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass

def git_pull(github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None):
    git=git_target(github_address,github_organization,github_repo,github_user=github_user,github_pass=github_pass,gitssh=gitssh)
    call=["git","pull",git]
    out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    print(out.communicate()[0].rstrip())
    out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass

def git_add(files_to_add):
    for f in files_to_add:
        call=["git","add",f]
        out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        print(out.communicate()[0].rstrip())
        out.stdout.close()
        out.stdin.close()
        out.stderr.close()
        try:
            out.kill()
        except:
            pass

def git_commit(message):
    call=["git","commit","-m", message]
    out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    print(out.communicate()[0].rstrip())
    out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass

def git_push(github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None):
    git=git_target(github_address,github_organization,github_repo,github_user=github_user,github_pass=github_pass,gitssh=gitssh)
    call=["git","push",git,"--all"]
    if gitssh:
        out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        print(out.communicate()[0].rstrip())
    else:
        FNULL = open(os.devnull, 'w')
        out=Popen(call, stdout=FNULL, stdin=PIPE ,stderr=PIPE) #, stdout=FNULL, stderr=subprocess.STDOUT old: stdout=PIPE, stdin=PIPE, stderr=STDOUT
        out=Popen(["git","push"],stdout=PIPE, stdin=PIPE, stderr=PIPE)
	out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass

def git_sync(files_to_add,message,github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None):
    git_add(files_to_add)
    git_commit(message)
    git_fetch(github_address,github_organization,github_repo,github_user=github_user,github_pass=github_pass,gitssh=gitssh)
    git_merge(message)
    git_push(github_address,github_organization,github_repo,github_user=github_user,github_pass=github_pass,gitssh=gitssh)
