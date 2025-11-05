#! /usr/bin/env python3

"""
File transfer client. Connects to a server and sends one or more files
using a custom framing protocol.
"""

# --- Block 1: Imports and Setup ---
import socket  
import sys     
import os    
from framing import FramedWriter   
from buffers import BufferedWriter 
sys.path.append("lib")  
import params       

def main():
    # --- Block 2: Command-Line Argument Parsing ---
    
    # Define the command-line flags this program accepts.
    switchesVarDefaults = (
        # (flags, variable_name, default_value)
        (('-s', '--server'), 'server', "127.0.0.1:50001"), # -s flag, stores in 'server'
        (('-?', '--usage'), "usage", False),          # -? (help) flag, stores in 'usage'
    )
    
    # Run the "smarter" params.py parser on the command-line args (sys.argv)
    paramMap = params.parseParams(switchesVarDefaults)
    
    # Get the server address from the parser results (e.g., "127.0.0.1:50000")
    server_address = paramMap["server"]
    
    # Get the list of "positional" arguments (filenames) that params.py collected
    files_to_add = paramMap["positionalArgs"] 

    # Check for errors:
    # 1. Did the user ask for help ('-?')
    # 2. Did the user forget to provide any filenames?
    if paramMap["usage"] or not files_to_add:
        # If either is true, print the correct usage and exit.
        print("Usage: %s -s <server>:<port> <file1> [file2...]" % sys.argv[0])
        sys.exit(1) # Exit with an error code
    
    # Try to split the server address (e.g., "127.0.0.1:50000") into host and port
    try:
        serverHost, serverPort = server_address.split(":") # Splits at the ":"
        serverPort = int(serverPort) # Converts the port string "50000" to a number
    except:
        # If split() or int() fails, the format was wrong.
        os.write(2, f"Error: Can't parse server:port from '{server_address}'\n".encode())
        sys.exit(1)

    # --- Block 3: Connect to the Server ---
    
    # This 'try' block catches network errors (e.g., "Connection refused")
    try:
        # 1. Ask the OS for a new, empty socket "plug"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # 2. Tell the socket to connect to the server's address.
        # This is a "blocking call" - the program pauses here until
        # the connection is made or it fails.
        s.connect((serverHost, serverPort))
    except Exception as e:
        # 'e' holds the error message (e.g., "Connection refused")
        os.write(2, f"Error connecting to server: {e}\n".encode())
        sys.exit(1)

    print(f"Connected to server at {server_address}.")

    # --- Block 4: Send the Files ---
    
    # 1. Get the raw OS file descriptor (a number) for our new socket 's'.
    # This is the "pipe" that our BufferedWriter will write to.
    socket_fd = s.fileno()
    
    # 2. Build our abstraction layers, from the bottom up:
    #    - BufferedWriter(socket_fd): Creates a writer that reliably writes
    #      bytes to the network socket.
    #    - FramedWriter(...): Creates our file-packaging tool and tells it
    #      to use the BufferedWriter as its destination.
    writer = FramedWriter(BufferedWriter(socket_fd)) 

    print(f"Sending files: {', '.join(files_to_add)}")
    
    # 3. Loop through the "to-do list" (shopping list) of filenames
    for filename in files_to_add:
        try:
            # 4. Tell the FramedWriter to do its job on this one file.
            # This is where the magic happens:
            # - FramedWriter opens the file, gets its size, and creates the 108-byte header.
            # - FramedWriter writes the header to the BufferedWriter.
            # - FramedWriter reads the file's data and writes it to the BufferedWriter.
            # - The BufferedWriter sends all those bytes over the network.
            writer.write_file(filename)
        except FileNotFoundError:
            # Catch error if the user typed a bad filename
            os.write(2, f"Error: Input file '{filename}' not found.\n".encode())
    
    # 5. We are done sending all files.
    # This calls writer.close() -> BufferedWriter.close() -> os.close(socket_fd).
    # This flushes any remaining data in the buffer and closes the
    # socket, which is the "hang up" signal that tells the server we're done.
    writer.close()
    
    print("File transfer complete.")

# --- Block 5: Main Execution Guard ---
# This is a standard Python check:
# "Is this script being run directly?" (vs. being imported by another script)
if __name__ == "__main__":
    main() # If yes, run the main function.