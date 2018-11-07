import os
import git
os.chdir("/Users/jboucas/")
rw_dir="/Users/jboucas/"
repo = git.Repo.clone_from("https://github.com/mpg-age-bioinformatics/htseq-tools.git", "test_clone", branch='master')

repo = git.Repo("test_clone")
assert repo.__class__ is git.Repo 

repo = git.Repo("/Users/jboucas/")
assert repo.__class__ is git.Repo 

