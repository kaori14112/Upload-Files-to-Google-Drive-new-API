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


def listToString(s):  
    
    # initialize an empty string 
    str1 = ""  
    
    # traverse in the string   
    for ele in s:  
        str1 += ele   
    
    # return string   
    return str1


def checkDir(dir):
    """
                Checking if given path is File or not
        """

    isFile = os.path.isfile(dir)
    return isFile


def checkPathex(path):
    """
                Checking if given path is exist or not
        """

    isExist = os.path.exists(path)
    return isExist


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


def checkPath(path):
    isEx = checkPathex(path)

    # Print error if source folder doesn't exist
    if isEx == False:
       print(path + 'File or Directory does not exist!')
       exit()
    else:
       # Determine if Path is File or Folder
       isFile = checkDir(path)
       return isFile


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
                   #if response is None and flag == 'p':
                   #   print ('Parent folder not found!')
                   #   return None
                      
               except googleapiclient.errors.HttpError as err:
                      #Parse error message
                      message = ast.literal_eval(err.content)['error']['message']

                      if message == 'File not found: ':
                         print(message + folder_name)
                         exit(1)
                      # Exit with stacktrace in case of other error
                      else:
                         raise

               for file in response.get('files', []):
               # Process change
               #    print(file)

                   if file['name'] == d_folder:
                      if flag == 'p':
                         print ("Parent Folder: " + file['name'] + " : " + file['id'])
                         #Comment 'break' and 'return' bellow if you want to print all folder as same name
                         return file['id']
                         break
                      elif flag == 'c':
                         print ("Destination Folder : " + file['name'] + " : " + file['id'])
                         #Comment 'break' and 'return' bellow if you want to print all folder as same name
                         return file['id']
                         break
                      else:
#                         print('No flag defined get folderID function, returning folder ID...')
                         return file['id']
                         break

               page_token = response.get('nextPageToken', None)

               if page_token is None:
                  break
#               return file['id']
#               break

    
def upload_file(service, file_dir, folder_id):
    """
                Upload files in the local folder to Google Drive
        """

    mime = magic.Magic(mime=True)        
    
    # Auto-iterate through all files in the folder.
    file1 = os.path.basename(file_dir)
#    print (src_folder_name)
    # Check the file's size
    statinfo = stat(file_dir)

    if statinfo.st_size > 0:
       
       print('uploading ' + file1 + '... ', end = '')

       #get mime types
#       file_dir = os.path.normpath(str(file_dir)) + os.sep

       mine_type = mime.from_file(file_dir)

       # Upload file to folder.
       media = MediaFileUpload(
               file_dir,
               mimetype=mine_type,
               resumable=True
       )

       request = service.files().create(
                 media_body=media,
                 body={'name': file1, 'parents': [folder_id]}
       )

       response = None

       while response is None:
             status, response = request.next_chunk()

             if status:
                print("... %d%%." % int(status.progress() * 100), end = '...')

       print("Complete!")


def upload_folder(service, path, parent_folder_id):
    try:
        chdir(path)
        # Print error if source folder doesn't exist
    except OSError:
        print(path + ' is missing, exiting...')
        return false
    
    arr = sort_dir(path)
    for name in arr:
        localpath = os.path.join(path, name)
#        print(localpath)
        
        if os.path.isfile(localpath):
           upload_file(service, localpath, parent_folder_id)
        elif os.path.isdir(localpath):
           print('\n')
           print('\x1b[6;30;42m' + 'Moving to another Folder...' + '\x1b[0m')
           FdID = get_folder_id(service, parent_folder_id, name, 'n')
		       
           if FdID is not None:
              print('\x1b[6;30;42m' + 'Folder "' + name + '" already exist on Google Drive, uploading files to ' + name  + '...' + '\x1b[0m')
              upload_folder(service, localpath, FdID)
           else:
              print('Folder "' + name + '" dont exist on Google Drive, creating...')
              n_FdID = create_folder(service, parent_folder_id, name)
    
              if n_FdID is not None:
                 print('Create Folder "' + name  + '" successfully, id: ' + n_FdID)
                 print('\x1b[6;30;42m' + 'uploading files to: ' + name + '\x1b[0m')
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
#    if p_folder_id:
#       file_metadata['parents'] = [{'id': n_p_folder_id}]
       
    file = service.files().create(body=file_metadata,
                                  fields='id').execute()
    return file.get('id')


def isdir(path, x):
    path = os.path.join(path, x)
    return os.path.isdir(path)


def sort_dir(path):
    arr = os.listdir(path)
    arr.sort(key=lambda x: (isdir(path, x), x))
    return arr
    

def main():
    
    #Variables
    args = parse_args()
    src_folder_name = args.source
    src_folder_name = os.path.normpath(str(src_folder_name)) + os.sep
#    print(src_folder_name)
    d_folder = args.destination
    p_folder = args.parent  
    
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
 
    #Functions
    creds = authentication()
    service = build('drive', 'v3', credentials=creds)
    p_folder_id = get_folder_id(service, 'root', p_folder, 'p')
    
    if p_folder_id is None:
       print ('Parent folder not found!')
       exit()
       
    d_folder_id = get_folder_id(service, p_folder_id, d_folder, 'c')
    
    if d_folder_id is None:
       print ('Destination folder not found!')
#       exit()
       Join = input('Would you like to create new folder? Type yes or y proceed, no or n to cancel and exit.\n')
       if Join.lower() == 'yes' or Join.lower() == 'y':
          print('Creating folder...')
          #exit()
          n_folder = create_folder(service, p_folder_id, d_folder)
          if n_folder is not None:
             print('Folder ' + d_folder  + ' created, here is id: ' + n_folder)
             print('\x1b[6;30;42m' + 'uploading files to: ' + d_folder  + '...' + '\x1b[0m')
             upload_folder(service, src_folder_name ,n_folder)
             exit()
          else:
             print('Something definitely wrong while creating folder... Exiting...')
             exit()
             
       elif Join.lower() == 'no' or Join.lower() == 'n':
          print("You choosed to not create folder, exiting...")
       else:
          print('No Answer Given, abort...')
       
    if src_folder_name == None:
       print ('No local directory defined, just print Parent and Destination folder if you pass those argurments')
       exit()
    else:
       chkPath = checkPath(src_folder_name)
       if chkPath == True:
          print ('\x1b[6;30;42m' + 'File detected, uploading: "' + d_folder + '" ...' + '\x1b[0m')
          upload_file(service, src_folder_name , d_folder_id)
          print('Complete uploaded file to drive folder: "' + d_folder + '" - FolderID: ' + d_folder_id)
       else:
          print ('\x1b[6;30;42m' + 'Folder detected, uploading to: "' + d_folder + '"' + '\x1b[0m')
          upload_folder(service, src_folder_name, d_folder_id)
          print('Complete uploaded folder to drive folder: "' + d_folder + '" - FolderID: ' + d_folder_id)


if __name__ == "__main__":
    main()
