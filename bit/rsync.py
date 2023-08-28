from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import sys
import getpass
from os.path import expanduser
from subprocess import Popen, PIPE, STDOUT
import stat
import tempfile

import bit.config as config

def get_remote_config(sshLogin,remotePass):
    remote_address=sshLogin.split("@")[1]
    call="sshpass -p "+remotePass+" scp "+sshLogin+":~/.bit_config \
    ~/.bit_config."+remote_address
    #print(call)
    os.system(call)
    uhome=expanduser("~")+"/"
    if os.path.isfile(uhome+".bit_config.%s" %remote_address) :
        os.chmod(uhome+".bit_config.%s" %remote_address, stat.S_IRWXU )
    else:
        print("Could not find ~/.bit_config on remote server.\
        \nPlease run 'bit --config' on remote server.")
        sys.exit(0)

def read_remote_config(sshLogin,remotePass,forceImport=None):
    remote_address=sshLogin.split("@")[1]
    if os.path.isfile(".bit_config.%s" %remote_address):
        if not forceImport:
            print("Using previously collected remote config.")
        else:
            get_remote_config(sshLogin,remotePass)
    else:
        get_remote_config(sshLogin,remotePass)

    remote_config=config.read_bitconfig(showit=None,bit_config=".bit_config.%s" \
    %remote_address)
    return remote_config

def list_local_sync(base_destination,list_of_files):

    # check if files all come from the same project folder
    configdic=config.read_bitconfig()
    local_path=configdic["local_path"]
    size_local=len(local_path.split("/"))
    parent_folder=[]
    check_project=[]
    for i in list_of_files:
        f=os.path.abspath(i)
        parent_folder.append(f.split("/")[size_local])
        check_project.append(f.split("/")[size_local+1])
    check_project=list(set(check_project))
    if len(check_project) > 1:
        print("Found more than one project:\n")
        for p in check_project:
            print(p)
            sys.stdout.flush()
        sys.exit(0)
    else:
        project_name=check_project[0]
        parent_folder=parent_folder[0]+"/"

    target_project=parent_folder+project_name

    base_destination=base_destination+"/"+parent_folder+"/"+project_name
    upload_dic={}
    subfolders=[base_destination]
    check=base_destination.split("/")
    for i in range(len(check)):
        c="/".join(check[:i-len(check)])
        subfolders.append(c)

    for f in list_of_files:
        full=os.path.abspath(f)
        if CheckFoldersCon(local_path,full):
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
                tfile=base_destination+full.split(local_path+"/"+target_project  )[1]
                upload_dic[full]=tfile
                subfolders.append( tfile.split(os.path.basename(tfile))[0] )
            else:
                upload_dic[full]=base_destination+"/"+os.path.basename(full)
        else:
            print("%s is either a link to %s or is not on your projects path. This file\
            will not be syncronized." %(f, full))
            sys.stdout.flush()

    subfolders=list(set(subfolders))
    subfolders=[ xx for xx in subfolders if len(xx) > 0 ]
    subfolders.sort()

    #print(upload_dic,"\n",subfolders)

    return upload_dic, subfolders, base_destination, parent_folder

def list_local_for_remote_sync(base_destination,list_of_files):

    # check if files all come from the same project folder
    configdic=config.read_bitconfig()
    local_path=configdic["local_path"]
    size_local=len(local_path.split("/"))
    parent_folder=[]
    check_project=[]
    for i in list_of_files:
        f=os.path.abspath(i)
        parent_folder.append(f.split("/")[size_local])
        check_project.append(f.split("/")[size_local+1])
    check_project=list(set(check_project))
    if len(check_project) > 1:
        print("Found more than one project:\n")
        for p in check_project:
            print(p)
            sys.stdout.flush()
        sys.exit(0)
    else:
        project_name=check_project[0]
        parent_folder=parent_folder[0]

    target_project=parent_folder+"/"+project_name

    base_destination=base_destination+parent_folder+"/"+project_name
    upload_dic={}
    subfolders=[base_destination]
    check=base_destination.split("/")
    for i in range(len(check)):
        c="/".join(check[:i-len(check)])
        subfolders.append(c)

    for f in list_of_files:
        full=os.path.abspath(f)
        if CheckFoldersCon(local_path,full):
            if os.path.isdir(full):
                subfol=base_destination+"/"+os.path.basename(full)
                upload_dic[full]=base_destination+"/"+os.path.basename(full)
                subfolders.append(subfol)
            elif os.path.isfile(full):
                tfile=base_destination+full.split(local_path+"/"+target_project  )[1]
                upload_dic[full]=tfile
                subfolders.append( tfile.split(os.path.basename(tfile))[0] )
            else:
                upload_dic[full]=base_destination+"/"+os.path.basename(full)
        else:
            print("%s is either a link to %s or is not on your projects path. This file\
            will not be syncronized." %(f, full))
            sys.stdout.flush()

    subfolders=list(set(subfolders))
    subfolders=[ xx for xx in subfolders if len(xx) > 0 ]
    subfolders.sort()

    return upload_dic, subfolders, base_destination, parent_folder

def CheckFoldersCon(base,files_to_check):
    lbase=len(base)
    if files_to_check[:lbase] == base:
        return True
    else:
        return False

def rsync_to(sshLogin,rsync_files,forceImport=None,sync_to=True,sync_from=False):#,n_processors=1):
    remotePass=str(getpass.getpass(prompt="Please give in your password for %s:\
     " %sshLogin.split("@")[1] ))

    remote_config=read_remote_config(sshLogin,remotePass,forceImport)
    remote_path=remote_config["local_path"]
    sync_dic, subfolders, path_to_project, parent_folder=list_local_sync(remote_path,\
    rsync_files)

    create_subfolders=[ ff for ff in subfolders if ff not in remote_path ]
    create_subfolders=" ".join(create_subfolders)

    # if remote_config["user_group"]:
    #     remote_group=" ".join(remote_config["user_group"])
    #     remote_group_group="; chmod 700 "+remote_path+parent_folder+" ; for us in "\
    #     +remote_group+" ; do setfacl -m user:${us}:rwx "+remote_path+parent_folder+" ; done "

    #     remote_group_project="; chmod 700 "+path_to_project+" ; for us in "\
    #     +remote_group+" ; do setfacl -m user:${us}:rwx "+path_to_project+" ; done "
    # else:
    remote_group_group="; echo Not_using_acls "
    remote_group_project="; echo Not_using_acls "

    create_subfolders="\'MANAGER=$(ls -ld "+remote_path+" | awk \"{ print \\$3 }\" ); \
    if [ ! -d "+remote_path+"/"+parent_folder+" ]; then mkdir -p "+remote_path+"/"+\
    parent_folder+remote_group_group+"; chown $MANAGER "+remote_path+"/"+parent_folder+"; fi; \
    if [ ! -d "+path_to_project+" ]; then mkdir -p "+path_to_project+remote_group_project+"; \
    chown $MANAGER "+path_to_project+"; fi; \
    for f in "+create_subfolders+"; do if [ ! -d $f ]; then mkdir -p $f; fi; done\'"

    create_subfolders="sshpass -p "+str(remotePass)+" ssh "+str(sshLogin)+" "+create_subfolders
    os.system(create_subfolders)

#    def SENDFILES(f,sync_dic=sync_dic,remotePass=remotePass,sshLogin=sshLogin):
#        call='rsync -tlzhPL --rsh="sshpass -p %s ssh -o \
#        StrictHostKeyChecking=no -l %s" %s %s:%s' %(str(remotePass), \
#        str(sshLogin.split("@")[0]), f,  str(sshLogin.split("@")[1]), \
#        sync_dic[f])
#        print(f)
#        sys.stdout.flush()
#        print(call)
#        #os.system(call)
#        return f

    #pool = mp.Pool(n_processors)
    funclist = []
    for f in sync_dic:
        call='rsync -rtlzhP --rsh="sshpass -p %s ssh -o StrictHostKeyChecking=no -l %s" %s %s:%s' \
        %(str(remotePass), str(sshLogin.split("@")[0]), f,  str(sshLogin.split("@")[1]), sync_dic[f])
        #print(call)
        funclist.append(call)
        #out=pool.apply_async(SENDFILES,[call])
        #funclist.append(out)
        #call='rsync -tlzhPL --rsh="sshpass -p %s ssh -o \
        #StrictHostKeyChecking=no -l %s" %s %s:%s' %(str(remotePass), \
        #str(sshLogin.split("@")[0]), f,  str(sshLogin.split("@")[1]), \
        #sync_dic[f])
        #os.system(call)
    #results=[]
    #for ff in funclist:
    #    res=ff.get()
    #    results.append(res)
    #    #print( res )
    #    #sys.stdout.flush()
    #print(results)
    return funclist

def rsync_from(sshLogin,rsync_files,forceImport=None,sync_to=False,sync_from=True):
    remotePass=str(getpass.getpass(prompt="Please give in your password for %s: "\
    %sshLogin.split("@")[1] ))

    configdic=config.read_bitconfig()
    local_path=configdic["local_path"]

    remote_config=read_remote_config(sshLogin,remotePass,forceImport)
    remote_path=remote_config["local_path"]

    # get remote dirs and subdirs

    sync_dic, subfolders, path_to_project, parent_folder=list_local_for_remote_sync(\
    remote_path, rsync_files)

    check_remote=[]
    for f in sync_dic:
         check_remote.append(sync_dic[f])
    check_remote=" ".join(check_remote)

    # check if files exist on remote
    temp=tempfile.NamedTemporaryFile()
    check_remote_files="\'for f in "+check_remote+" ; do if [ -f $f ]; then echo $f; fi; done\' > "+temp.name
    check_remote_files="sshpass -p "+str(remotePass)+" ssh "+str(sshLogin)+" "+check_remote_files
    os.system(check_remote_files)
    res=temp.readlines()
    temp.close()
    resFiles=[ s.strip("\n") for s in res ]

    # check if folders exist on remote
    temp=tempfile.NamedTemporaryFile()
    check_remote_folder="\'for f in "+check_remote+" ; do if [ -d $f ]; then echo $f; find $f -type d -print; fi; done\' > "+temp.name
    check_remote_folder="sshpass -p "+str(remotePass)+" ssh "+str(sshLogin)+" "+check_remote_folder
    os.system(check_remote_folder)
    res=temp.readlines()
    temp.close()
    resFolders=[ s.strip("\n")+"/" for s in res ]

    list_folders_contents=" ".join(resFolders)
    temp=tempfile.NamedTemporaryFile()
    check_remote_folder="\'for f in "+list_folders_contents+" ; do cd $f;\
    for c in $(ls); do cc=$(readlink -f $c); if [ -f $cc ]; then echo $cc; fi; done; done\' > "+temp.name
    check_remote_folder="sshpass -p "+str(remotePass)+" ssh "+str(sshLogin)+" "+check_remote_folder
    os.system(check_remote_folder)
    res=temp.readlines()
    temp.close()
    resAllFiles=[ s.strip("\n") for s in res ]

    res=[resFiles, resAllFiles] #resFolders
    res=[item for sublist in res for item in sublist]
    res=list(set(res))

    showres="\n".join(res)
    print("The following targets could be found on the remote server:\n%s" %showres)
    sys.stdout.flush()

    inv_sync_dic={}
    for r in res:
        inv_sync_dic[r]=local_path+"/"+r.split(remote_path)[1]

    lenLocalPath=len(os.path.abspath(local_path).split("/"))
    for remfold in resFolders:
        ltf=local_path+"/"+remfold.split(remote_path)[1]
        if not os.path.exists(ltf):
            os.makedirs(ltf)
            if len(os.path.abspath(ltf).split("/")) in [lenLocalPath+1,lenLocalPath+2]:
                if configdic["user_group"]:
                    os.chmod(ltf, stat.S_IRWXU)
                    user_group=configdic["user_group"]
                    try:
                        for use in user_group:
                            call=["setfacl","-m","user:%s:rwx" %use,ltf]
                            out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
                            print(out.communicate()[0].rstrip())

                    except:
                        print("Failed to setfacls.")
                        sys.stdout.flush()
                local_path_owner=os.stat(local_path)
                local_path_owner=local_path_owner.st_uid
                os.chown(ltf,local_path_owner,-1)
    sync_from_calls=[]
    for f in inv_sync_dic:
        call='rsync -tlzhP --rsh="sshpass -p %s ssh -o \
        StrictHostKeyChecking=no -l %s" %s:%s %s' %(str(remotePass), \
        str(sshLogin.split("@")[0]), str(sshLogin.split("@")[1]), \
        f, inv_sync_dic[f] )
        sync_from_calls.append(call)
        #os.system(call)
    return sync_from_calls
