import socket

target_host = "127.0.0.1"
target_port = 8080

# create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# send some data
client.sendto(b"Hello, Server!", (target_host, target_port))

# receive some data
response, server_address = client.recvfrom(4096)
print(response.decode())
client.close()   