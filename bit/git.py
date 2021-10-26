from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import sys
import subprocess as sb
from subprocess import Popen, PIPE, STDOUT
import requests
import json

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
    # if not os.path.exists(local_name):
    #     os.makedirs(local_name)
    # cwd = os.getcwd()
    # os.chdir(local_name)
    # out=sb.call(['git','init'])
    # out=sb.call(['git','config','remote.origin.url',git2])
    # out=sb.call(['git','config','branch.master.remote','origin'])
    # out=sb.call(['git','config','branch.master.merge','refs/heads/master'])
    # out=sb.call(['git','pull', git])
    out=sb.call(['git','clone',git, local_name ])
    # os.chdir(cwd)
    return out

def git_fetch(github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None):
    git=git_target(github_address,github_organization,github_repo,github_user=github_user,github_pass=github_pass,gitssh=gitssh)
    call=["git","fetch",git]
    out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    print(out.communicate()[0].decode('utf-8').rstrip())
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
    print(out.communicate()[0].decode('utf-8').rstrip())
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
    print(out.communicate()[0].decode('utf-8').rstrip())
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
        print(out.communicate()[0].decode('utf-8').rstrip())
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
    print(out.communicate()[0].decode('utf-8').rstrip())
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
        print(out.communicate()[0].decode('utf-8').rstrip())
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

def git_write_comment(message,github_api,github_organization,github_repo,issue,github_user=None,github_pass=None):
    github_api=github_api.split("orgs/")[0]+"repos/"+github_organization+"/"+github_repo+"/issues/"+issue+"/comments"
    create_call=["curl","-u",github_user+":"+github_pass\
    ,github_api,"-d",'{"body":"'+message+'"}']
    #print( " ".join(create_call) )
    out=Popen(create_call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    #print(out.communicate()[0].rstrip()) 
    import time
    time.sleep(2)
    try:
        out.stdout.close()
    except:
        pass
    try:
        out.stdin.close()
    except:
        pass
    try:
        out.stderr.close()
    except:
        pass
    try:
        out.kill()
    except:
        pass


def make_github_repo( github_api, repo_name, configdic):
    url=f'{github_api}{configdic["github_organization"]}/repos'
    repo = { "name" : repo_name , \
             "private" : 'true' ,\
             "auto_init": 'true' }
    response = requests.post( url, data=json.dumps(repo), auth=( configdic["github_user"], configdic["github_pass"] ))
    if response.status_code == 201:
        print('Successfully created Repository "%s"' % repo_name )
    else:
        print('Could not create Repository "%s"' % repo_name)
        print('Response:', response.content)
        sys.stdout.flush()
        sys.exit(1)
    return response

def make_github_issue(github_api,  title, repo_name, configdic, assignee ):
    '''Create an issue on github.com using the given parameters.'''
    # Our url to create issues via POST
    base_api=github_api.split("orgs")[0]
    url=f'{base_api}repos/{configdic["github_organization"]}/{repo_name}/issues'
    issue = {'title': title,\
            'assignee': assignee}
    # Add the issue to our repository
    response = requests.post( url, data=json.dumps(issue), headers={"Accept": "application/vnd.github.v3+json"}, auth=( configdic["github_user"], configdic["github_pass"] ))#, headers=headers)
    
    if response.status_code == 201:
        print('Successfully created Issue "%s"' % title )

    else:
        print('Could not create Issue "%s"' % title)
        print('Response:', response.content)
        sys.stdout.flush()
        sys.exit(1)
    return response

def make_github_card(make_issue_response, github_api, configdic, column):
    '''Create an card for an issue on github.com using the given parameters.'''
    # Our url to create issues via POST
    base_api=github_api.split("orgs")[0]
    url=f'{base_api}projects/columns/{column}/cards'
    issue_response=json.loads(make_issue_response.text)
    issue_id=issue_response["id"]
    card = {'content_id': issue_id,\
            "content_type":"Issue"}
    # Add the issue to our repository
    response = requests.post( url, data=json.dumps(card), headers={"Accept": "application/vnd.github.inertia-preview+json"}, auth=( configdic["github_user"], configdic["github_pass"] ))#, headers=headers)
    
    if response.status_code == 201:
        print('Successfully created card.' )
    else:
        print('Could not create card.')
        print('Response:', response.content)
        sys.stdout.flush()
        sys.exit(1)
    return response