# Simple SSH command runner using Paramiko.
#
# Usage:
#   python ssh_cmd.py
#
# The script prompts for username/password and SSH server details.
import paramiko

def ssh_command(ip, port, user, passwd, cmd):
    # Connect to an SSH server and run a single command.
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=passwd)
    
    _, stdout, stderr = client.exec_command(cmd)
    output = stdout.readlines() + stderr.readlines()
    if output:
        print('--- Output ---')
        for line in output:
            print(line.strip())
            
if __name__ == '__main__':
    import getpass
    # user = getpass.getuser()
    user = input('Username: ')
    password = getpass.getpass()
    
    # Prompt for server details; provide sensible defaults.
    ip = input('Enter server IP: ') or '192.168.1.203'
    port_input = input('Enter port or <CR>: ')
    # Convert the entered port to an integer before passing to Paramiko.
    port = int(port_input) if port_input else 2222
    cmd = input('Enter command or <CR>: ') or 'id'
    ssh_command(ip, port, user, password, cmd)
