# Python networking scripts (learning / demo)

This repository contains a collection of small networking examples and
learning scripts demonstrating raw TCP/UDP sockets, a simple netcat-like
tool, an FTP/TCP proxy that rewrites passive-mode replies, and basic
Paramiko-based SSH client/server helpers.

Files of interest
- `tcp_sample.py` — minimal TCP client that fetches an HTTP response.
- `udp_sample.py` — minimal UDP client example.
- `multi_tcp.py` — small multi-threaded TCP server that acknowledges data.
- `netcat.py` — netcat-like tool with listen, upload, execute, and command-shell modes.
- `proxy.py` — TCP proxy with optional FTP PASV/EPSV response rewriting.
- `ssh_cmd.py` — simple Paramiko-based SSH command runner (client-side).
- `ssh_rcmd.py` — remote-command helper that executes commands received over SSH.
- `ssh_server.py` — minimal Paramiko SSH server example (educational only).
- rforward.py

Dependencies
- Python 3.8+ (tested with 3.11)
- `paramiko` for SSH examples: install with `pip install paramiko`

Quick start

1. Check syntax for all scripts:

```bash
python -m py_compile *.py
```

2. Run `tcp_sample.py` or `udp_sample.py` to experiment with basic sockets:

```bash
python tcp_sample.py
python udp_sample.py
```

3. `netcat.py` usage examples are included in the script epilog — run
	 it for interactive testing. For example, to listen with a command shell:

```bash
python netcat.py -t 0.0.0.0 -p 5555 -l -c
```

4. `proxy.py` can be used to proxy an FTP control connection and rewrite
	 PASV/EPSV responses so passive data flows through the proxy. See the
	 script header for usage examples.

Security / disclaimers
- These scripts are educational examples. Do not run servers with these
	examples exposed to untrusted networks or use them with production keys.
- The SSH server uses a static `test_rsa.key` in the script directory —
	generate your own key and protect it appropriately.

If you want, I can add more inline documentation, usage tests, or create
examples showing how to run each script locally.