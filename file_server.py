#! /usr/bin/env python3
# Shebang line: Tells the OS to run this file using the python3 interpreter.

"""
File transfer server. Listens for a connection and receives one or more files
using a custom framing protocol.

This is the THREADED version. It uses standard Python threading to handle 
multiple clients concurrently.
"""

# --- Block 1: Imports and Setup ---
import socket  # Provides networking tools (socket(), bind(), listen(), accept())
import sys     # Used for sys.exit() and sys.path
import os      # Provides OS-level functions like fileno()
import threading # <--- NEW: The library for creating and managing threads
from framing import FramedReader   # Your custom tool to unpack 108-byte headers
from buffers import BufferedReader # Your custom tool for reliable os.read() calls
sys.path.append("lib")       # Adds 'lib' folder to Python's search path
import params                # Your teacher's helper script for parsing command-line args

# --- NEW: Thread Handler Function ---
# This function is the "worker" for each thread. It runs concurrently
# with the main server loop and other client threads.
def handle_client(conn, addr):
    # 'conn' is the connection socket object specific to this client.
    # 'addr' is the client's (IP, port) information.
    # threading.get_ident() gives us the unique ID of the current thread for logging.
    print(f"Thread (ID: {threading.get_ident()}): Handling connection from {addr}")
    try:
        # 1. Get the raw file descriptor
        # We need the raw integer 'pipe' number for our low-level buffers.
        conn_fd = conn.fileno()
        
        # 2. Build the abstraction layers
        # Create a BufferedReader to read reliably from the socket pipe.
        # Pass that to a FramedReader that understands our file format.
        reader = FramedReader(BufferedReader(conn_fd))

        # 3. Use the abstraction to receive files
        # The loop continues as long as the client is sending files.
        # It returns False when the client disconnects (sends 0 bytes).
        while reader.read_next_file():
            pass # The read_next_file() method does all the actual work.
        
        # We reach here only when the client has successfully disconnected.
        print(f"Thread (ID: {threading.get_ident()}): Finished with client {addr}")

    except Exception as e:
        # If something breaks (like a sudden network drop), we catch it here.
        # We use os.write(2, ...) because it's safer than print() when multiple 
        # threads might try to write to the screen at the exact same time.
        os.write(2, f"Thread Error: {e}\n".encode())
    finally:
        # 4. Clean up THIS client's connection.
        # This is critical. It closes the socket for this specific client.
        conn.close() 
        # Unlike the fork version, we DO NOT call sys.exit(0) here.
        # When this function returns, the thread automatically disappears.

# The main function is run by the primary (parent) thread.
def main():
    # --- Block 2: Command-Line Argument Parsing ---
    # Define valid flags: -l for port (default 50001), -? for help.
    switchesVarDefaults = (
        (('-l', '--listenPort') ,'listenPort', 50001),
        (('-?', '--usage'), "usage", False),
    )
    # Parse the arguments using the helper library.
    paramMap = params.parseParams(switchesVarDefaults)
    listenPort = int(paramMap["listenPort"])
    listenAddr = '' # Listen on all available network interfaces (Wi-Fi, Ethernet, etc.)

    # If the user asked for help (-?), print usage and quit.
    if paramMap["usage"]:
        print("Usage: %s -l <listen_port>" % sys.argv[0])
        sys.exit(1)

    # --- Block 3: Server Setup (Listening Socket) ---
    try:
        # 1. Create the main "welcome desk" socket (IPv4, TCP)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 2. Allow immediate reuse of the port if the server crashes and restarts.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 3. Bind our "welcome desk" to the specific port (e.g., 50001).
        s.bind((listenAddr, listenPort))
        # 4. Start listening. Allow up to 5 clients to wait in line if we're busy.
        s.listen(5)
        print(f"Threaded Server listening on port {listenPort}...")
    except Exception as e:
        print(f"Error setting up server socket: {e}")
        sys.exit(1)

    # --- Block 4: Main Server Loop ---
    # Notice how much simpler this is than the forking version!
    # No zombie reaping is needed because threads clean up after themselves.
    while True:
        try:
            # 1. Wait for a new client.
            # This is a BLOCKING call. The main thread sleeps here until a client connects.
            # We don't need a timeout because we don't need to wake up to reap zombies.
            conn, addr = s.accept()
            print(f"Main: Accepted connection from {addr}")

            # 2. Create a new Thread to handle this client.
            # target=handle_client: Tells the thread what function to run.
            # args=(conn, addr): Passes the connection socket and address to that function.
            t = threading.Thread(target=handle_client, args=(conn, addr))
            
            # 3. Set the thread as a "daemon".
            # This means if you kill the main server (Ctrl+C), these threads 
            # will automatically die too, instead of keeping your terminal stuck.
            t.daemon = True 
            
            # 4. Start the thread!
            # The new thread immediately jumps to the 'handle_client' function,
            # while this main thread immediately continues to the next line.
            t.start()
            
            # The loop finishes and instantly goes back to the top to 's.accept()' 
            # waiting for the next client, while the thread is busy working.

        except KeyboardInterrupt:
            # This handles Ctrl+C gracefully.
            print("\nServer stopping...")
            break
        except Exception as e:
            # Catch any other unexpected errors so the server doesn't crash.
            print(f"Main: Error accepting connection: {e}")

# --- Block 5: Main Execution Guard ---
if __name__ == "__main__":
    main()