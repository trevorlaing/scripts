# Simple TCP proxy with optional FTP PASV/EPSV response rewriting.
# Useful for learning how control and data channels interact.
import sys
import re
import socket
import threading
import select

# Mapping of bytes to printable characters for hex dump output.
HEX_FILTER = ''.join(
    [(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)])
    
def hexdump(src, length=16, show=True):
    if isinstance(src, bytes):
        src = src.decode('utf-8', errors='replace')
    
    results = list()
    for i in range(0, len(src), length):
        word = str(src[i:i+length])
        
        printable = word.translate(HEX_FILTER)
        hexa = ' '.join([f'{ord(c):02x}' for c in word])
        hexwidth = length*3
        results.append(f'{i:04x} {hexa:<{hexwidth}} {printable}')
    if show:
        for line in results:
            print(line)
    else:
        return results

def receive_from(connection):
    # Read all available data from a socket until it times out.
    buffer = b''
    connection.settimeout(60)
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except Exception as e:
        pass
    return buffer

def request_handler(buffer):
    # Modify outgoing packets from client to server if needed.
    return buffer

def response_handler(buffer, local_host, remote_host):
    # Rewrite FTP passive-mode responses so the client connects through us.
    if buffer.startswith(b'227'):
        return rewrite_pasv_response(buffer, local_host)
    if buffer.startswith(b'229'):
        return rewrite_epsv_response(buffer, local_host, remote_host)
    return buffer

def rewrite_pasv_response(buffer, local_host):
    match = re.search(rb'\((\d{1,3}(?:,\d{1,3}){5})\)', buffer)
    if not match:
        return buffer

    parts = match.group(1).split(b',')
    remote_data_host = '.'.join(p.decode() for p in parts[:4])
    remote_data_port = int(parts[-2]) * 256 + int(parts[-1])

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((local_host, 0))
    listener.listen(1)
    local_port = listener.getsockname()[1]

    start_ftp_data_proxy(listener, remote_data_host, remote_data_port)

    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', local_host):
        local_host = '127.0.0.1'

    local_ip_parts = [int(x) for x in local_host.split('.')]
    p1 = local_port // 256
    p2 = local_port % 256
    new_addr = b','.join(str(part).encode() for part in local_ip_parts)
    return re.sub(rb'\(\d{1,3}(?:,\d{1,3}){5}\)', b'(' + new_addr + b',' + str(p1).encode() + b',' + str(p2).encode() + b')', buffer)

def rewrite_epsv_response(buffer, local_host, remote_host):
    match = re.search(rb'\(\|\|\|(\d+)\|\)', buffer)
    if not match:
        return buffer

    remote_data_port = int(match.group(1))
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((local_host, 0))
    listener.listen(1)
    local_port = listener.getsockname()[1]

    start_ftp_data_proxy(listener, remote_host, remote_data_port)
    return re.sub(rb'\(\|\|\|(\d+)\|\)', f'(|||{local_port}|)'.encode(), buffer)

def start_ftp_data_proxy(listener, remote_host, remote_port):
    def data_proxy():
        try:
            local_data_socket, addr = listener.accept()
            print(f'[*] Accepted FTP data connection from {addr[0]}:{addr[1]}')
            proxy_data_connection(local_data_socket, remote_host, remote_port)
        except Exception as e:
            print(f'FTP data proxy failed: {e}')
        finally:
            listener.close()

    thread = threading.Thread(target=data_proxy, daemon=True)
    thread.start()

def proxy_data_connection(local_data_socket, remote_host, remote_port):
    remote_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_data_socket.connect((remote_host, remote_port))

    try:
        while True:
            readable, _, _ = select.select([local_data_socket, remote_data_socket], [], [], 0.5)
            if local_data_socket in readable:
                data = local_data_socket.recv(4096)
                if not data:
                    break
                remote_data_socket.sendall(data)
            if remote_data_socket in readable:
                data = remote_data_socket.recv(4096)
                if not data:
                    break
                local_data_socket.sendall(data)
    finally:
        local_data_socket.close()
        remote_data_socket.close()
        print('[*] FTP data proxy closed.')

def proxy_handler(client_socket, remote_host, remote_port, receive_first, local_host):
    # Handle one client connection and proxy data to the remote host.
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    remote_buffer = b''
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

    # Send it to our response handler
    local_response_host = local_host
    if local_response_host == '0.0.0.0':
        local_response_host = client_socket.getsockname()[0]
    remote_buffer = response_handler(remote_buffer, local_response_host, remote_host)

    # If we have data to send to our local client, send it
    if len(remote_buffer):
        print(f'[<==] Sending {len(remote_buffer)} bytes to localhost.')
        client_socket.sendall(remote_buffer)

    # Now loop and forward data between local client and remote host.
    while True:
        readable, _, _ = select.select([client_socket, remote_socket], [], [], 0.5)

        if client_socket in readable:
            local_buffer = client_socket.recv(4096)
            if not local_buffer:
                print('[*] Local connection closed.')
                client_socket.close()
                remote_socket.close()
                break

            print(f'[==>] Received {len(local_buffer)} bytes from localhost.')
            hexdump(local_buffer)
            local_buffer = request_handler(local_buffer)
            remote_socket.sendall(local_buffer)
            print(f'[==>] Sent {len(local_buffer)} bytes to remote.')

        if remote_socket in readable:
            remote_buffer = remote_socket.recv(4096)
            if not remote_buffer:
                print('[*] Remote connection closed.')
                client_socket.close()
                remote_socket.close()
                break

            print(f'[<==] Received {len(remote_buffer)} bytes from remote.')
            hexdump(remote_buffer)
            remote_buffer = response_handler(remote_buffer, local_response_host, remote_host)
            client_socket.sendall(remote_buffer)
            print(f'[<==] Sent {len(remote_buffer)} bytes to localhost.')

def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((local_host, local_port))
    except Exception as e:
        print(f'Failed to listen on {local_host}:{local_port}')
        print(f'Check for other listening sockets or correct permissions.')
        sys.exit(0)

    print(f'Listening on {local_host}:{local_port}')

    server.listen(5)

    while True:
        # Accept a new incoming connection
        client_socket, addr = server.accept()
        print(f'Accepted connection from {addr[0]}:{addr[1]}')

        # Start a thread to talk to the remote host
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remote_host, remote_port, receive_first, local_host)
        )
        proxy_thread.start()

def main():
    if len(sys.argv[1:]) != 5:
        print('Usage: ./proxy.py [localhost] [localport] [remotehost] [remoteport] [receive_first]')
        print('Example: ./proxy.py 127.0.0.1 8080 10.10.10.1 80 True')
        sys.exit(0)

    local_host = sys.argv[1]
    local_port = int(sys.argv[2])
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])
    receive_first = sys.argv[5].lower() == 'true'

    server_loop(local_host, local_port, remote_host, remote_port, receive_first)

if __name__ == '__main__':
    main()