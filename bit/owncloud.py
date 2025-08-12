from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import time
import datetime
import os
import sys
import getpass
import shutil

import bit.config as config
import bit.git as git
from nc_py_api import Nextcloud

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

def get_ownCloud_links(link_info, http):
    from urllib.parse import quote
    path = link_info.get("path", "").lstrip("/")
    url = link_info.get("url", "")
    store = quote(path)
    private_link = f"{http}/index.php/apps/files?dir=/{store}"

    print("\nYour link:\n%s" % private_link)
    print("Public link:\n%s\n" % url)
    return private_link

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
            size_local=len(automation_path.split("/"))
        elif code_path in f:
            size_local=len(code_path.split("/"))
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

    # login to owncloud/nextcloud
    try:
        nc = Nextcloud(nextcloud_url=configdic["owncloud_address"], nc_auth_user=configdic["owncloud_user"], nc_auth_pass=configdic["owncloud_pass"])
    except:
        print("Could not login to Cloud.\nPlease make sure you are giving \
        the right address to your Cloud and using the right login credentials.")
        sys.exit(0)

    # create required subfolders in ownCloud
    for fold in subfolders:
        parent = os.path.dirname(fold)
        name = os.path.basename(fold)
        try:
            entries = nc.files.listdir(parent)
            if name not in [e.name for e in entries if e.is_dir]:
                nc.files.mkdir(fold)
        except Exception as e:
            print(f"Failed checking/creating {fold}: {e}")


    # Upload files
    if len(upload_dic)>1:
        print("Uploading %s files.." %str(len(upload_dic)))
        sys.stdout.flush()
    else:
        print("Uploading %s file.." %str(len(upload_dic)))
        sys.stdout.flush()

    skipped_files=[]
    for f in upload_dic:
        with open(f, 'rb') as file_handle:
            file_handle.seek(0, os.SEEK_END)
            size = file_handle.tell()
            file_handle.seek(0)
            if size == 0:
                skipped_files.append(os.path.basename(f))
                print(f"\t{f} is empty. Skipping .. ")
                continue
            print(f"\t{upload_dic[f]}")
            nc.files.upload_stream(upload_dic[f], file_handle, chunk_size=50*1024*1024)

    print("Finished uploading.")
    # Time stamp for expiration date
    tshare = datetime.date.today()
    tshare = tshare + datetime.timedelta(days=int(days_to_share))
    tshare = time.mktime(tshare.timetuple())

    share = nc.files.sharing.create(base_destination, share_type=3, permissions=1, expire_date=datetime.datetime.fromtimestamp(tshare))
    raw_data = vars(share).get("_raw_data", {})
    link_info = {
        'id': raw_data.get("id"),
        'path': raw_data.get("path"),
        'url': raw_data.get("url"),
        'token': raw_data.get("token")
    }
    private_link=get_ownCloud_links(link_info,configdic["owncloud_address"])

    # nc.logout()

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
        publink = link_info.get("url", "<no-url>")
        issueMSG="Public link: %s; Private link: %s; Commit message: %s" \
        %(publink, private_link,message)
        git.git_write_comment(issueMSG,config.get_github_api(configdic["github_address"]),\
        configdic["github_organization"],project_name,str(issue),\
        github_user=configdic["github_user"],github_pass=configdic["github_pass"])

downloadreqs=["owncloud_address","owncloud_upload_folder",\
"owncloud_download_folder","owncloud_user",\
"owncloud_pass","local_path"]


def ownCloud_download(gitssh=None, pick_a_date=None):
    configdic = config.read_bitconfig()
    for r in downloadreqs:
        while configdic[r] is None:
            configdic = config.check_reqs([r], configdic, config_file=None, gitssh=gitssh)

    local_path = os.path.abspath(configdic["local_path"])
    size_local = len(local_path.split("/"))

    f = os.path.abspath(str(pick_a_date))
    parent_folder = f.split("/")[size_local]
    project_name = f.split("/")[size_local + 1]

    target_project = parent_folder + "/" + project_name
    base_destination = get_owncloud_base_folder(configdic, target_project, getfolder=True, pick_a_date=pick_a_date)

    try:
        nc = Nextcloud(
            nextcloud_url=configdic["owncloud_address"],
            nc_auth_user=configdic["owncloud_user"],
            nc_auth_pass=configdic["owncloud_pass"]
        )
    except Exception as e:
        print("Could not login to Cloud.\nPlease make sure you are giving \
        the right address to your Cloud and using the right login credentials.")
        sys.exit(0)
        sys.exit(1)

    download_dir = f"{pick_a_date}_download"
    os.makedirs(download_dir, exist_ok=True)

    try:
        def download_recursive(remote_dir, local_dir):
            os.makedirs(local_dir, exist_ok=True)
            entries = nc.files.listdir(remote_dir)
            for entry in entries:
                remote_path = f"{remote_dir}/{entry.name}"
                local_path = os.path.join(local_dir, entry.name)
                if entry.is_dir:
                    download_recursive(remote_path, local_path)
                else:
                    with open(local_path, "wb") as f_out:
                        nc.files.download2stream(remote_path, f_out)

        download_recursive(base_destination, download_dir)

    except Exception as e:
        print(f"Error downloading files: {e}")
        shutil.rmtree(download_dir, ignore_errors=True)
        sys.exit(1)


    # Zip the folder
    zip_filename = f"{pick_a_date}.zip"
    shutil.make_archive(pick_a_date, 'zip', download_dir)
    shutil.rmtree(download_dir)

    print(f"Downloaded {zip_filename}")
    sys.stdout.flush()



def ownCloud_create_folder(gitssh=None, pick_a_date=None, days_to_share=None):
    configdic = config.read_bitconfig()
    for r in downloadreqs:
        while configdic[r] is None:
            configdic = config.check_reqs([r], configdic, config_file=None, gitssh=gitssh)

    local_path = os.path.abspath(configdic["local_path"])
    size_local = len(local_path.split("/"))

    f = os.path.abspath(str(pick_a_date))
    parent_folder = f.split("/")[size_local]
    project_name = f.split("/")[size_local + 1]

    target_project = parent_folder + "/" + project_name
    base_destination = get_owncloud_base_folder(configdic, target_project, create_folder=True, pick_a_date=pick_a_date)

    try:
        nc = Nextcloud(
            nextcloud_url=configdic["owncloud_address"],
            nc_auth_user=configdic["owncloud_user"],
            nc_auth_pass=configdic["owncloud_pass"]
        )
    except Exception:
        print("Could not login to Cloud.\nPlease make sure you are giving \
        the right address to your Cloud and using the right login credentials.")
        sys.exit(0)

    check = base_destination.strip("/").split("/")
    print(check)
    for i in range(1, len(check) + 1):
        c = "/" + "/".join(check[:i])
        print(c)
        parent = os.path.dirname(c)
        name = os.path.basename(c)
        try:
            entries = nc.files.listdir(parent)
            if name not in [e.name for e in entries if e.is_dir]:
                nc.files.mkdir(c)
        except Exception as e:
            print(f"Failed creating {c}: {e}")

    # Create a public upload-enabled share link
    tshare = datetime.date.today() + datetime.timedelta(days=int(days_to_share))
    expiration = datetime.datetime.fromtimestamp(time.mktime(tshare.timetuple()))

    share = nc.files.sharing.create(
        base_destination,
        share_type=3,  # public link
        permissions=1 | 4,  # read + create (upload)
        expire_date=expiration
    )

    raw_data = vars(share).get("_raw_data", {})
    link_info = {
        'id': raw_data.get("id"),
        'path': raw_data.get("path"),
        'url': raw_data.get("url"),
        'token': raw_data.get("token")
    }
    private_link = get_ownCloud_links(link_info, configdic["owncloud_address"])
