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
# We no longer need to import 'params' or change the sys.path

def main():
    # --- 1. Parse Command-Line Arguments Manually ---
    server_address = "127.0.0.1:50001"  # Default server
    files_to_add = []
    
    # Manually loop through arguments
    args = sys.argv[1:]  # Get all arguments except the script name
    i = 0
    while i < len(args):
        arg = args[i]
        # Check for the -s or --server flag
        if arg == '-s' or arg == '--server':
            # Check if there's a value *after* the flag
            if i + 1 < len(args):
                server_address = args[i+1]
                i += 2  # Skip both the flag and its value
            else:
                os.write(2, b"Error: -s flag requires an argument\n")
                sys.exit(1)
        # Check for the usage flag
        elif arg == '-?' or arg == '--usage':
            print("Usage: %s -s <server>:<port> <file1> [file2...]" % sys.argv[0])
            sys.exit(1)
        # If it's not a flag, it must be a filename
        else:
            files_to_add.append(arg)
            i += 1

    # Now, check if we actually got any filenames
    if not files_to_add:
        os.write(2, b"Error: No files specified for transfer.\n")
        print("Usage: %s -s <server>:<port> <file1> [file2...]" % sys.argv[0])
        sys.exit(1)
    
    # Try to parse the server address
    try:
        serverHost, serverPort = server_address.split(":")
        serverPort = int(serverPort)
    except:
        os.write(2, f"Error: Can't parse server:port from '{server_address}'\n".encode())
        sys.exit(1)

    # --- 2. Connect to the Server ---
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((serverHost, serverPort))
    except Exception as e:
        os.write(2, f"Error connecting to server: {e}\n".encode())
        sys.exit(1)

    print(f"Connected to server at {server_address}.")

    # --- 3. Send the Files ---
    socket_fd = s.fileno()
    
    # We must create the BufferedWriter first, then the FramedWriter.
    # Assumes FramedWriter was modified to accept a buffer object
    writer = FramedWriter(BufferedWriter(socket_fd)) 

    print(f"Sending files: {', '.join(files_to_add)}")
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