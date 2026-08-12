"""Simple multi-threaded TCP server that acknowledes received data.

Accepts multiple connections and responds with a short ACK message.
"""

import socket
import threading

IP = '0.0.0.0'
PORT = 9998

def main():
    # create a socket object
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IP, PORT))
    server.listen(5)
    # Start listening for incoming connections on the configured port.
    print(f"[*] Listening on {IP}:{PORT}")

    while True:
        # Accept and hand off the client socket to a worker thread.
        client, address = server.accept()
        print(f"[*] Accepted connection from {address[0]}:{address[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()

def handle_client(client_socket):
    # Use the socket as a context manager so it's closed automatically.
    with client_socket as sock:
        request = sock.recv(1024)
        # Decode bytes for logging; this may raise if non-UTF8 but is fine for examples.
        print(f"[*] Received: {request.decode('utf-8')}")
        # Simple acknowledgement response.
        sock.send(b"ACK")

if __name__ == "__main__":
    main()
