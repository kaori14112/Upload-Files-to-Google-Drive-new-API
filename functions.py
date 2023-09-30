from __future__ import print_function
import pickle
import os.path

#Import google API libraries
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.errors

# Import general libraries
from argparse import ArgumentParser
from os import chdir, listdir, stat
from sys import exit
from datetime import datetime
import sys
import ast
import magic
import hashlib
import threading

# Global list to store file information for upload
upload_list = []



# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


def parse_args():
    """
                Parse arguments
        """

    parser = ArgumentParser(
                description="Upload local folder to Google Drive")
    parser.add_argument('-s', '--source', type=str,
                                                  help='Folder to upload')
    parser.add_argument('-d', '--destination', type=str,
                                                  help='Destination Folder in Google Drive')
    parser.add_argument('-p', '--parent', type=str,
                                                  help='Parent Folder in Google Drive')

    return parser.parse_args()
    
def logging(log, level=0):
    curr_time = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
    if level == 0:
        print(curr_time + "[INFO] " + log)
    elif level == 1:
        print(curr_time + "[WARN] " + log)
    elif level == 2:
        print(curr_time + "[CRIT] " + log)


def convert_string(str):
#    for char in string.punctuation:
#        str = str.replace(char, '_')
    for char in str:
        if char in list_char:
            str = str.replace(char,"_")
        if char == "'":
            str = str.replace(char,";")
        if char == '"':
            str = str.replace(char,"'")
    return str


def authentication():
    """
                Authenticate to Google API
        """

    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            checkPath('credentials.json')
            flow = InstalledAppFlow.from_client_secrets_file(
                   'credentials.json', SCOPES)
            #EDIT below to change authentication method, i prefered run on Console cause i'm using linux server without UI
            #creds = flow.run_local_server(port=0)
            creds = flow.run_console()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds
    

def humanbytes(B):
   'Return the given bytes as a human friendly KB, MB, GB, or TB string'
   B = float(B)
   KB = float(1024)
   MB = float(KB ** 2) # 1,048,576
   GB = float(KB ** 3) # 1,073,741,824
   TB = float(KB ** 4) # 1,099,511,627,776

   if B < KB:
      return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
   elif KB <= B < MB:
      return '{0:.2f} KB'.format(B/KB)
   elif MB <= B < GB:
      return '{0:.2f} MB'.format(B/MB)
   elif GB <= B < TB:
      return '{0:.2f} GB'.format(B/GB)
   elif TB <= B:
      return '{0:.2f} TB'.format(B/TB)
      
      
def convert_size_to_bytes(size_str):
    # Split the string into parts (e.g., "0.0" and "Byte")
    parts = size_str.split()
    
    # Check if the parts contain a valid number and unit
    if len(parts) != 2 or not parts[0].replace('.', '', 1).isdigit():
        raise ValueError("Invalid file size format")
    
    # Extract the numerical part and convert it to a float
    size_num = float(parts[0])
    
    # Define a dictionary to map units to bytes
    size_units = {
        "Byte": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
        "PB": 1024**5,
        "EB": 1024**6,
        "ZB": 1024**7,
        "YB": 1024**8
    }
    
    # Get the unit and convert the size to bytes
    size_unit = parts[1]
    if size_unit in size_units:
        size_in_bytes = int(size_num * size_units[size_unit])
        return size_in_bytes
    else:
        raise ValueError("Invalid file size unit")


def checkDir(path):
    """
                Checking if given path is File or not
        """

    isFile = os.path.isfile(path)
    return isFile


def checkPathex(path):
    """
                Checking if given path is exist or not
        """

    isExist = os.path.exists(path)
    return isExist


def checkPath(path):
    isEx = checkPathex(path)

    # Print error if source folder doesn't exist
    if isEx == False:
        logging('%s does not exist!' % path)
        exit()
    else:
        # Determine if Path is File or Folder
        isFile = checkDir(path)
        return isFile
        
        
def checkmd5(file_path):
    # Calculate the MD5 checksum of the file
    logging("Calculating md5 of: %s" % file_path)
    md5_hash = hashlib.md5()
    if (os.path.isfile(file_path)):
        with open(file_path, "rb") as file:
            # Read the file in small chunks to save memory
            for chunk in iter(lambda: file.read(4096), b""):
                md5_hash.update(chunk)
            
        return md5_hash.hexdigest()
    else:
        return "hash_not_found"


def upload(service, path, folder_id, d_folder):

    chkPath = checkPath(path)

    if chkPath == True: #file
        logging('Uploading file from %s to: %s ...' % (path, d_folder))
        upload_file(service, path , folder_id)
        logging('Complete uploaded files to gg drive folder: %s - Google Drive folder ID: %s'  % (d_folder, folder_id))
    else: #folder
        logging('Uploading files from %s to: %s ...'  % (path, d_folder))
        results = upload_folder(service, path, folder_id)

        if results == False:
            logging('Upload Failed.')
        else:
            logging('Complete uploaded folder to drive folder: %s - FolderID: %s' % (d_folder, folder_id))


def isdir(path, x):
    path = os.path.join(path, x)
    return os.path.isdir(path)


def sort_dir(path):
    arr = os.listdir(path)
    arr.sort(key=lambda x: (isdir(path, x), x))
    return arr


def generate_space(lenght):
    space = ' '
    return lenght*space


def absolutePath(path):
    return os.path.abspath(path)
    
    
def search_file_or_folder(drive_service, name, md5, f_flag):
    """
            Search file / folder with name and hash from specific path
        """    
    page_token = None

    if f_flag == 0: #folder
        while True:
            try:
                response = drive_service.files().list(q="mimeType='application/vnd.google-apps.folder'",
                                                  spaces='drive',
                                                  fields='nextPageToken, files(id, name)',
                                                  pageToken=page_token).execute()
            
            except googleapiclient.errors.HttpError as err:
            #Parse error message
                message = ast.literal_eval(err.content)['error']['message']

                if message == 'File not found: ':
                    logging(message + name, 2)
                    # Exit with stacktrace in case of other errors
                    exit(1)
                else:
                    raise
            for folder in response.get('files', []):
                if folder['name'] == name:
                    return folder['id']
    elif f_flag == 1: #folder
        while True:
            try:
                response = drive_service.files().list(q="mimeType != 'application/vnd.google-apps.folder' and name = '" + name + "'",
                                                  spaces='drive',
                                                  fields='files(id, name, md5Checksum)'
                                                  ).execute()
            
            except googleapiclient.errors.HttpError as err:
            #Parse error message
                message = ast.literal_eval(err.content)['error']['message']

                if message == 'File not found: ':
                    logging(message + name, 2)
                    # Exit with stacktrace in case of other errors
                    exit(1)
                else:
                    raise
            
            filtered_files = [file for file in response.get('files', []) if 'md5Checksum' in file]
            if len(filtered_files) > 0:
                #print(filtered_files)
                for item in filtered_files:
                    if item['md5Checksum'] == str(md5):
                        return item['md5Checksum']
                logging("file are not yet exist on Google Drive (md5 not match), uploading new file...")
                return ""
            else:
                logging("file are not yet exist on Google Drive, uploading...")
                return ""
    else:
        return ""

def get_folder_id(drive_service, parent_folder_id, d_folder, flag):
    """
                Check if destination folder exists and return it's ID
        """

    page_token = None

    while True:
        try:
            response = drive_service.files().list(q="mimeType='application/vnd.google-apps.folder' and '" + parent_folder_id +"' in parents",
                                                  spaces='drive',
                                                  fields='nextPageToken, files(id, name)',
                                                  pageToken=page_token).execute()

        except googleapiclient.errors.HttpError as err:
            #Parse error message
            message = ast.literal_eval(err.content)['error']['message']

            if message == 'File not found: ':
                logging(message + d_folder, 2)
                # Exit with stacktrace in case of other errors
                exit(1)
            else:
                raise

        for folder in response.get('files', []):
            if folder['name'] == d_folder:
                if flag == 'p':
                    logging("Parent Folder: %s - id: %s" % (folder['name'], folder['id']))
                    return folder['id']
                    break
                elif flag == 'c':
                    logging("Destination Folder : %s - id: %s" % (folder['name'], folder['id']))
                    return folder['id']
                    break
                else:
                    return folder['id']
                    break

        page_token = response.get('nextPageToken', None)

        if page_token is None:
            break


def upload_file(service, file_dir, folder_id):
    """
                Upload files in the local folder to Google Drive
        """

    mime = magic.Magic(mime=True)
    file1 = os.path.basename(file_dir)

    # Check the file's size
    statinfo = stat(file_dir)

    if statinfo.st_size > 0:

#       print('uploading ' + file1 + '... ')

        #get mime types
        mine_type = mime.from_file(file_dir)

        # Upload file to folder.
        media = MediaFileUpload(
                file_dir,
                mimetype=mine_type,
                resumable=True
        )

        request = service.files().create(
                  media_body=media,
                  body={'name': file1,
                        'parents': [folder_id]
                       }
        )

        response = None

        logging("uploading %s..." % file1)
        a = 0
        while response is None:
            status, response = request.next_chunk()
            if a == 1:
                if status:
                    previous_progress_message = "Current: %s / Total: %s - %.2f%%" % (humanbytes(status.resumable_progress), humanbytes(status.total_size), status.progress() * 100)
                    padding = ' ' * (len(previous_progress_message) + 2)  # Add 2 for the carriage return and space

                    print(padding, end="\r")  # Clear the line
                    print("Current: %s / Total: %s - %.2f%%" % (humanbytes(status.resumable_progress), humanbytes(status.total_size), status.progress() * 100), end="\r", flush=True)
                    a = 0
            elif a == 0:
#                lenght = len(file1) + 11
#                space = generate_space(lenght)
                if status:
                    previous_progress_message = "Current: %s / Total: %s - %.2f%%" % (humanbytes(status.resumable_progress), humanbytes(status.total_size), status.progress() * 100)
                    padding = ' ' * (len(previous_progress_message) + 2)  # Add 2 for the carriage return and space

                    print(padding, end="\r")  # Clear the line
                    print("Current: %s / Total: %s - %.2f%%" % (humanbytes(status.resumable_progress), humanbytes(status.total_size), status.progress() * 100), end="\r", flush=True)
                    
                    #print(str(datetime.now()) + "> " + "uploading " + file1 + " ... %d%%." % int(status.progress() * 100), end = "\r")

        #print(str(datetime.now()) + "> " + "uploading " + file1 + " ... 100%. ", end = "\r", flush=True)
        logging("File %s upload successfully!" % file1)
        print("\n")
#        print("Complete!")


def upload_folder(service, path, parent_folder_id):

    try:
        chdir(path)
    except OSError:
        logging('%s is missing, exiting...' % path, 1)
        return False

    if not os.listdir(path):
        logging('Directory is empty, moving to next folder...')
        return False

    arr = sort_dir(path)

    for name in arr:
        localpath = os.path.join(path, name)
#        print(localpath)

        if os.path.isfile(localpath):
            md5 = checkmd5(localpath)
            logging("local md5 %s is %s" % (name, md5))
            search_rs = search_file_or_folder(service, name, md5, 1)
            logging("ggdr md5 %s is %s" % (name, search_rs))
            if search_rs == "":
                upload_file(service, localpath, parent_folder_id)
            else:
                logging("file already exist on GGDr, skipping... \n")
                continue
            
        elif os.path.isdir(localpath):
            print('\n')
            logging('Processing Directory: %s' % localpath)

            FdID = get_folder_id(service, parent_folder_id, name, 'n')
            if FdID is not None:
                logging('Folder %s already exist on Google Drive' % name)
                logging('checking files on: %s...' % name)
                upload_folder(service, localpath, FdID)
            else:
                logging('Folder %s dont exist on Google Drive, creating...' % name, 1)
                n_FdID = create_folder(service, parent_folder_id, name)

                if n_FdID is not None:
                    logging('Create Folder %s successfully, id: %s' % (name, n_FdID))
                    logging('checking files on: %s...' % name)
                    upload_folder(service, localpath, n_FdID)
                else:
                    logging('Something definitely wrong while creating folder... Exiting...', 2)

    logging('All files in %s uploaded successfully!' % path)



def create_folder(service, p_folder_id, folder_name):
    file_metadata = {
        'name': folder_name,
        'parents': [p_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
    }

    file = service.files().create(body=file_metadata,
                                  fields='id').execute()
    return file.get('id')


def upload_mutiple_files(service, thread=4):
    upload_list_size = len(upload_list)
    if upload_list_size > 4:
        for i in range(4):
            thread = threading.Thread(target=upload_file, args=(service, upload_list[i]['path'], upload_list[i]['folder_id']))
            threads.append(thread)
            thread.start()
        # Wait for all threads to finish    
        for thread in threads:
            thread.join()
        
