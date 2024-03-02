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
    
    ids = set()  # Use a set to store unique IDs
    for path in paths:
        match = uuid_regex.search(path)
        if match:
            ids.add(match.group())
    
    return ids



# -- Initialization -- 

#Add function to find APPID given name using find /private/var/containers -name "Progname*"
parser = argparse.ArgumentParser(description='Transfer specific app cache files from an iOS device to PC.')
parser.add_argument('-i', '--appid', required=False, help='AppID of the iOS application.')
parser.add_argument('-H', '--host', required=True, help='IP or hostname of jailbroken iOS device.')
parser.add_argument('-o', '--output', default='./', help='Local file path for storing the files (default is current directory).')
parser.add_argument('-v', '--version', action='store_true', help='Set output of tool to verbose to monitor file transfers.')
parser.add_argument('--find-app-id', required=False, help='Provide the name of the App to find the App\'s ID. Adding this parameter will cause the program to ignore the -i flag.')

args = parser.parse_args()
app_id_folder = f'/var/mobile/Containers/Data/Application/{args.appid}'
local_destination_folder = args.output
ios_ip = args.host
password = getpass.getpass("Enter SSH password: ")
verbose = args.version

host = ios_ip
port = 22
username = 'root' # Default for jailbroken devices





ssh = create_ssh_client(host, port, username, password)

if args.find_app_id:
    bundle_paths = find_bundle_path(ssh, args.find_app_id)
    unique_bundle_ids = extract_ids_from_paths(bundle_paths)
    if(unique_bundle_ids):
        print("\nFound potential Bundle IDs:")
        for id in unique_bundle_ids:
            print(id)
    else:
        print("NO apps found matching the provided name.")

    app_paths = find_app_paths(ssh, args.find_app_id)
    unique_ids = extract_ids_from_paths(app_paths)
    if(unique_ids):
        print("\nFound potential APP IDs:")
        for id in unique_ids:
            print(id)
    else:
        print("NO apps found matching the provided name.")
    ssh.close()
    exit()


found_Paths = find_files(ssh, app_id_folder)
if len(found_Paths) == 0:
    print("No .db or .sqlite files identified for the given AppID. Ensure that you are using the correct AppID from Objection (run env while Objection is attached to process)")
    ssh.close()
    exit()
move_files(ssh, found_Paths)
scp_files_to_pc(ssh, local_destination_folder)
cleanup_var_directory(ssh)

#scp_files_to_pc(ssh, '/scp/capable/location', local_destination_folder)
ssh.close()