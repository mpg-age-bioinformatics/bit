import os
import git
os.chdir("/Users/jboucas/")
rw_dir="/Users/jboucas/"
repo = git.Repo.clone_from("https://github.com/mpg-age-bioinformatics/htseq-tools.git", "test_clone", branch='master')
repo = git.Repo.clone_from("https://github.molgen.mpg.de/mpg-age-bioinformatics/MG_HTS_lifespan.git", "test_clone_pass", branch='master')



try:
    repo = git.Repo(rw_dir+"test_clone")

except:

assert repo.__class__ is git.Repo 

repo = git.Repo("/Users/jboucas/")
assert repo.__class__ is git.Repo 

# github pass needs to be given 2 when not using ssh

def git_clone(local_name,github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None):
    git_repo, git_no_pass =git_target(github_address,github_organization,github_repo,github_user=github_user,github_pass=github_pass,gitssh=gitssh,usepw=True)
    if gitssh:
        repo=git.Repo.clone_from(git_repo,local_name, branch='master')
    else:
        repo=git.Repo.clone_from(git_no_pass,local_name, branch='master')
    return repo

from git import RemoteProgress

class MyProgressPrinter(RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print(op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE")

def git_fetch(github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None):
    git=git_target(github_address,github_organization,github_repo,github_user=github_user,github_pass=github_pass,gitssh=gitssh)
    cwd = os.getcwd()
    repo=git.Repo(cwd)
    origin=repo.remotes[0]
    #response=remote.fetch()

    # final solution for git fetch
    # repo.remotes[0].fetch()

    for fetch_info in origin.fetch(progress=MyProgressPrinter()):
        print("Updated %s to %s" % (fetch_info.ref, fetch_info.commit))

### repo in arguments newly added
def git_merge(message,repo):
    print(repo.git.merge('FETCH_HEAD'))
    #call=["git","merge","FETCH_HEAD","-m",message]
    #out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    #print(out.communicate()[0].rstrip())
    #out.stdout.close()
    #out.stdin.close()
    #out.stderr.close()
    #try:
    #    out.kill()
    #except:
    #    pass

## origin added to arguments here
def git_pull(github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None, origin=None:
    origin.pull()
    #git=git_target(github_address,github_organization,github_repo,github_user=github_user,github_pass=github_pass,gitssh=gitssh)
    #call=["git","pull",git]
    #out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    #print(out.communicate()[0].rstrip())
    #out.stdout.close()
    #out.stdin.close()
    #out.stderr.close()
    #try:
    #    out.kill()
    #except:
    #    pass

## origin added to arguments here
def git_push(github_address,github_organization,github_repo,github_user=None,github_pass=None,gitssh=None, origin=None:
    origin.push()

### repo in arguments newly added
def git_add(files_to_add, repo):
    repo.index.add(files_to_add)

def git_commit(message):
    repo.index.commit(message)