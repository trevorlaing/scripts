"""UDP client sample: send a datagram and wait for a response.

Demonstrates basic UDP socket usage with sendto/recvfrom.
"""

import socket

target_host = "127.0.0.1"
target_port = 9997

# create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# send some data
client.sendto(b"Hello, Server!", (target_host, target_port))

# receive some data
data, addr = client.recvfrom(4096)

# Print the received payload and close the socket.
print(data.decode())
client.close()