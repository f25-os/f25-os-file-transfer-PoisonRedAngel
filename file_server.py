#! /usr/bin/env python3

"""
File transfer server. Listens for a connection and receives one or more files
using a custom framing protocol.

This is the "Part 1" server: it handles one client at a time, sequentially.
"""

# --- Block 1: Imports and Setup ---
import socket
import sys
import os

from framing import FramedReader 
from buffers import BufferedReader
sys.path.append("lib")       # for params
import params 

def main():
    # --- Block 2: Command-Line Argument Parsing ---
    # Setup for the params library, modeled on echoServer.py
    switchesVarDefaults = (
        (('-l', '--listenPort') ,'listenPort', 50001), # -l for listen port
        (('-?', '--usage'), "usage", False),
    )
    
    paramMap = params.parseParams(switchesVarDefaults)
    listenPort = int(paramMap["listenPort"]) # Convert port to integer
    listenAddr = ''       # Symbolic name meaning all available interfaces

    if paramMap["usage"]:
        print("Usage: %s -l <listen_port>" % sys.argv[0])
        sys.exit(1)
        
    # --- Block 3: Server Setup (Listening Socket) ---
    # This is the "welcome desk" socket. Its only job is to wait for
    # new clients to arrive, not to talk to them.
    
    try:
        # 1. Create the main socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # This line allows the server to re-use the port immediately
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # 2. Bind the socket to the port
        s.bind((listenAddr, listenPort))
        
        # 3. Listen for incoming connections
        s.listen(1) # Allow one connection to queue up
        print(f"Server listening on port {listenPort}...")
    except Exception as e:
        print(f"Error setting up server socket: {e}")
        sys.exit(1)
        
    # --- Block 4: Main Server Loop (Accepting & Handling Clients) ---
    # This loop waits for a client, handles all their files, 
    # closes the connection, and then loops back to wait for the next client.
    while True:
        print("Waiting for a new client connection...")
        # 4. Accept a new connection
        # This is a BLOCKING call. The program stops here until a client connects.
        # 'conn' is the NEW socket for talking to this specific client.
        # 'addr' is the client's IP address and port.
        conn, addr = s.accept()
        print(f"Accepted connection from {addr}")

        # Use try/finally to ensure the connection is *always* closed
        try:
            # --- Block 4a: The Core Logic (Receiving Files) ---
            
            # 1. Get the raw file descriptor from the new connection socket
            conn_fd = conn.fileno()
            
            # 2. Build the abstraction layers, just like the client but in reverse.
            #    We pass the 'conn_fd' to the BufferedReader.
            reader = FramedReader(BufferedReader(conn_fd))
    
            # 3. Use the abstraction.
            #    Loop as long as the reader can find new files in the stream.
            #    The FramedReader's read_next_file() returns False when
            #    it reads 0 bytes, signaling an EOF from the client.
            while reader.read_next_file():
                pass # The read_next_file() method does all the work
            
            print(f"Client {addr} finished sending files.")

        except Exception as e:
            # Handle any network errors or framing errors
            os.write(2, f"An error occurred with client {addr}: {e}\n".encode())
        finally:
            # 4. Clean up the connection.
            #    The reader.close() will close the BufferedReader, which closes conn_fd.
            #    We also close the high-level 'conn' object to be safe.
            print(f"Closing connection from {addr}.")
            conn.close() 

if __name__ == "__main__":
    main()