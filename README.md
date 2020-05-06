## This is a newer version of script upload files to Google Drive. Tested on Python 3.6
This is new version script upload file to google drive (compatible with http2lib 0.17.3 / google-api-python-client 1.8.2 - newest currently)
## How to use?
#### Install requirements libs for python: pip3 install -r .requirements --user
 
#### Enable google drive API and get credential json file: https://developers.google.com/drive/api/v3/quickstart/python
 
#### Put json file on a same folder at script
 
#### Just typing this command to upload files: python3 upload.py -s /local/directory/ -d Destination_Folder -p Parent_Folder
 
- Local directory: the folder on your local machine that you want to upload file from
 
- Destination Folder: the destination folder on google drive that you wanted to upload to
 
- Parent Folder: Just incase you upload wrong folder, define parent folder of destination folder. (you can upload 1 file or folder just need to fill `-s` with full path: ex: **-p /root/backup/abc.tar.gz** to upload file named abc.tar.gz, **-p /root/backup/** if you want to upload all files in that folders)
 
- If destination folder not yet created on Google Drive (GGDR) then script will ask you want to create or not, type `yes or y` to execute / `no or n` to abort.
 
- You can upload to any folder you want, if you not define destination folder (only defined parent folder `-p`) then it will create destination folder under parent folder for you, ex: **python3 upload.py -s /home/test/ -p parent_test**
 
- If you not define parent folder (only defined destination folder `-d`), it will upload to destination folder on root of GGDR , ex: **python3 upload.py -s /home/test/ -d abc**
 
- If you not define parent and destination folder, default it will upload to root directory on GGDR, ex: **python3 upload.py -s /home/test/**
 
- If you want to upload single file? Simply just type full path to that file, ex: **python3 -s /home/test/abc.tar.gz -d abc -p parent_abc**
 
* Please report if you got problem, thank you.
 
#### Base on project: https://gist.github.com/jmlrt/f524e1a45205a0b9f169eb713a223330
 
That project use PyDrive library that no longer work with current API version, i have to rewrite it and add more tweak.
 
