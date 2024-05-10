import smtplib, ssl

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

import re

import subprocess
from subprocess import Popen, PIPE, STDOUT
import requests
import json
import sys

import os

from bit.config import read_bitconfig

groups_dic={"Adam_Antebi":"AA",\
"Aleksandra_Filipovska":"AF",\
"Anne_Schaefer":"AS",\
"Bioinformatics":"bit",\
"Constantinos_Demetriades":"CD",\
"CRISPR_Screening":"CS",\
"Dario_Valenzano":"DV",\
"Ivan_Matic":"IM",\
"James_Stewart":"JS",\
"Lena_Pernas":"LPe",\
"Linda_Partridge":"LP",\
"Martin_Denzel":"MD",\
"Martin_Graef":"MG",\
"Metabolomics":"met",\
"Nils_Larson":"NL",\
"Peter_Tessarz":"PT",\
"Phenotyping":"Ph",\
"Proteomics":"Prot",\
"Ron_Jachimowicz":"RJ",\
"Sara_Wickstroem":"SW",\
"Stephanie_Panier":"SP",\
"Thomas_Langer":"TL",\
"Zachary_Frentz":"ZF"}

def isnotebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Proba

def read_config(config_file="/beegfs/group_bit/data/projects/departments/Bioinformatics/bit_automation/automation.config"):
    config_dic={}
    with open(config_file, "r") as file_in:
        for line in file_in:
            line=line.rstrip("\n")
            line=line.split(" ")
            config_dic[line[0]]=line[1]
            
    bit_config=read_bitconfig()
    config_dic["github_user"]=bit_config["github_user"]
    config_dic["github_pass"]=bit_config["github_pass"]
    config_dic["DAVIDUSER"]=bit_config["DAVIDUSER"]

    return config_dic
    
def send_email(subject, body="", EMAIL_TOKEN=None, \
               attach=None, \
               toaddr=[],\
               fromaddr="automation@age.mpg.de",\
               project_type=None,\
               config_dic=None):
    if not EMAIL_TOKEN:
        EMAIL_TOKEN=config_dic["EMAIL_TOKEN"]
    if not project_type:
        project_type="["+config_dic["project_type"]+"]"
    elif project_type=="empty":
        project_type=""
    else:
        project_type="["+project_type+"]"

    msg = MIMEMultipart()
    
    static_receiver=["automation@age.mpg.de"]
    toaddr=static_receiver+toaddr

    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)
    
    if str(subject)[0] != "[":
        subject=" "+subject
    
    msg['Subject'] = "{project_type}{subject}".format(project_type=project_type,subject=subject)
    msg.attach(MIMEText(body, 'plain'))

    if attach:
        attachment = open(str(attach), "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % report_file)
        msg.attach(part)

#     server = smtplib.SMTP_SSL('mail.age.mpg.de', 587)
#     server.login(fromaddr, EMAIL_TOKEN)
#     text = msg.as_string()
#     server.sendmail(fromaddr, toaddr, text)
#     server.quit()
    context = ssl.create_default_context()
    with smtplib.SMTP("mail.age.mpg.de", 587) as server:
        server.starttls(context=context)
        server.login(fromaddr, EMAIL_TOKEN)
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
#     server.quit()
#     print( f'Email sent to {", ".join(toaddr)}' )
    print( "Email sent to {toaddr}".format(toaddr=', '.join(toaddr) ) )
    sys.stdout.flush()
    
def check_email(email,config_dic,submission_file):
    email=str(email).rstrip().lstrip()
    email=email.split(",")
    email=[ re.search("([^@|\s]+@[^@]+\.[^@|\s]+)",e,re.I) for e in email ]
    email=[ e.group(1) for e in email if e ]
    if not email :
        print("Contact email not provided." )
        sys.stdout.flush()
        send_email("contact email not provided.",\
                   "For {submission_file} contact email not provided.".format(submission_file=submission_file),\
                    config_dic=config_dic)
        sys.exit(1)
    return email

def check_group(group,submission_file,email,project_type,config_dic):
    if group not in list(groups_dic.keys()):
        print("Group {group} does not exist.".format(group=group) )
        sys.stdout.flush()
        # send_email("group does not exist",\
        #            "For {submission_file} group {group} does not exist. Assuming External.".format(submission_file=submission_file,group=group),\
        #            toaddr=[], 
        #           EMAIL_TOKEN=config_dic["EMAIL_TOKEN"],
        #           project_type=project_type)

        user_domain=[ s for s in email if "mpg.de" in s ]
        if user_domain:

            user_domain=user_domain[0].split("@")[-1]
            mps_domain="mpg.de"

            if ( user_domain[-len(mps_domain):] == mps_domain ) :
                return user_domain.split(".mpg.de")[0]

        return "bit_ext"
        
    else:
        return groups_dic[group]

def check_project_exists(folder,config_dic,group,project_title, email):
    if os.path.isdir(folder):
        send_email("[{group_prefix}_{project_title}] project already exists".format(group_prefix=groups_dic[group],project_title=project_title),\
                   "{project_title} already exists. Please submit again using a different project name.\n{folder}".format(project_title=project_title,folder=folder),\
                   toaddr=email, 
                   config_dic=config_dic  )
        print("{folder} already exists".format(folder=folder))
        sys.stdout.flush()
        sys.exit(1)
    return True

def check_source_files(files,md5file,store_age_folder,GET_RAW,project_title,email,config_dic,metadata):
    for f in files:
        if ( not os.path.exists(store_age_folder+f) ) & ( GET_RAW ):
            send_email("[{group_prefix}_{project_title}] raw data file missing".format(group_prefix=groups_dic[metadata["Group"]],project_title=project_title),\
                       "{f} missing".format(f=f),\
                       toaddr=email, 
                       config_dic=config_dic)
            print("{f} missing".format(f=store_age_folder+f))
            sys.stdout.flush()
            sys.exit(1)
     
    if md5file:
        if ( not os.path.exists(store_age_folder+md5file) ) & ( GET_RAW ):
            send_email("[{group_prefix}_{project_title}] md5sums file missing".format(group_prefix=groups_dic[metadata["Group"]],project_title=metadata["Project title"]),\
                       "{f} missing".format(f=f),\
                       toaddr=email, 
                       config_dic=config_dic)
            print("md5sums file missing".format(f=f))
            sys.stdout.flush()
            sys.exit(1)
    return True


def verify_md5sum(md5sums,md5file_in):
    for file in list(md5sums.keys()):
        with open(md5file_in, "r") as md5file:
            md5check=False
            for line in md5file:
                if file in line:
                    if md5sums[file] in line:
                        md5check=True
            if not md5check:
                return file
            
    return False

def md5sumcheck(file,config_dic,group,project_title,project_archive,email,md5file):
    cmd = [ "md5sum", file ] 
    sys.stdout.flush()
    out=Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    re=str( out.communicate()[0].decode('utf-8').rstrip()) 
    out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass
    md5sum=str(re).split(" ")[0]
    md5sums={ os.path.basename(file): md5sum }
    
    missing_file=verify_md5sum(md5sums,project_archive+md5file)
    if missing_file:
        send_email("[{group_prefix}_{project_title}] md5sum could not be comfirmed".format(group_prefix=groups_dic[group],project_title=project_title),\
                   "{file} missing".format(file=missing_file),\
                   toaddr=email, 
                   config_dic=config_dic)
        print("{file} md5 missing".format(file=missing_file))
        sys.stdout.flush()
        sys.exit(1)
    return True

def make_github_repo( repo_name, user, token, config_dic):
    url = 'https://github.molgen.mpg.de/api/v3/orgs/mpg-age-bioinformatics/repos'
    repo = { "name" : repo_name , \
             "private" : 'true' ,\
             "auto_init": 'true' }
    response = requests.post( url, data=json.dumps(repo), auth=( user, token ))#, headers=headers)
    if response.status_code == 201:
        print('Successfully created Repository "%s"' % repo_name )

    else:
        print('Could not create Repository "%s"' % repo_name)
        print('Response:', response.content)
        send_email("[{repo_name}] repository could not be created".format(repo_name=repo_name), 
                      config_dic=config_dic)
        sys.stdout.flush()
        sys.exit(1)
    return response

def make_github_issue(title, repo_name, user, token, config_dic, body=None, assignee=None ):
    '''Create an issue on github.com using the given parameters.'''
    # Our url to create issues via POST
    url = 'https://github.molgen.mpg.de/api/v3/repos/mpg-age-bioinformatics/{repo_name}/issues'.format(repo_name=repo_name)
    issue = {'title': title,\
            'assignee': assignee}
    # Add the issue to our repository
    response = requests.post( url, data=json.dumps(issue), headers={"Accept": "application/vnd.github.v3+json"}, auth=( user, token ))#, headers=headers)
    
    if response.status_code == 201:
        print('Successfully created Issue "%s"' % title )

    else:
        print('Could not create Issue "%s"' % title)
        print('Response:', response.content)
        print(response.text)
        send_email("[{repo}] could not create Issue".format(repo=repo_name), 
                        config_dic=config_dic)
        sys.stdout.flush()
        sys.exit(1)
    return response

def make_github_card(make_issue_response, repo_name, user, token, config_dic, column=301):
    '''Create an card for an issue on github.com using the given parameters.'''
    # Our url to create issues via POST
    url = f'https://github.molgen.mpg.de/api/v3/projects/columns/{column}/cards'
    issue_response=json.loads(make_issue_response.text)
    issue_id=issue_response["id"]
    card = {'content_id': issue_id,\
            "content_type":"Issue"}
    # Add the issue to our repository
    response = requests.post( url, data=json.dumps(card), headers={"Accept": "application/vnd.github.inertia-preview+json"}, auth=( user, token ))#, headers=headers)
    
    if response.status_code == 201:
        print('Successfully created card.' )
    else:
        print('Could not create card.')
        print('Response:', response.content)
        print(response.text)
        send_email("[{repo}] could not create card".format(repo=repo_name), 
                        config_dic=config_dic)
        sys.stdout.flush()
        sys.exit(1)
    return response

def git_clone(local_name,github_repo, team_members=None):
    git="git@github.molgen.mpg.de:mpg-age-bioinformatics/{github_repo}.git".format(github_repo=github_repo)
    # cwd = os.getcwd()
    # os.chdir(local_name)
    # out=subprocess.call(['git','init'])
    # out=subprocess.call(['git','config','remote.origin.url',git])
    # out=subprocess.call(['git','config','branch.master.remote','origin'])
    # out=subprocess.call(['git','config','branch.master.merge','refs/heads/master'])
    # out=subprocess.call(['git','pull', git])
    out=subprocess.call(['git','clone',git, local_name ])
    # if not os.path.exists(local_name):
    #     os.makedirs(local_name)
    #if team_members:
    #    for t in team_members.split(","):
    #        out=subprocess.call(['setfacl', '-Rdm', f'u:{t}:rx', local_name ])
    #else:
    #out=subprocess.call(['setfacl', '-Rdm', 'g:group_bit:rx', local_name ])
    out=subprocess.call(['chmod', '-R','g+r', local_name ])
    # os.chdir(cwd)
    return out

def git_fetch(github_repo):
    git="git@github.molgen.mpg.de:mpg-age-bioinformatics/{github_repo}.git".format(github_repo=github_repo)
    call=["git","fetch",git]
    out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    print(str( out.communicate()[0].decode('utf-8').rstrip()) )
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
    print(str( out.communicate()[0].decode('utf-8').rstrip()) )
    out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass

def git_pull(github_repo):
    git="git@github.molgen.mpg.de:mpg-age-bioinformatics/{github_repo}.git".format(github_repo=github_repo)
    call=["git","pull",git]
    out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    print(str( out.communicate()[0].decode('utf-8').rstrip()) )
    out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass

def git_add():
    call=["git","add","-A", "." ]
    out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    print(str(out.communicate()[0].decode('utf-8').rstrip()) )
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
    print(str( out.communicate()[0].decode('utf-8').rstrip()) )
    out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass

def git_push(github_repo):
    git="git@github.molgen.mpg.de:mpg-age-bioinformatics/{github_repo}.git".format(github_repo=github_repo)
    call=["git","push",git,"--all"]
    out=Popen(call, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    print(str( out.communicate()[0].decode('utf-8').rstrip()) )
    out.stdout.close()
    out.stdin.close()
    out.stderr.close()
    try:
        out.kill()
    except:
        pass

def git_sync(local_name, github_repo, message):
    cwd = os.getcwd()
    os.chdir(local_name)
    git_add()
    git_commit(message)
    git_fetch(github_repo)
    git_merge(message)
    git_push(github_repo)
    os.chdir(cwd)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="automation helper",\
    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-e", "--email", help="Email subject.")
    parser.add_argument("-p", "--project", help="Project type. eg. RNAseq.", default="empty")
    parser.add_argument("-t", "--to", help="Receivers.",default=None)
    parser.add_argument("-l", "--link", help="Link to results.",default=None)
    parser.add_argument("-c", "--config", help="Path to automation config file.",default=None)
    args = parser.parse_args()

    config_dic=read_config(args.config)

    if args.link:
        body="Hi,\n\nyou can find the results for this project here:\n\n{link}\n\nThis is an automatically generated email.".format(link=args.link)
    else:
        body=""

    if args.to:
        to=str(args.to).split(",")
    else:
        to=[]
    
    send_email(args.email, body=body, \
               attach=None, \
               toaddr=to,\
               fromaddr="automation@age.mpg.de",\
               project_type=args.project,\
               config_dic=config_dic)
        
    sys.exit(0)
