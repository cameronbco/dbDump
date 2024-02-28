import paramiko
from scp import SCPClient
import os
import argparse
import getpass

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


#Add function to find APPID given name using find /private/var/containers -name "Progname*"
parser = argparse.ArgumentParser(description='Transfer specific app cache files from an iOS device to PC.')
parser.add_argument('-i', '--appid', required=True, help='AppID of the iOS application.')
parser.add_argument('-H', '--host', required=True, help='IP or hostname of jailbroken iOS device.')
parser.add_argument('-o', '--output', default='./DUMP', help='Local file path for storing the files (default is current directory).')
parser.add_argument('-v', '--version', action='store_true', help='Set output of tool to verbose to monitor file transfers.')
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