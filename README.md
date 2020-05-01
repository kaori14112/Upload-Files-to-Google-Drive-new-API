## This is a newer version of script upload files to Google Drive. Tested on Python 3.6
This is new version script upload file to google drive (compatible with http2lib 0.17.2 / google-api-python-client 1.8.0 - newest currently)
## How to use?
#### Install requirements libs for python: pip3 install -r .requirements --user

#### Enable google drive API and get credential json file: https://developers.google.com/drive/api/v3/quickstart/python

#### Just typing this command to upload files: python3 upload.py -s /local/directory/ -d Destination_Folder -p Parent_Folder
* Local directory: the folder on your local machine that you want to upload file from
* Destination Folder: the destination folder on google drive that you wanted to upload to
* Parent Folder: Just incase you upload wrong folder, define parent folder of destination folder. (you can upload 1 file or folder just need to fill -s with full path: ex: -p /root/backup/abc.tar.gz to upload file named abc.tar.gz, -p /root/backup/ if you want to upload all files in that folders)
* If destination folder not yet created then script will ask you want to create or not, type yes or y to execute / no or n to abort.
* Please report if you got problem, thank you.

#### Base on project: https://gist.github.com/jmlrt/f524e1a45205a0b9f169eb713a223330
* That project use PyDrive that no longer work with current API version, i have to rewrite it and add more tweak.
