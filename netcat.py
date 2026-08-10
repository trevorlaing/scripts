# Simple netcat-like tool supporting:
#   - connect/send mode
#   - listen mode with command shell
#   - one-shot execute mode
#   - file upload mode
#
# Usage examples are available in the argparse epilog below.
import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

# Run a shell command and return the decoded output.
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    return output.decode()

class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        # Create a TCP socket and allow address reuse.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        # Decide whether to listen as a server or connect as a client.
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def send(self):
        # Connect to the remote target and optionally send initial input.
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)
        try:
            while True:
                recv_len = 1
                response = ''
                # Read from the remote socket until no more data arrives.
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    if not recv_len:
                        break
                    response += data.decode()
                    if recv_len < 4096:
                        break
                if response:
                    print(response, end='')
                    buffer = input('> ')
                    buffer += '\n'
                    self.socket.send(buffer.encode())
                else:
                    break
        except KeyboardInterrupt:
            print('User terminated.')
        finally:
            self.socket.close()
            sys.exit()

    def listen(self):
        # Bind to the local address and wait for incoming client connections.
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        try:
            while True:
                client_socket, _ = self.socket.accept()
                client_thread = threading.Thread(target=self.handle, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print('Shutting down.')
        finally:
            self.socket.close()
            sys.exit()

    def handle(self, client_socket):
        # Handle a connected client based on the selected mode.
        if self.args.execute:
            output = execute(self.args.execute)
            if output:
                client_socket.send(output.encode())
            client_socket.close()
        elif self.args.upload:
            # Receive a file upload and save it locally.
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                file_buffer += data

            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())
            client_socket.close()

        elif self.args.command:
            # Provide an interactive command shell to the client.
            cmd_buffer = b''
            try:
                while True:
                    client_socket.send(b'BHP: #> ')
                    while b'\n' not in cmd_buffer:
                        data = client_socket.recv(64)
                        if not data:
                            client_socket.close()
                            return
                        cmd_buffer += data

                    command = cmd_buffer.decode().strip()
                    cmd_buffer = b''
                    if not command:
                        continue
                    if command.lower() in ('exit', 'quit'):
                        client_socket.send(b'Bye!\n')
                        client_socket.close()
                        return

                    response = execute(command)
                    if response:
                        client_socket.send(response.encode())
            except Exception as e:
                print(f'Server killed {e}')
                client_socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Example:
            netcat.py -t 192.168.1.1 -p 5555 -l -c # command shell
            netcat.py -t 192.168.1.1 -p 5555 -l -u=mytest.txt # upload to file
            netcat.py -t 192.168.1.1 -p 5555 -l -e=\"cat /etc/passwd\" # execute command
            echo  'ABC' | ./netcat.py -t 192.168.1.1 -p 135 # echo text to server port 135
            netcat.py -t 192.168.1.1 -p 5555 # connect to server
        '''))
    parser.add_argument('-c', '--command', action='store_true', help='command shell')
    parser.add_argument('-e', '--execute', help='execute specified command')
    parser.add_argument('-l', '--listen', action='store_true', help='listen')
    parser.add_argument('-p', '--port', type=int, default=5555, help='specified port')
    parser.add_argument('-t', '--target', default='192.168.1.203', help='specified IP')
    parser.add_argument('-u', '--upload', help='upload file')
    args = parser.parse_args()
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()

    nc = NetCat(args, buffer.encode())
    nc.run()   