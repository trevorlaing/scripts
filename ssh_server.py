"""Simple Paramiko-based SSH server example for testing and learning.

This script implements a minimal SSH server using Paramiko for
educational/demo purposes only.
"""

import os
import paramiko
import socket
import sys
import threading

CMD = os.path.dirname(os.path.realpath(__file__))
# Path to the server private key used for SSH host authentication.
HOSTKEY = paramiko.RSAKey(filename=os.path.join(CMD, 'test_rsa.key'))

class Server (paramiko.ServerInterface):
    def __init__(self):
        # Simple threading event used to coordinate auth/requests if needed.
        # Paramiko will call the ServerInterface methods from transport threads.
        self.event = threading.Event()
        
    def check_channel_request(self, kind, chanid):
        # Allow only 'session' channel requests (exec/shell).
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        # Any other channel kinds (e.g., x11, forwarded-tcpip) are rejected.
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_auth_password(self, username, password):
        # Very small example credential check. Do NOT use in production.
        if (username == 'tim') and (password == 'sekret'):
            return paramiko.AUTH_SUCCESSFUL
        # Any other credentials fail authentication.
        return paramiko.AUTH_FAILED
        
if __name__ == '__main__':
    server_host = '192.168.1.207'
    ssh_port = 2222
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((server_host, ssh_port))
        # Listen for a single incoming connection; this example accepts one client.
        sock.listen(100)
        print('[+] Listening for connection ...')
        client, addr = sock.accept()
    except Exception as e:
        print('[-] Listen failed: ' + str(e))
        sys.exit(1)
    else:
        # `client` is a socket object for the accepted connection.
        print('[+] Got a connection!', client, addr)
        
    # Wrap the socket in a Paramiko Transport to handle the SSH protocol.
    bhSession = paramiko.Transport(client)
    bhSession.add_server_key(HOSTKEY)
    server = Server()
    # Start the SSH server side; Paramiko will call our `Server` callbacks.
    bhSession.start_server(server=server)
    
    # Wait (timeout 20s) for the client to open a channel (e.g., exec/shell).
    chan = bhSession.accept(20)
    if chan is None:
        print('*** No channel.')
        sys.exit(1)
        
    print('[+] Authenticated!')
    # Print any initial banner/message from the client (if present).
    print(chan.recv(1024).decode())
    # Send a binary welcome message over the channel.
    chan.send(b'Welcome to bh_ssh')
    try:
        while True:
            # Read a command from local stdin and forward it to the remote.
            command = input("Enter command: ")
            if command != 'exit':
                # Encode to bytes before sending over SSH channel.
                chan.send(command.encode())
                r = chan.recv(8192)
                print(r.decode())
            else:
                chan.send(b'exit')
                print('exiting')
                bhSession.close()
                break
    except KeyboardInterrupt:
        bhSession.close()