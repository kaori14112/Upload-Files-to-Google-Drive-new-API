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
            flow = InstalledAppFlow.from_client_secrets_file(
                   'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


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
        print('\x1b[0;31;43m' + path + ' does not exist!' + '\x1b[0m')
        exit()
    else:
        # Determine if Path is File or Folder
        isFile = checkDir(path)
        return isFile
       
def upload(service, path, folder_id, d_folder):

    chkPath = checkPath(path)
    
    if chkPath == True:
        print ('\x1b[6;30;42m' + 'File detected, uploading: "' + d_folder + '" ...' + '\x1b[0m')
        upload_file(service, path , folder_id)
        print('Complete uploaded file to drive folder: "' + d_folder + '" - FolderID: ' + folder_id)
    else:
        print ('\x1b[6;30;42m' + 'Folder detected, uploading to: "' + d_folder + '"' + '\x1b[0m')
        results = upload_folder(service, path, folder_id)
        
        if results == False:
            print('Upload Failed.')
        else:
            print('Complete uploaded folder to drive folder: "' + d_folder + '" - FolderID: ' + folder_id)


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
                print(message + d_folder)
                # Exit with stacktrace in case of other errors
                exit(1)
            else:
                raise

        for folder in response.get('files', []):
            if folder['name'] == d_folder:
                if flag == 'p':
                    print ("Parent Folder: " + folder['name'] + " : " + folder['id'])
                    return folder['id']
                    break
                elif flag == 'c':
                    print ("Destination Folder : " + folder['name'] + " : " + folder['id'])
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
       
        print("uploading " + file1 + " ... 0%. ", end = "\r")
        a = 0
        while response is None:
            status, response = request.next_chunk()
            if a == 1:
                if status:
                    print("uploading " + file1 + " ... %d%%." % int(status.progress() * 100), end = "\r")
                    a = 0
            elif a == 0:
#                lenght = len(file1) + 11
#                space = generate_space(lenght)
                if status:
                    print(str(datetime.now()) + "> " + "uploading " + file1 + " ... %d%%." % int(status.progress() * 100), end = "\r")

        print(str(datetime.now()) + "> " + "uploading " + file1 + " ... 100%. ", end = "\r", flush=True)
        print("")
#        print("Complete!")


def upload_folder(service, path, parent_folder_id):

    try:
        chdir(path)
    except OSError:
        print(path + ' is missing, exiting...')
        return False
        
    if not os.listdir(path):
        print('Directory is empty, moving to next folder...')
        return False

    arr = sort_dir(path)

    for name in arr:
        localpath = os.path.join(path, name)
#        print(localpath)
        
        if os.path.isfile(localpath):
            upload_file(service, localpath, parent_folder_id)
        elif os.path.isdir(localpath):
            print('\n')
            print('Processing Directory: ' + '\x1b[6;30;42m' + localpath + '\x1b[0m')
                       
            FdID = get_folder_id(service, parent_folder_id, name, 'n')
            if FdID is not None:
                print('Folder "' + name + '" already exist on Google Drive, checking files on ' + '\x1b[6;30;42m' + name  + '...' + '\x1b[0m')
                print('checking files on: ' + '\x1b[6;30;42m' + name  + '...' + '\x1b[0m')
                upload_folder(service, localpath, FdID)
            else:
                print('Folder "' + name + '" dont exist on Google Drive, creating...')
                n_FdID = create_folder(service, parent_folder_id, name)

                if n_FdID is not None:
                    print('Create Folder "' + name  + '" successfully, id: ' + n_FdID)
                    print('checking files on: ' + '\x1b[6;30;42m' + name  + '...' + '\x1b[0m')
                    upload_folder(service, localpath, n_FdID)
                else:
                    print('Something definitely wrong while creating folder... Exiting...')

    print('All files in "' + path  + '" uploaded successfully!')



def create_folder(service, p_folder_id, folder_name):
    file_metadata = {
        'name': folder_name,
        'parents': [p_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
    }

    file = service.files().create(body=file_metadata,
                                  fields='id').execute()
    return file.get('id')



def main():

    #Variables
    args = parse_args()
    
    src_folder_name = args.source
    if src_folder_name == '.':
        src_folder_name = os.getcwd()
       
    checkfilepath = checkPath(src_folder_name)
    if checkfilepath != True:
        src_folder_name = absolutePath(src_folder_name)


    d_folder = args.destination
    p_folder = args.parent
    d_folder_id = None
    p_folder_id = None

    #Rewrite output (added time stamps)
    old_out = sys.stdout

    class St_ampe_dOut:
        """Stamped stdout."""
        nl = True

        def write(self, x):
            """Write function overloaded."""
            if x == '\n':
                old_out.write(x)
                self.nl = True
            elif self.nl:
                old_out.write('%s> %s' % (str(datetime.now()), x))
                self.nl = False
            else:
                old_out.write(x)

        def flush(self):
            pass

    sys.stdout = St_ampe_dOut()

    #authentication
    creds = authentication()
    service = build('drive', 'v3', credentials=creds)

    #Get folders ID from arguments that user typed
    if p_folder != None and d_folder != None:
        p_folder_id = get_folder_id(service, 'root', p_folder, 'p')
        d_folder_id = get_folder_id(service, p_folder_id, d_folder, 'c')
        if p_folder_id == None:
            print('Parent folder not found, exiting...')
            
    elif p_folder == None and d_folder != None:
        print('Only destination directory defined: ' + d_folder)
        p_folder_id = 'root'
        d_folder_id = get_folder_id(service, 'root', d_folder, 'c')
#        print('Destination folder ID: ' + d_folder_id)
    elif p_folder == None and d_folder == None:
        print('No parent and destination folder are define, files will be upload to root')
        d_folder_id = 'root'
    else:
        print('Input not valid!')
    
    #Create folder if not exist
    if d_folder_id is None:
        print ('Destination folder not found!')
#        exit()
        Join = input('Would you like to create new folder? Type yes or y proceed, no or n to cancel and exit.\n')
        if Join.lower() == 'yes' or Join.lower() == 'y':
            print('Creating folder...')
            #exit()
            n_folder_id = create_folder(service, p_folder_id, d_folder)
            if n_folder_id != None:
                print('Folder ' + d_folder  + ' created, here is id: ' + n_folder_id)
                upload(service, src_folder_name, n_folder_id, d_folder)
                exit()
            else:
                print('Something definitely wrong while creating folder... Exiting...')
                exit()

        elif Join.lower() == 'no' or Join.lower() == 'n':
            print("You choosed to not create folder, exiting...")
        else:
            print('No Answer Given, abort...')
          
    
    if src_folder_name == None:
        print ('No local directory defined, exiting...')
        exit()
    
    if p_folder_id == None and d_folder_id == 'root':
        upload(service, src_folder_name, 'root', 'root')
    else:
        upload(service, src_folder_name, d_folder_id, d_folder)

if __name__ == "__main__":
    main()
