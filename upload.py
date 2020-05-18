from __future__ import print_function
from functions import *


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
