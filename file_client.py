#! /usr/bin/env python3

"""
File transfer client. Connects to a server and sends one or more files
using a custom framing protocol.
"""

import socket
import sys
import os
from framing import FramedWriter
from buffers import BufferedWriter
from lib import params # This is a helper from the lib folder to parse command-line arguments.

def main():
    # --- 1. Parse Command-Line Arguments ---
    # Setup for the params library to handle arguments like -s for the server address.
    switchesVarDefaults = (
        (('-s', '--server'), 'server', "127.0.0.1:50001"),
        (('-?', '--usage'), "usage", False),
    )
    paramMap = params.parseParams(switchesVarDefaults)
    server, usage = paramMap["server"], paramMap["usage"]

    if usage or len(sys.argv) < 1:
        print("Usage: %s -s <server>:<port> <file1> [file2...]" % sys.argv[0])
        sys.exit(1)
    
    files_to_add = sys.argv
    
    try:
        serverHost, serverPort = server.split(":")
        serverPort = int(serverPort)
    except:
        print("Can't parse server:port from '%s'" % server)
        sys.exit(1)

    # --- 2. Connect to the Server ---
    # Use the code from the echoClient.py demo to establish a connection.
    try:
        # Create a new socket.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the server's address and port.
        s.connect((serverHost, serverPort))
    except Exception as e:
        print(f"Error connecting to server: {e}")
        sys.exit(1)

    print("Connected to server.")

    # --- 3. Send the Files ---
    # Get the socket's raw file descriptor.
    socket_fd = s.fileno()
    
    # Create an instance of our FramedWriter, telling it to write to the socket.
    # We must create the BufferedWriter first, then the FramedWriter.
    writer = FramedWriter(BufferedWriter(socket_fd))

    # Loop through each file provided on the command line.
    for filename in files_to_add:
        try:
            # Tell our writer to archive the file into the socket.
            writer.write_file(filename)
        except FileNotFoundError:
            os.write(2, f"Error: Input file '{filename}' not found.\n".encode())
    
    # Close the writer, which flushes the final buffer and closes the socket connection.
    writer.close()
    
    print("File transfer complete.")

if __name__ == "__main__":
    main()