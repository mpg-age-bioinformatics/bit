#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import sys
from subprocess import Popen, PIPE, STDOUT
import stat
import shlex

import bit.config as config
import bit.git as git
import bit.owncloud as oc
import bit.rsync as rsync

import multiprocessing as mp

def worker(call):
    out=Popen(shlex.split(call), stdout=PIPE, stdin=PIPE, stderr=PIPE)
    message=out.communicate()
    out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass
    return "\n********************\n"+call.split(" ")[-1]+"\n"+message[0]+"\n"+message[1]

def main():

    import argparse

    parser = argparse.ArgumentParser(description="bit, [b]ermuda [i]nformation [t]riangle.\
     bit is a git-based tool for the management of code and data. It uses git for code versioning\
     and ownCloud for storing and exchanging data. It saves storage by avoiding versioning\
     of data while logging changes in associated git wikis.",\
    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input", nargs='*', help="Input files")
    parser.add_argument("-s", "--subfolder", help="Subfolder to be created.", default=None)
    parser.add_argument("-m", "--message",nargs='*', help="Message to write on log file.", default=None)
    parser.add_argument("-d", "--pick_a_date", help="Pick an existing date folder to transfer data to/from. Format=YYYY-MM-DD", default=None)
    parser.add_argument("-c", "--create_folder", help="Create dropbox folder for user to upload data.", action="store_true")
    parser.add_argument("-g", "--getfolder", help="Downloads a folder as zip file. Requires --pick_a_date. Defaults base_folder=upload:download to download", action="store_true")
    parser.add_argument("-t", "--days_to_share", help="Number of days you wish to share this folder further.", default=21)
    parser.add_argument("--issue", help="Issue to comment on with --message and owncloud data links", default=None)
    parser.add_argument("--scripts",help="Needs -i and -m. Simultaneously sync the scripts.user folder when uploading data.", action="store_true")
    parser.add_argument("--start", help="Project name of the format. PI_PROJECT_NAME. Initiates a project. This will create the required local folders and respective git repositories.", default=None)
    parser.add_argument("--stdfolders",nargs='*', help="Folders to be created in addition to scripts.user and and wiki.user when a project is started.", default=["tmp","slurm_logs"])
    parser.add_argument("--adduser",help="Add a user to a project creating his scripts.user and wiki.user folder",action="store_true")
    parser.add_argument("--sync", nargs='*',  help="Files or folders to syncronize with remote server using rsync over ssh.",default=None)
    parser.add_argument("--sync_to", help="Destination server to sync to in the form: <user_name>@<server.address>", default=None)
    parser.add_argument("--sync_from", help="Destination server to sync from in the form: <user_name>@<server.address>", default=None)
    parser.add_argument("--cpus",help="Number of CPUs/channels to open for rsync.", default=1)
    parser.add_argument("--forceRemote", help="If syncing from or to a remoter server force the import of a remote 'bit_config'.", action="store_true")
    parser.add_argument("--gitnossh", help="Use password instead of git SSH keys.",  action="store_false")
    parser.add_argument("--config", help="Generate a config file.", action="store_true")
    args = parser.parse_args()

    if args.sync:
        if args.sync_to:
            calls=rsync.rsync_to(args.sync_to, args.sync, forceImport=args.forceRemote, \
            sync_to=True, sync_from=False)
        elif args.sync_from:
            calls=rsync.rsync_from(args.sync_from, args.sync, forceImport=args.forceRemote, \
            sync_to=False, sync_from=True)

        pool=mp.Pool(int(args.cpus))

        funclist=[]
        for call in calls:
            out=pool.apply_async(worker,[call])
            funclist.append(out)
        results=[]
        for ff in funclist:
            res=ff.get()
            print(res)
            results.append(res)

    if args.config:
        print("Setting up your config file.")
        sys.stdout.flush()
        config.make_bitconfig()
        sys.exit(0)

    # initate a project
    if args.start:
        configdic=config.read_bitconfig()
        for r in config.start_reqs:
            if r != "user_group":
                while configdic[r] == None:
                    configdic=config.check_reqs([r],configdic,config_file=None, gitssh=None)
        local_path=os.path.abspath(configdic["local_path"])
        full_path=os.path.abspath(args.start)
        project_name=os.path.basename(full_path)

        # check format projects_folder/group_head/project_name
        if len(full_path.split("/")) != len(local_path.split("/"))+2:
            print("The path (%s) to this project does not obey the structure and/or defined local path (%s). Check the reference structure:\n%s" \
            %(full_path,local_path,config.structure) )
            sys.stdout.flush()
            sys.exit(0)

        # have the user rechecking that the the string for the project name is really correct
        checks=None
        while checks not in ["Y","N"]:
            checks=str(input("Is the label %s in agreement with the structure PF_project_name where PF stands for the initials of the Parent_Folder? (Y/N) " \
            %project_name )) or None
        if checks=="N":
            sys.exit(0)

        # create the repo
        github_api=config.get_github_api(configdic["github_address"])
        # github_api=github_api+configdic["github_organization"]+"/repos"
        # create_call=["curl","-u",configdic["github_user"]+":"+configdic["github_pass"]\
        # ,github_api,"-d",'{"name":"'+project_name+'","private": true,\
        # "auto_init": true }']

        # p = Popen(create_call, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        # print(p.communicate()[0].decode('utf-8').rstrip())
        # sys.stdout.flush()

        response =  git.make_github_repo(github_api, project_name, configdic)
        response =  git.make_github_issue(github_api, project_name, project_name, configdic, configdic["github_user"] )
        response =  git.make_github_card(response, github_api, configdic, "77")

        # !!removing the need for wiki!!
        # clone the repo and the wiki by initiating this user
        #input("\n\n*************\n\nPlease go to %s/%s/%s/wiki and click on 'Create the first page' and then 'Save Page'.\n\nPress Enter once you have saved the first wiki page.\n\n*************\n\n" \
        #%(configdic["github_address"],configdic["github_organization"],project_name) )

        config.init_user(full_path,configdic["github_address"],configdic["github_organization"],\
        project_name,github_user=configdic["github_user"],\
        github_pass=configdic["github_pass"],gitssh=args.gitnossh)

        # create additional folders
        for f in args.stdfolders:
            if not os.path.exists(full_path+"/"+f):
                os.makedirs(full_path+"/"+f)

        if configdic["user_group"]:
            os.chmod(full_path, stat.S_IRWXU)
            user_group=configdic["user_group"].split(",")
            try:
                for use in user_group:
                    call=["setfacl","-m","user:%s:rwx" %use,full_path]
                    out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
                    print(out.communicate()[0].decode('utf-8').rstrip())
            except:
                print("Failed to setfacls.")
                sys.stdout.flush()

        local_path_owner=os.stat(local_path)
        local_path_owner=local_path_owner.st_uid
        #os.chown(full_path,local_path_owner,-1)

        sys.exit(0)

    if args.adduser:
        configdic=config.read_bitconfig()
        for r in config.start_reqs:
            while configdic[r] == None:
                configdic=config.check_reqs([r],configdic,config_file=None, gitssh=args.gitnossh)
        local_path=os.path.abspath(configdic["local_path"])
        if args.start:
            full_path=os.path.abspath(args.start)
        else:
            full_path=os.path.abspath(os.getcwd())
        project_name=os.path.basename(full_path)

        # check format projects_folder/group_head/project_name
        if len(full_path.split("/")) != len(local_path.split("/"))+2:
            print("The path (%s) to this project does not obey the structure and/or defined local path (%s). Check the reference structure:\n%s" %(full_path,local_path,config.structure))
            sys.stdout.flush()
            sys.exit(0)

        config.init_user(full_path,configdic["github_address"],configdic["github_organization"],project_name,github_user=configdic["github_user"],github_pass=configdic["github_pass"],gitssh=args.gitnossh)
        sys.exit(0)

    if args.input:
        if not args.message:
            print("ERROR\nYou need to use -m to leave a message in the logs.")
            sys.exit()
        oc.ownCloud_upload(input_files=args.input,message=args.message,gitssh=args.gitnossh,days_to_share=args.days_to_share,scripts=args.scripts,issue=args.issue, subfolder=args.subfolder,pick_a_date=args.pick_a_date)
        sys.exit(0)

    if args.create_folder:
        oc.ownCloud_create_folder(gitssh=args.gitnossh,pick_a_date=args.pick_a_date,days_to_share=args.days_to_share)
        sys.exit(0)

    if args.getfolder:
        if not args.pick_a_date:
            print("--getfolder implies --pick_a_date.\nPlease use -d in combination with -g.\nThank you!")
            sys.exit(0)
        oc.ownCloud_download(gitssh=args.gitnossh,pick_a_date=args.pick_a_date)
        sys.exit(0)

    sys.exit(0)
