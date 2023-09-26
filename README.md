# bit [![Build Status](https://travis-ci.org/mpg-age-bioinformatics/bit.svg?branch=master)](https://travis-ci.org/mpg-age-bioinformatics/bit)

**The [b]ermuda [i]nformation [t]riangle is a git-based tool for the management of code and data.**

It uses git for code versioning and ownCloud for storing and exchanging data. It avoids the costs of data versioning by logging changes in the data storage platform on github.

It is primarly made for multiple users working on the same projects on an HPC cluster but it can be easily used on local/cloud/non-HPC machines without changes to the code.

Data is transferred using http requests through the ownClowd API to avoid the risks of mounted drives and the need for ftp access.

Every time data is uploaded to ownClowd, the upload is registered on the respective wiki on github together with an hyperlink to the respective folder.

###### Concept

```
                          >links-to-data>
customer <<<<<<< github ------------------- ownCloud >>>>>>> customer
                       \                   /
                   code \                 /
              versioning \      bit      / data upload
                       &  \             / & download
          data upload logs \           /
                            \         /           rsync
                             HPC/local ------------------------HPC2/local2
```

###### Structure

**bit** enforces you to keep a clean house. It's based on structured folders and won't work without it.

Model:

```
/file_system_a
    |
    '- data
        |
        '- projects
            |
            |- Company_A
            |   |
            |   |- CA_project_y
            |   |
            |   '- CA_project_x
            |       |
            |       |- results
            |       |- models
            |       |- scripts
            |       |- tmp
            |       |- slurm_logs
            |       '- wiki
            |
            '- Company_B
                |
                '- CB_project_n
```

The labels are irrelevant as long as the projects/company_y/project_x structure is kept constant.

#### Example usage

**_Config_**
```bash
bit --config
```
Generate a config file with all required services addresses as well as user names and passwords if desired.

**_Start a project_**
```bash
bit --start CA_Johns_IL13
```
Initiated from inside the folder of "Company_A" it initiates the project "Johns_IL13" where "CA" stands for the initials of the parent folder for easy tracing in git and ownCloud.

**_Upload data_**
```bash
bit -i file.tar.bz2 -m my first upload
```
Upload a file to ownCloud, register the upload and https link to the data folder on the project's wiki, commit and push wiki to git. Returns a 21 days public link as well as a permanent private link to the data.

**_Bind data and code_**
```bash
bit -i file.tar.bz2 --scripts --issue 5 -m my first upload
```
Just like above but commiting and pushing the scripts folder to git enforcing therefore binding of code and data via the commit message.



#### Installation

```bash
git clone https://github.com/mpg-age-bioinformatics/bit.git
cd bit
python setup.py install -f --user
```

or

```
pip3 install git+git@github.com:mpg-age-bioinformatics/bit.git --user
```

###### Dependencies

* [git](https://git-scm.com)
* [curl](https://curl.haxx.se)
* [rsync](https://rsync.samba.org) (for *sync* options)
* [sshpass](https://sourceforge.net/projects/sshpass/) (for *sync* options)

Once you have **bit** on your path you should run `bit --config` to generate a config file.

#### Options

```
usage: bit [-h] [-i [INPUT [INPUT ...]]] [-s SUBFOLDER]
           [-m [MESSAGE [MESSAGE ...]]] [-d PICK_A_DATE] [-c] [-g]
           [-t DAYS_TO_SHARE] [--issue ISSUE] [--scripts] [--start START]
           [--stdfolders [STDFOLDERS [STDFOLDERS ...]]] [--adduser]
           [--sync [SYNC [SYNC ...]]] [--sync_to SYNC_TO]
           [--sync_from SYNC_FROM] [--cpus CPUS] [--forceRemote] [--gitssh]
           [--config]

bit, [b]ermuda [i]nformation [t]riangle. bit is a git-based tool for the
management of code and data. It uses git for code versioning and ownCloud for
storing and exchanging data. It saves storage by avoiding versioning of data
while logging changes in associated git wikis.

optional arguments:
  -h, --help            show this help message and exit
  -i [INPUT [INPUT ...]], --input [INPUT [INPUT ...]]
                        Input files (default: None)
  -s SUBFOLDER, --subfolder SUBFOLDER
                        Subfolder to be created. (default: None)
  -m [MESSAGE [MESSAGE ...]], --message [MESSAGE [MESSAGE ...]]
                        Message to write on log file. (default: None)
  -d PICK_A_DATE, --pick_a_date PICK_A_DATE
                        Pick an existing date folder to transfer data to/from.
                        Format=YYYY-MM-DD (default: None)
  -c, --create_folder   Create dropbox folder for user to upload data.
                        (default: False)
  -g, --getfolder       Downloads a folder as zip file. Requires
                        --pick_a_date. Defaults base_folder=upload:download to
                        download (default: False)
  -t DAYS_TO_SHARE, --days_to_share DAYS_TO_SHARE
                        Number of days you wish to share this folder further.
                        (default: 21)
  --issue ISSUE         Issue to comment on with --message and owncloud data
                        links (default: None)
  --scripts             Needs -i and -m. Simultaneously sync the scripts.user
                        folder when uploading data. (default: False)
  --start START         Project name of the format. PI_PROJECT_NAME. Initiates
                        a project. This will create the required local folders
                        and respective git repositories. (default: None)
  --stdfolders [STDFOLDERS [STDFOLDERS ...]]
                        Folders to be created in addition to scripts.user and
                        and wiki.user when a project is started. (default:
                        ['tmp', 'slurm_logs'])
  --adduser             Add a user to a project creating his scripts.user and
                        wiki.user folder (default: False)
  --sync [SYNC [SYNC ...]]
                        Files or folders to syncronize with remote server
                        using rsync over ssh. (default: None)
  --sync_to SYNC_TO     Destination server to sync to in the form:
                        <user_name>@<server.address> (default: None)
  --sync_from SYNC_FROM
                        Destination server to sync from in the form:
                        <user_name>@<server.address> (default: None)
  --cpus CPUS           Number of CPUs/channels to open for rsync. (default:
                        1)
  --forceRemote         If syncing from or to a remoter server force the
                        import of a remote 'bit_config'. (default: False)
  --gitssh              Use your git SSH keys. (default: False)
  --config              Generate a config file. (default: False)

```
