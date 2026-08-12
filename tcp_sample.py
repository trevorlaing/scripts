"""TCP client sample: connect to a host and fetch a simple HTTP response.

Minimal example showing how to create a TCP socket, send an HTTP
request, and print the response.
"""

import socket

target_host = "www.google.com"
target_port = 80

# create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
client.connect((target_host, target_port))

# send some data
client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")
# receive some data (this example reads a single chunk)
response = client.recv(4096)

# Print the HTTP response (decoded from bytes).
print(response.decode())
client.close()