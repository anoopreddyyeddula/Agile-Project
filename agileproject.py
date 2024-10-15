# Import required modules
import os
import posixpath, time 
import pysftp
import signal
import logging
import datetime, paramiko
import getpass
from stat import S_ISDIR

# Set up logging
logfile = 'sftp_log.txt'
logging.basicConfig(filename=logfile,level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

sftpconnection = None

# Define a list of available commands
Commands = ["1. help (prints command)", 
           "2. listdirectory (list files on remote directory)", 
           "3. getfile (download a file)",
           "4. bye-bye (logouts from server)",
           "5. getfiles (download multiple files)",
           "6. listlocal (list local directory)" ,
           "7. putfile (upload a file)" ,
           "8. putfiles (upload multiple files)" ,
           "9. createdirectory (Create a directory on remote server)",
           "10. deletefile (delete a file on server)",
           "11. changepermission (change file permissions on server)",           
           "12. copyremote (copy directories on server)",
           "13. deletedirectory (delete directory from server)",  
           "14. renameremote (rename file on server)",
           "15. renamelocal (rename file on local machine)" ,      
           "16. changedirectory (change directory)",
           "17. cdlocal (change directory in local)" ]

# Define a function to initiate the connection  
def initiate_connection(hostname,username,password):
    try:
        print(f"Connceting to: {hostname}")
        logging.info("Connecting to the host")
        sftpconnection = pysftp.Connection(host=hostname,username=username,password=password)
        save_connection(hostname,username,password) 
        print("Connected successfully", sftpconnection)       
        logging.info(f'Connected Successfully to SFTP Server') 
        sftpconnection.cwd(f'/u/{username}')      
        CommandConfig(sftpconnection)  
    except Exception as e:
        print("Connection Error. Please connect again.")
        logging.info(f'Connection Error. Please connect again')
        print("\n Exiting....")
        exit()


    
# Define a function to configure commands   
def CommandConfig(sftpconnection):
        global login_user, working_dir
        ShowChoice()
        sftpconnection.cwd('Downloads/Agile')                  
        print(f"Directory you are working with :{sftpconnection.pwd}")
        print("\n")        
        CommandCentral(sftpconnection)     

# Define a function to handle commands
def CommandCentral(sftpconnection):
    while(True):
        print("Select your preference (Command):")
        preference = input()
        if preference.lower() == "help":
            logging.info(f'User selected help command')
            ShowChoice()
            
        elif preference.lower() == "listdirectory": 
            logging.info(f'User selected list directory to list all file and folder')
            for info in sftpconnection.listdir_attr(remotepath='.'):
                print(info)
                
        elif preference.lower() == "getfile": 
            logging.info(f'User selected get file to download a file from remote server to local server')
            print("Please provide the name of a file, including its extension, located in the current directory.")
            fname = input()
            if sftpconnection.isfile(fname):
                print(f"Downloading {fname} file from current directory")
                if os.path.isfile('./'+fname) and os.path.exists('./'+fname):
                    print('File already exists')
                else:
                    if get_file(fname,sftpconnection):                                                
                        print("Download completed successfully")
                    else:
                        print("Download unsuccessful. \n Attempting automatic retry")
                        if get_file(fname):
                            print("Download completed successfully")
                        else:
                            print("Download unsuccessful once more.\n Please retry after a brief interval")
                            continue
            else:
                print(f"The entered filename does not exist.\n Please make sure to enter a valid filename and try again.")
                
        
        elif preference.lower() == "bye-bye": 
            logging.info(f'User logged out of the server')
            print("Are you sure you want to log out?(yes/no)")
            logout = input()
            if logout == 'yes':
                sftpconnection.close()
                return
            elif logout == 'no':
                continue
            
        
        elif preference.lower() == "getfiles":
            logging.info(f'User selected multiple file command to download files')
            print("Please list the file names from the current directory, separated by commas (,)")                
            files = input()
            fileslist = files.split(',')                
            for i in fileslist:               
                if sftpconnection.isfile(i) and sftpconnection.exists(i):
                    print(f"Downloading file:{i} from current directory")                    
                    if get_file(i,sftpconnection):
                        print("Download completed successfully")
                    else:
                        print("The download was unsuccessful.")
                        continue
                else:
                    print(f"The entered fname does not exist.\n Please make sure to enter a valid filename and try again.")
                    
        elif preference.lower() == "listlocal": 
            logging.info(f'User selected list local machine directory')
            print("Displaying a list of files and folders in the current directory")
            for paths in os.scandir(os.getcwd()): 
                print(paths.name)
            
        elif preference.lower() == "putfile":
            logging.info(f'User selected upload file from local to remote server')
            print("Please provide the file path within the local directory:")
            fpath = input()
            if os.path.isdir(fpath): 
                print("Please provide the filname located in the specified directory:")
                fname = input()
                if put_file(fpath,fname,sftpconnection):
                    print("Upload successful")
                else:
                    print("File upload failed.")
                    continue
                
        elif preference.lower() == "putfiles":
            logging.info(f'User selected multiple files to the server')
            print("Please list the file names from the current directory, separated by commas (,)")
            files = input()
            fpath = '.'
            filesnames = files.split(',')             
            for i in filesnames:                     
                if put_files(fpath, i, sftpconnection):
                    print("upload successfully")
                else:
                    print("upload failed")
                    
        elif preference.lower() == "createdirectory":
            logging.info(f'User selected create directory on remote server')
            print("Please provide the desired name for the directory you wish to create:")
            newdir = input() 
            if sftpconnection.isdir(newdir) and sftpconnection.exists(newdir):
                print("The directory name you entered already exists. Please provide a different name and try again")                
            else:
                print(f"Initiating the creation of a new directory with the following name: {newdir}")
                sftpconnection.mkdir(newdir,mode=777)
                
                if sftpconnection.exists(newdir):
                    print(f"Successfully created a new directory with the name: {newdir} successfully")
                    for info in sftpconnection.listdir_attr(remotepath='.'):
                        print(info)
                else:
                    print(f"An error occurred during the creation process. Please try again. {newdir}")
                    
        elif preference.lower() == "deletefile":
            print("Please provide the filename you wish to delete from the server:")
            logging.info(f'User selected delete files on remote server')
            delfname = input()
            
            if sftpconnection.isfile(delfname) and sftpconnection.exists(delfname):
                print("Initiating the deletion of the specified file...")
                sftpconnection.remove(delfname)
                if sftpconnection.exists(delfname):
                    print("File deletion failed. Please attempt the operation again.")
                else:
                    print("File successfully deleted.")
            else:
                print(f"The file name you entered does not exist")     
                
        elif preference.lower() == "changepermission":
            logging.info(f'User selected Permissions on the remote server')
            print("Please provide the filename or foldername for which you wish to modify permissions:")
            userpermission = 7
            grouppermission = 7
            otherpermission = 7
            filepermissions = input()
                      
            if sftpconnection.isfile(filepermissions) or sftpconnection.isdir(filepermissions) and sftpconnection.exists(filepermissions):
                    print("Configure user permissions for the file/folder by responding to the following questions. \n Note: By default, permissions are set to read, write, and execute")
                    
                    print("Would you like the user to have read permissions? y/n")
                    uread = input().lower()
                    if uread == 'y':
                        userpermission = 4
                    elif uread == 'n':
                        userpermission = 0
                    
                    print("Would you like the user to have write permissions? y/n")
                    uwrite = input().lower()
                    
                    if uwrite == 'y':
                        userpermission = userpermission + 2
                    elif uwrite == 'n':
                        userpermission = userpermission + 0
                        
                    print("Would you like the user to have execute permissions? y/n")
                    uexecute = input().lower()
                    if uexecute == 'y':
                        userpermission = userpermission + 1
                    elif uexecute == 'n':
                        userpermission =userpermission + 0
                    
                    print(f"user permission chmod {filepermissions} is {userpermission}")
                    
                    print("Configure group permissions for the file by responding to the following questions. \n Note: By default, permissions are set to read, write, and execute.")
                    
                    print("Would you like the user to have read permissions? y/n")
                    
                    gread=input().lower()
                    if gread == 'y':
                        grouppermission = 4 
                    elif gread == 'n':
                        grouppermission = 0
                    
                    print("Would you like the user to have write permissions? y/n")
                    gwrite = input().lower()
                    
                    if gwrite == 'y':
                        grouppermission = grouppermission + 2
                    elif gwrite == 'n':
                        grouppermission = grouppermission + 0
                        
                    print("Would you like the user to have execute permissions? y/n")
                    gexecute = input().lower()
                    if gexecute == 'y':
                        grouppermission = grouppermission + 1
                    elif gexecute == 'n':
                        grouppermission =grouppermission + 0
                        
                        
                    print("Configure permissions for others on the file by responding to the following questions.\n Note: By default, permissions are set to read, write, and execute.")
                    
                    print("Would you like the user to have read permissions? y/n")
                    oread =input().lower()
                    if oread == 'y':
                        otherpermission = 4
                    elif oread == 'n':
                        otherpermission = 0
                    
                    print("Would you like the user to have write permissions? y/n")
                    owrite = input().lower()
                    
                    if owrite == 'y':
                        otherpermission = otherpermission + 2
                    elif owrite == 'n':
                        otherpermission = otherpermission + 0
                        
                    print("Would you like the user to have execute permissions? y/n")
                    oexecute = input().lower()
                    if oexecute == 'y':
                        otherpermission = otherpermission + 1
                    elif oexecute == 'n':
                        otherpermission =otherpermission + 0
                        
                    print("Applying the specified permissions to the file...")
                    
                    changingpermission = int(str(userpermission)+str(grouppermission)+str(otherpermission))#assign(str(userpermission),str(grouppermission), str(otherpermission))
                    
                    print(changingpermission, type(changingpermission))
                    try:
                        sftpconnection.chmod(filepermissions, changingpermission)
                        print("File permissions have been successfully updated.")
                    except IOError as e:
                        print("An error occurred while assigning permissions. Please verify if the file/folder still exists on the server.")
                        continue
            else:
                
                print(" The file/folder name you enetered does not exist. Please try again")  
                
        elif preference.lower() == "copyremote": 
            print("Please provide the directory you wish to copy:")
            remotesrc= input()
            if sftpconnection.isdir(remotesrc):
                print("Please specify the destination directory for the copy:")
                remotedest= input()
                
                if sftpconnection.exists(remotedest):
                    print(f"The directory you entered already exists. Please provide a different name or location")
                else:
                    print(f"Copy the directory {remotesrc} to {remotedest}")
                    
                    comm = 'cp -R'+' '+remotesrc + ' ' +remotedest 
                    try:
                        print(sftpconnection.execute(comm))
                    
                    except Exception as e:
                        print(f"An error occurred while copying directories. {e} \n Please Try again")
                        continue
            else:
                print("The specified directory does not exist.")
        
        elif preference.lower() == "deletedirectory":
            print("Please provide the name of the directory you want to delete from the server:")
            logging.info(f'User selected delete directory on remote server')
            deldir = input()
            level=0            
            if sftpconnection.exists(deldir) and sftpconnection.isdir(deldir):
                print("Initiating the deletion of the specified directory...")
                for contents in sftpconnection.listdir_attr(deldir):
                    rempath = posixpath.join(deldir, contents.fname)
                    if S_ISDIR(contents.st_mode):
                        print('\n')
                        #rmtree(sftpconnection, rempath, level=(level + 1))
                    else:
                        rempath = posixpath.join(deldir, contents.fname)
                        print('removing %s%s' % ('    ' * level, rempath))
                        sftpconnection.remove(rempath)
                sftpconnection.rmdir(deldir)
                if sftpconnection.exists(deldir):
                    print("Folder deletion failed. Please try the operation again")
                else:
                    print("Directory successfully deleted.")
            else:
                print(f"The directory name you entered does not exist")
                
        elif preference.lower() == 'renameremote':
            logging.info(f'Rename of the remote file is done')
            print("Please provide the filename you wish to rename on the server:")
            renrfname= input() 
            if sftpconnection.isfile(renrfname) and sftpconnection.exists(renrfname):                
                print("Please enter the new name you would like for the file:")
                newrenrfname= input()
                if sftpconnection.isfile(newrenrfname) and sftpconnection.exists(newrenrfname):
                    print("The new filename you entered already exists. Please choose a different name")
                else:
                    sftpconnection.rename(renrfname, newrenrfname) 
                    if sftpconnection.isfile(newrenrfname) and sftpconnection.exists(newrenrfname):
                        print(" Renamed successfully") 
                    else:
                        print("File renaming was unsuccessful. Please attempt the operation again.")
            else:
                print("The fname you entered does not exist.")       
                
        elif preference.lower() == "renamelocal":
            logging.info(f'User has used renames fname on the local machine on the current directory command')
            print("Please provide the filename you wish to rename on the local machine:")
            renlfname= input()
            if os.path.isfile(renlfname) and os.path.exists(renlfname):
                print("Please enter the new name you would like for the file:")
                newrenlfname= input()
                if os.path.isfile(newrenlfname) and os.path.exists(newrenlfname):
                    print("The new fname you entered already exists. Please choose a different name.")
                else:
                    os.rename(renlfname, newrenlfname)
                    if os.path.isfile(newrenlfname) and os.path.exists(newrenlfname):
                        print("Renamed successfully") 
                    else:
                        print("Rename unsuccessful. Please try again")
            else:
                print("The fname you entered does not exist.")
                                            
        elif preference.lower() == "changedirectory": 
            logging.info(f'User selected change directory on remote server')
            print("Please enter the name of the directory:")
            working_dir = input()
            print(working_dir)
            try:    
                if sftpconnection.isdir(working_dir):
                    sftpconnection.cwd(working_dir)
                    print(f'Current working directory is {sftpconnection.pwd}')
                else:
                    print("The directory name you entered is incorrect. Please provide the correct name and try again.")
            except Exception as e:
                print("An error occurred while attempting to change the directory",e)
        
        elif preference.lower() == "cdlocal": 
            logging.info(f'User selected cdlocal to change the user directory on local')
            print("Please enter the name of the directory:")
            working_dir = input()
            print(working_dir)
            try:    
                if os.path.isdir(working_dir):
                    os.chdir(working_dir)
                    cwd = os.getcwd()
                    print("Current working directory is:", cwd)
                else:
                    print("The directory name you entered is incorrect. Please provide the correct name and try again")
            except Exception as e:
                print("An error occurred while attempting to change the directory: ",e)

# Define a function to save connection information                   
def save_connection(hostname,username,password):
    while(True):
        if os.path.isfile("saveconnection.log"):
            savefile = os.path.join(os.getcwd(),"saveconnection.log")
            save = open(savefile, "a")
            save.write("\nConnection succesful\n")
            save.write(f"host:{hostname}\n")
            save.write(f"username:{username}\n")
            save.write(f"password:{password}\n")
            break
        else:
            save=open("saveconnection.log", "x")
            continue

# Define a function to use saved connection information
def usesave_connection(num):
    if os.path.exists("saveconnection.log"):
        savefile = os.path.join(os.getcwd(),"saveconnection.log")
        save = open(savefile, "r")
        credlines= save.readlines()
        credline=credlines[-num:]
        credi = dict(cred.rstrip("\n").split(':') for cred in credline)
        hostname=credi.get("host")
        username=credi.get("username")
        password=credi.get("password")
        
        return hostname,username,password 
    else: 
        print("No previous connection information available.")
        credentials()

# Define a function to input new connection credentials
def credentials():
    print("Please enter the FTP server name:")
    hostname = input()
    print("Please enter your username:")
    username = input()
    print("Please enter your password :")
    password = getpass.getpass(stream=None)
    
    return hostname,username,password 

# Define a function to handle user connection request
def user_request():
    if os.path.exists("saveconnection.log"):
        print("Do you want to use your previously saved login information?(yes/no)")
        descision=input()
        if descision == 'yes':
            response=usesave_connection(3)
            print(f"Saved credentials: {response[0]},{response[1]}")
            initiate_connection(response[0],response[1],response[2])
            logging.info(f'Logged in with the save connection log file')
        else:
            credos=credentials()
            initiate_connection(credos[0],credos[1],credos[2])
    else:
        credos=credentials()
        initiate_connection(credos[0],credos[1],credos[2])


# Define a function to handle signals (e.g., CTRL+C)
def signal_handle(signum, frame):
    print("You wished to close the client by pressing CTRL+c. \n Until next time")
    exit()

signal.signal(signal.SIGINT, signal_handle)

# Define a function to show available commands
def ShowChoice():
        print("Please select command from below")
        for command in Commands:
            print(command)
        print("\n")

# Define a function to download a single file
def get_file(filename,sftpconnection):    
        try:
            sftpconnection.get(filename, preserve_mtime=True)
        except IOError as e:
            return False
        except OSError as e:
            return False        
        if os.path.exists('./'+filename):
            return True
        else:
            return False
                
# Define a function to upload a single file
def put_file(filepath,filename,sftpconnection):  
    filepathserver = sftpconnection.pwd 
    try:
        sftpconnection.put(filepath+"/"+filename,confirm=True, preserve_mtime=False)
    except IOError as e:
        return False
    except OSError as e:
        return False
        
    if sftpconnection.exists(filepathserver+"/"+filename):
        return True
    else:
        return False

# Define a function to upload multiple files
def put_files(filepath, i, sftpconnection): 
    if os.path.isfile(i) and os.path.exists(i):
        print(f"Uploading file:{i}")
        if put_file(filepath,i,sftpconnection):
            return True
        else:
            return False       
    else:
        print(f"Filename you entered does not exists.\n Please try again")
           

# Main program starts here
if __name__ == "__main__":
    try:
        user_request()
    except Exception as e:
        error_message = f"An error occurred: {str(e)}. Please try again."
        print(error_message)
        logging.error(error_message)
        print("\nExiting...")
        exit()