import paramiko
from scp import SCPClient
import os
import argparse
import getpass
import re
from collections import defaultdict

def create_ssh_client(host, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=username, password=password)
    return ssh

def find_files(ssh, app_id_folder):
    find_command = f'find {app_id_folder} -name "*.sqlite" -or -name "*.db"'
    

    # Example command to move files - adjust as needed
    stdin, stdout, stderr = ssh.exec_command(find_command)
    file_paths = stdout.read().decode('utf-8').strip().split('\n')
    if(Plist):
        find_command = f'find {app_id_folder} -name "*.plist"'
        stdin, stdout, stderr = ssh.exec_command(find_command)
        plist_paths = stdout.read().decode('utf-8').strip().split('\n')
        file_paths.extend(plist_paths)
    return file_paths

def move_files(ssh, file_paths, target_folder='/var/dumpDatabasesFolder'):
    makeFolder_command = f"mkdir {target_folder}"
    stdin, stdout, stderr = ssh.exec_command(makeFolder_command)
    folder_creation_output = stdout.read() + stderr.read()  # Capture output
    for file_path in file_paths:
        if file_path:  # Ensure the file path is not empty
            if(verbose == True):
                print("Moving: ", file_path)
            move_command = f"cp '{file_path}' {target_folder}"
            stdin, stdout, stderr = ssh.exec_command(move_command)
            output = stdout.read() + stderr.read()  # Capture output


def scp_files_to_pc(ssh,destination_folder, source_folder='/var/dumpDatabasesFolder'):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    with SCPClient(ssh.get_transport()) as scp:
        scp.get(source_folder, local_path=destination_folder, recursive=True)

def cleanup_var_directory(ssh):
    # Be VERY careful with this command; it deletes files!
    cleanup_command = "rm -r /var/dumpDatabasesFolder"
    stdin, stdout, stderr = ssh.exec_command(cleanup_command)
    output = stdout.read() + stderr.read()  # Capture both stdout and stderr

def find_bundle_path(ssh, app_name):
    # Define the paths to search
    search_paths = [
        '/private/var/containers/Bundle/Application'
    ]
    
    found_paths = []  # Initialize an empty list to collect found paths
    
    # Iterate over each path and execute the find command
    for path in search_paths:
        # Use -iname for case-insensitive search of directories that include the specified app_name
        find_command = f'find {path} -type d -iname "*{app_name}*.app"'
        stdin, stdout, stderr = ssh.exec_command(find_command)
        # Read and decode the output, then split into lines
        paths = stdout.read().decode('utf-8').strip().split('\n')
        # Filter out empty strings and extend the found_paths list with paths that are not empty
        found_paths.extend([p for p in paths if p])
    
    return found_paths

def find_app_paths(ssh, app_name):
    # Define the paths to search
    search_paths = [
        #'/private/var/containers',
        '/private/var/mobile/Containers/Data/Application'
    ]
    
    found_paths = []  # Initialize an empty list to collect found paths
    
    # Iterate over each path and execute the find command
    for path in search_paths:
        find_command = f'find {path} -name "{app_name}*"'
        stdin, stdout, stderr = ssh.exec_command(find_command)
        # Read and decode the output, then split into lines
        paths = stdout.read().decode('utf-8').strip().split('\n')
        # Filter out empty strings and extend the found_paths list
        found_paths.extend([p for p in paths if p])
    
    return found_paths

def extract_ids_from_paths(paths):
    # Regular expression to match the UUID format
    uuid_regex = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
    
    ids_paths = {}  # Use a dictionary to store unique ID-path pairs
    for path in paths:
        match = uuid_regex.search(path)
        if match:
            uuid = match.group()
            # Only store the path if the ID has not been encountered before
            if uuid not in ids_paths:
                ids_paths[uuid] = path
    
    return ids_paths

'''def dumpPlist(appID):
    print("test")

def beginDump(pathName, appName):
    print(pathName)
    command = f'cp -r {pathName} /var/Payload'
    return 0


def extract_ipa_from_name(appName):
    filePath = '/var/containers/Bundle/Application'
    findCommand = f"find {filePath} -type d -iname '*{appName}*.app' -print"
    stdin, stdout, stderr = ssh.exec_command(findCommand)
    output = stdout.read().decode('utf-8').strip().split('\n')
    error = stderr.read().decode('utf-8').strip()
    if error:
        print("Error:", error)
        return
    
    if len(output) == 1:
        # Only one path found
        print("Found app path:", output[0])
    num_paths = len(output)
    if num_paths == 1 and output[0]:  # Checking output[0] to ensure it's not an empty string
        print("Found app path:", output[0])
        return output[0]
    elif num_paths > 1:
        print("Found multiple file paths, please choose one:\n")
        for i, path in enumerate(output):
            print(f"{i}: {path}")
        
        while True:
            try:
                selection = int(input("Enter the number corresponding to the desired path: "))
                if 0 <= selection < num_paths:
                    chosen_path = output[selection]
                    print("You selected:", chosen_path, "\nBeginning dump...")
                    beginDump(chosen_path, appName)
                    return 1
                else:
                    print("Invalid selection. Please select a number listed above.")
            except ValueError:
                print("Please enter the number cooresponding to the correct found path.")
    else:
        print("No paths found matching the criteria.")
'''
# -- Initialization -- 

#Add function to find APPID given name using find /private/var/containers -name "Progname*"
parser = argparse.ArgumentParser(description='Transfer specific app cache files from an iOS device to PC.')
parser.add_argument('-i', '--appid', required=False, help='AppID of the iOS application.')
parser.add_argument('-H', '--host', required=True, help='IP or hostname of jailbroken iOS device.')
parser.add_argument('-o', '--output', default='./', help='Local file path for storing the files (default is current directory).')
parser.add_argument('-v', '--verbose', action='store_true', help='Set output of tool to verbose to monitor file transfers.')
parser.add_argument('--find-app-id', required=False, help='Provide the name of the App to find the App\'s ID. Adding this parameter will cause the program to ignore the -i flag.')
# Functionality to add.
parser.add_argument('-P', '--Plist',action='store_true', help='Dumps Plist files along with DB and SQLITE folders.')
'''
parser.add_argument('--extract-by-name', required=False, help='Provide the appname, attempts to pull the .IPA file from the jailbroken device')
parser.add_argument('--extract-by-bundle-id', required=False, help='Provide the appname, attempts to pull the .IPA file from the jailbroken device')
'''
args = parser.parse_args()
app_id_folder = f'/var/mobile/Containers/Data/Application/{args.appid}'
local_destination_folder = args.output
ios_ip = args.host
password = getpass.getpass("Enter SSH password: ")
verbose = args.verbose
Plist = args.Plist
host = ios_ip
port = 22
username = 'root' # Default for jailbroken devices

ssh = create_ssh_client(host, port, username, password)

#extract_ipa_from_name(args.extract_by_name)

if args.find_app_id:
    bundle_paths = find_bundle_path(ssh, args.find_app_id)
    unique_bundle_ids = extract_ids_from_paths(bundle_paths)
    if unique_bundle_ids:
        print("\nFound potential Bundle IDs and their paths:")
        for id, path in unique_bundle_ids.items():
            print(f"ID: {id}\n\tPath: {path}")
    else:
        print("No app bundles found matching the provided name.")

    app_paths = find_app_paths(ssh, args.find_app_id)
    unique_ids = extract_ids_from_paths(app_paths)
    if(unique_ids):
        print("\nFound potential APP IDs:")
        for id, path in unique_ids.items():
            print(f"ID: {id}\n\tPath: {path}")
    else:
        print("NO apps found matching the provided name.")
        exit(0)
    ssh.close()
    exit(1)



if not args.appid:
   print("The AppID is required in this instance!")
   exit(0)
else:
    found_Paths = find_files(ssh, app_id_folder)
    if len(found_Paths) == 0:
        print("No .db or .sqlite files identified for the given AppID. Ensure that you are using the correct AppID from Objection (run env while Objection is attached to process)")
        ssh.close()
        exit()
    move_files(ssh, found_Paths)
    scp_files_to_pc(ssh, local_destination_folder)
    cleanup_var_directory(ssh)
    exit(1)

#scp_files_to_pc(ssh, '/scp/capable/location', local_destination_folder)
ssh.close()
exit(0)