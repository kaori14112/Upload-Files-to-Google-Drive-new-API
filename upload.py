from __future__ import print_function
import pickle
import os.path
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.errors

# Import general libraries
from argparse import ArgumentParser
from os import chdir, listdir, stat
from sys import exit
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


def get_folder_id(drive_service, parent_folder_id, d_folder, flag):
    """
                Check if destination folder exists and return it's ID
        """
    page_token = None
    if parent_folder_id == 'None':
       print ('Subfolder not found')
       return None
    else: 
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
                         print(message + folder_name)
                         exit(1)
                      # Exit with stacktrace in case of other error
                      else:
                          raise

               for file in response.get('files', []):
               # Process change
#                   print(file)

                   if file['name'] == d_folder:
                      if flag == 'p':
                         print ("Parent Folder: " + file['name'] + " : " + file['id'])
                         return file['id']
                         break
                      else:
                         print ("Destination Folder : " + file['name'] + " : " + file['id'])
                         return file['id']
                         break

               page_token = response.get('nextPageToken', None)

               if page_token is None:
                  break
#               return file['id']
#               break
    
def upload_file(service, src_folder_name, folder_id):
    """
                Upload files in the local folder to Google Drive
        """
    try:
        chdir(src_folder_name)
        # Print error if source folder doesn't exist
    except OSError:
           print(src_folder_name + 'is missing')
    # Auto-iterate through all files in the folder.
    mime = magic.Magic(mime=True)        
   
    for file1 in listdir('.'):
        # Check the file's size
        statinfo = stat(file1)
        if statinfo.st_size > 0:
           print('uploading ' + file1)

           #get mime types
           mine_type = mime.from_file(src_folder_name + file1) # 'application/pdf'

           # Upload file to folder.
           media = MediaFileUpload(
                   src_folder_name + file1,
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
                    print("Uploaded %d%%." % int(status.progress() * 100))
           print("Upload Complete!")


def main():

    args = parse_args()
    src_folder_name = args.source
    d_folder = args.destination
    p_folder = args.parent
    creds = authentication()
    service = build('drive', 'v3', credentials=creds)
    p_folder_id = get_folder_id(service, 'root', p_folder, 'p')
    d_folder_id = get_folder_id(service, p_folder_id, d_folder, 'c')
    
    if src_folder_name == None:
       print ('No local directory defined, just print Parent and Destination folder if you pass those argurments')
    else:
       upload_file(service, src_folder_name, d_folder_id)
    print('Complete uploaded to folder id: ' + d_folder_id)

if __name__ == "__main__":
    main()
