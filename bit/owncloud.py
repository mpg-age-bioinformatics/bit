from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import time
import datetime
import os
import sys
import getpass

import bit.config as config
import bit.git as git
import bit._owncloud as owncloud

def list_upload(base_destination,list_of_files):
    upload_dic={}
    subfolders=[base_destination]
    check=base_destination.split("/")
    for i in range(len(check)):
        c="/".join(check[:i-len(check)])
        subfolders.append(c)

    for f in list_of_files:
        full=os.path.abspath(f)
        if os.path.isdir(full):
            subfol=base_destination+"/"+os.path.basename(full)
            subfolders.append(subfol)
            for root, directories, filenames in os.walk(full):
                bad_dirs=[]
                for directory in directories:
                    if os.path.basename(directory)[0] != ".":
                        subdir=os.path.join(root, directory).split(full)[-1]
                        subdir=subfol+subdir
                        subfolders.append(subdir)
                    else:
                        bad_dirs.append(os.path.basename(directory))
                for filename in filenames:
                    if not any(x in filename for x in bad_dirs):
                        subfile=os.path.join(root,filename)
                        if os.path.isfile(subfile):
                            upload_dic[subfile]=subfol+subfile.split(full)[-1]

        elif os.path.isfile(full):
            upload_dic[full]=base_destination+"/"+os.path.basename(full)

    subfolders=list(set(subfolders))
    subfolders=[ xx for xx in subfolders if len(xx) > 0 ]
    subfolders.sort()

    return upload_dic, subfolders

def get_ownCloud_links(link_info,http):
    link_info=str(link_info)
    store=link_info.split("path=")[1].split(",")[0]
    store=store.split("/")
    store="%2F".join(store)
    link=link_info.split("url=")[1].split(",")[0]
    print("\nYour link:\n%s" %http+"/index.php/apps/files?dir="+store)
    print("Public link:\n%s\n" %link)
    return http+"/index.php/apps/files?dir="+store

def get_owncloud_base_folder(configdic,project_name,getfolder=None,pick_a_date=None,create_folder=None,subfolder=None):

    if getfolder:
        if not pick_a_date:
            print("--getfolder implies --pick_a_date.\nPlease use -d in \
            combination with -g.\nThank you!")
            sys.exit()
        else:
            base_folder=configdic["owncloud_download_folder"]
    elif create_folder:
        base_folder=configdic["owncloud_download_folder"]
    else:
        base_folder=configdic["owncloud_upload_folder"]

    if pick_a_date == None:
        d = str(datetime.date.today())
    else:
        d = str(pick_a_date)

    if subfolder:
        d = d+"/"+str(subfolder)

    base_destination=base_folder+"/"+project_name+"/"+d

    return base_destination

def ownCloud_upload(input_files=None,message=None,gitssh=None,days_to_share=None,scripts=None,issue=None, subfolder=None, pick_a_date=None):

    if type(message) == list:
        message=[ str(xx) for xx in message ]
        message=" ".join(message)
    else:
        message=str(message)

    configdic=config.read_bitconfig()
    for r in config.requirements:
        if not gitssh:
            if r not in ["user_group" ]:
                while configdic[r] == None:
                    configdic=config.check_reqs([r],configdic,config_file=None, \
                    gitssh=None)
        else:
            if r not in [ "github_user", "github_pass","user_group" ]:
                while configdic[r] == None:
                    configdic=config.check_reqs([r],configdic,config_file=None, \
                    gitssh=gitssh)

    local_path=os.path.abspath(configdic["local_path"])
    automation_path=os.path.abspath(configdic["automation_path"])
    code_path=os.path.abspath(configdic["code_path"])

    # check if files all come from the same project folder
    parent_folder=[]
    check_project=[]
    for i in input_files:
        f=os.path.abspath(i)
        if local_path in f :
            size_local=len(local_path.split("/"))
        elif automation_path in f:
            size_local=len(local_path.split("/"))
        elif code_path in f:
            size_local=len(local_path.split("/"))
        parent_folder.append(f.split("/")[size_local])
        check_project.append(f.split("/")[size_local+1])
    check_project=list(set(check_project))
    if len(check_project) > 1:
        print("Found more than one path to project:\n")
        for p in check_project:
            print(p)
            sys.stdout.flush()
        sys.exit(0)
    else:
        project_name=check_project[0]
        parent_folder=parent_folder[0]

    target_project=parent_folder+"/"+project_name

    base_destination=get_owncloud_base_folder(configdic,target_project, subfolder=subfolder, pick_a_date=pick_a_date)

    upload_dic, subfolders=list_upload(base_destination,input_files)

    # login to owncloud
    try:
        oc=owncloud.Client(configdic["owncloud_address"])
        oc.login(configdic["owncloud_user"],configdic["owncloud_pass"])
    except:
        print("Could not login to ownCloud.\nPlease make sure you are giving \
        the right address to your owncloud and using the right login credentials.")
        sys.exit(0)

    # create required subfolders in ownCloud
    for fold in subfolders:
        try:
            oc.file_info(fold)
        except:
            oc.mkdir(fold)

    # Upload files
    if len(upload_dic)>1:
        print("Uploading %s files.." %str(len(upload_dic)))
        sys.stdout.flush()
    else:
        print("Uploading %s file.." %str(len(upload_dic)))
        sys.stdout.flush()

    skipped_files=[]
    for f in upload_dic:
        file_handle = open(f, 'r', 8192)
        file_handle.seek(0, os.SEEK_END)
        size = file_handle.tell()
        file_handle.seek(0)
        if size == 0:
            skipped_files.append(os.path.basename(f))
            print("\t%s is empty. Skipping .. " %str(f))
            sys.stdout.flush()
            continue
        if size > 1879048192:
            print("\t%s\t(chunked)" %str(upload_dic[f]))
            sys.stdout.flush()
            oc.put_file(upload_dic[f],f)
        else:
            print("\t%s" %str(upload_dic[f]))
            sys.stdout.flush()
            oc.put_file(upload_dic[f],f,chunked=False)

    print("Finished uploading.")
    # Time stamp for expiration date
    tshare = datetime.date.today()
    tshare = tshare + datetime.timedelta(days=int(days_to_share))
    tshare = time.mktime(tshare.timetuple())

    link_info = oc.share_file_with_link(base_destination,expiration=tshare)
    private_link=get_ownCloud_links(link_info,configdic["owncloud_address"])

    oc.logout()

    # Go to wiki folder and make a git sync
    print("Logging changes..")
    sys.stdout.flush()
    user_name=getpass.getuser()
    wikidir=code_path+"/"+target_project+"/wiki."+user_name
    scriptsdir=code_path+"/"+target_project+"/scripts."+user_name
    if os.path.isdir(wikidir):
        logdir=wikidir
        log_project=project_name+".wiki"
    elif os.path.isdir(scriptsdir):
        logdir=scriptsdir
        log_project=project_name
    else:
        print("Could not find wiki."+user_name+" nor scripts."+user_name)
        sys.exit(1)

    os.chdir(logdir)
    files_to_add=os.listdir(logdir)
    git.git_sync(files_to_add,message,configdic["github_address"],\
    configdic["github_organization"],log_project,\
    github_user=configdic["github_user"],github_pass=configdic["github_pass"],\
    gitssh=gitssh)

    # Write log file
    if len(skipped_files) > 0:
        skipped_files=", ".join(skipped_files)
        skipped_files="\n\n(skipped: %s)" %skipped_files
    else:
        skipped_files=""
    logfile="uploads.md"
    logtext="\n\n##### ["+base_destination.split("/")[3]+"\t::\t"+user_name+"]("+private_link+") : "\
    +str("".join(message))+"\n"+\
    str(datetime.datetime.now()).split(".")[0]+", "+str(", ".join(input_files))\
    +skipped_files

    log=open(logfile,"a")
    log.write(logtext)
    log.close()

    #  push the log
    git.git_add(["uploads.md"])
    git.git_commit(message)
    git.git_push(configdic["github_address"],configdic["github_organization"],\
    log_project,github_user=configdic["github_user"],\
    github_pass=configdic["github_pass"],gitssh=gitssh)

    if scripts:
        print("Syncronizing your code..")
        sys.stdout.flush()
        os.chdir(code_path+"/"+target_project+"/scripts."+user_name)
        #files_to_add=os.listdir(local_path+"/"+target_project+"/scripts."+user_name)
        #git.git_sync(files_to_add,message,configdic["github_address"],\
        git.git_sync(["-A"],message,configdic["github_address"],\
        configdic["github_organization"],project_name,\
        github_user=configdic["github_user"],\
        github_pass=configdic["github_pass"],gitssh=gitssh)

    if issue:
        for r in [ "github_user", "github_pass"]:
            while configdic[r] == None:
                configdic=config.check_reqs([r],configdic,config_file=None, \
                gitssh=None)
        publink=str(link_info).split("url=")[1].split(",")[0]
        issueMSG="Public link: %s; Private link: %s; Commit message: %s" \
        %(publink, private_link,message)
        git.git_write_comment(issueMSG,config.get_github_api(configdic["github_address"]),\
        configdic["github_organization"],project_name,str(issue),\
        github_user=configdic["github_user"],github_pass=configdic["github_pass"])

downloadreqs=["owncloud_address","owncloud_upload_folder",\
"owncloud_download_folder","owncloud_user",\
"owncloud_pass","local_path"]

def ownCloud_download(gitssh=None,pick_a_date=None):
    configdic=config.read_bitconfig()
    for r in downloadreqs:
        while configdic[r] == None:
            configdic=config.check_reqs([r],configdic,config_file=None, \
            gitssh=gitssh)
    local_path=os.path.abspath(configdic["local_path"])

    size_local=len(local_path.split("/"))

    f=os.path.abspath(str(pick_a_date))
    parent_folder=f.split("/")[size_local]
    project_name=f.split("/")[size_local+1]

    target_project=parent_folder+"/"+project_name

    base_destination=get_owncloud_base_folder(configdic,target_project,getfolder=True, pick_a_date=pick_a_date)

    # login to owncloud
    try:
        oc=owncloud.Client(configdic["owncloud_address"] )
        oc.login(configdic["owncloud_user"],configdic["owncloud_pass"])
    except:
        print("Could not login to ownCloud.\nPlease make sure you are giving \
        the right address to your owncloud and using the right login credentials.")
        sys.exit(0)

    oc.get_directory_as_zip(base_destination, pick_a_date+".zip")
    oc.logout()
    print("Downloaded %s.zip" %pick_a_date)
    sys.stdout.flush()

def ownCloud_create_folder(gitssh=None,pick_a_date=None,days_to_share=None):
    configdic=config.read_bitconfig()
    for r in downloadreqs:
        while configdic[r] == None:
            configdic=config.check_reqs([r],configdic,config_file=None, \
            gitssh=gitssh)
    local_path=os.path.abspath(configdic["local_path"])

    size_local=len(local_path.split("/"))

    f=os.path.abspath(str(pick_a_date))
    parent_folder=f.split("/")[size_local]
    project_name=f.split("/")[size_local+1]

    target_project=parent_folder+"/"+project_name

    base_destination=get_owncloud_base_folder(configdic,target_project,create_folder=True, pick_a_date=pick_a_date)

    # login to owncloud
    try:
        oc=owncloud.Client(configdic["owncloud_address"] )
        oc.login(configdic["owncloud_user"],configdic["owncloud_pass"])
    except:
        print("Could not login to ownCloud.\nPlease make sure you are giving \
        the right address to your owncloud and using the right login credentials.")
        sys.exit(0)

    check=base_destination.split("/")
    print(check)
    for i in range(len(check)+1):
        c="/".join(check[:i])
        print(c)
        try:
            oc.file_info(c)
        except:
            oc.mkdir(c)

    # Time stamp for expiration date
    tshare = datetime.date.today()
    tshare = tshare + datetime.timedelta(days=int(days_to_share))
    tshare = time.mktime(tshare.timetuple())

    link_info = oc.share_file_with_link(base_destination,expiration=tshare,public_upload=True)
    private_link=get_ownCloud_links(link_info,configdic["owncloud_address"])

    oc.logout()
