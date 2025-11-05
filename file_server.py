#! /usr/bin/env python3
# Shebang line: Tells the OS to run this file using the python3 interpreter.

"""
File transfer server. Listens for a connection and receives one or more files
using a custom framing protocol.

This is the "Part 2" server: it uses os.fork() to handle multiple
clients concurrently.
"""

# --- Block 1: Imports and Setup ---
import socket 
import os
import time 
import sys
from framing import FramedReader   
from buffers import BufferedReader 
sys.path.append("lib")   
import params                

# --- NEW: Child Handler Function ---
# This function contains all the logic for a single client interaction.
# It will be run ONLY by a child process.
def handle_client(conn, addr):
    # 'conn' is the connection socket object specific to this client.
    # 'addr' is the client's (IP, port) information.
    print(f"Child (PID: {os.getpid()}): Handling connection from {addr}")
    try:
        # --- This is the core logic from your Part 1 server ---
        
        # 1. Get the raw file descriptor
        # We get the raw integer file descriptor (e.g., 5) from the socket object.
        # This is what os.read() (inside your buffer) needs to work.
        conn_fd = conn.fileno() 
        
        # 2. Build the abstraction layers
        # Create a BufferedReader that reads from the client's socket.
        # Then, create a FramedReader that reads from that BufferedReader.
        reader = FramedReader(BufferedReader(conn_fd)) 

        # 3. Use the abstraction to receive files
        # This loop will run as long as the client is sending files.
        # reader.read_next_file() returns True if it gets a file.
        # It returns False if it reads 0 bytes (client disconnected).
        while reader.read_next_file():
            pass # The read_next_file() method does all the work.
        
        # This line is reached when the client disconnects (read_next_file() returns False).
        print(f"Child (PID: {os.getpid()}): Finished with client {addr}")

    except Exception as e:
        # Catch any errors (e.g., client crashes, network drops)
        os.write(2, f"Child (PID: {os.getpid()}): Error: {e}\n".encode())
    finally:
        # 4. Clean up and EXIT the child process
        # This 'finally' block *always* runs, even if there was an error.
        conn.close() # Close the connection socket to this specific client.
        sys.exit(0)  # IMPORTANT: The child process's job is done. It *must* exit.

# The main function is run once by the original parent server.
def main():
    # --- Block 2: Command-Line Argument Parsing ---
    # Define the command-line flags this program accepts.
    switchesVarDefaults = (
        (('-l', '--listenPort') ,'listenPort', 50001), # -l flag, stores in 'listenPort', defaults to 50001
        (('-?', '--usage'), "usage", False),          # -? flag, stores in 'usage'
    )
    
    # Use the params.py script to parse sys.argv
    paramMap = params.parseParams(switchesVarDefaults)
    # Convert the port from a string (from params.py) to an integer
    listenPort = int(paramMap["listenPort"])
    # An empty string '' tells s.bind() to listen on all available interfaces (e.g., Wi-Fi, Ethernet) It's a special code that means "listen on ALL addresses this computer has."
    listenAddr = '' 

    # If the user passed '-?', print usage and exit.
    if paramMap["usage"]:
        print("Usage: %s -l <listen_port>" % sys.argv[0])
        sys.exit(1)
        
    # --- Block 3: Server Setup (Listening Socket) ---
    try:
        # 1. Create the main "welcome desk" socket 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # this empty socket that speaks ipv4 and tcp  
        # 2. This option prevents "Address already in use" errors if you restart the server
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)# Enable address reuse, 1 means "true" in case of crashes
        # 3. Set the socket to non-blocking.
        # s.accept() will now raise a 'socket.timeout' error after 5 seconds.
        # This is *ESSENTIAL* to allow the 'while True' loop to run and reap zombies.
        s.settimeout(5.0) # this makes accept non-blocking with 5 second timeout 
        # 4. Bind the socket to the port (claim port 50001 on this machine)
        s.bind((listenAddr, listenPort))
        # 5. Start listening for clients. The 5 is the "backlog,"
        #    meaning it can queue up 5 clients while the parent is busy forking.
        s.listen(5) 
        print(f"Server (PID: {os.getpid()}) listening on port {listenPort}...")
    except Exception as e:
        print(f"Error setting up server socket: {e}")
        sys.exit(1)

    # This dictionary is for the PARENT to keep track of its children.
    active_children = {}
        
    # --- Block 4: Main Server Loop (Accept, Fork, and Reap) ---
    # This loop runs forever. Its only jobs are to reap children and accept new clients.
    while True:
        # --- 4a. Reap Zombie Children (FIXED) ---
        # A "zombie" is a child process that has exited (sys.exit(0)) but hasn't
        # been "cleaned up" (waited on) by the parent. We must clean them up
        # or they will fill up the system's process table.
        try:
            # We loop because multiple children might have exited.
            while True: 
                # This is a *non-blocking* check for an exited child.
                # os.WNOHANG means "don't wait" if no children are done.
                waitResult = os.waitid(os.P_ALL, 0, os.WNOHANG | os.WEXITED) # os.p_all means "check all children", 0 means "any child", os.WNOHANG means "don't block", os.WEXITED means "only exited children"
                
                # --- THIS IS THE FIX ---
                # If os.waitid returns None, it means there are *no children at all*.
                if waitResult is None:
                    break # Stop checking.
                
                # If si_pid is 0, it means there *are* children, but none have exited/zombified yet. so we stop checking for now. 
                if waitResult.si_pid == 0:
                    break # Stop checking for now. get out of the while True loop. 
                
                # If we get here, a child has exited!
                zPid = waitResult.si_pid # Get the PID of the zombie child.
                if zPid in active_children:
                    print(f"Parent: Reaped zombie child (PID: {zPid})")
                    del active_children[zPid] # Remove it from our tracking dictionary.
                
        except ChildProcessError:
            pass # This happens if there are no child processes to wait for. It's fine.
        except Exception as e:
            print(f"Parent: Error reaping child: {e}")

        # --- 4b. Accept New Connections ---
        try:
            # This is a BLOCKING call, but it will only block for up to 5 seconds.
            conn, addr = s.accept() # Wait for a new client to connect. but only for 5 seconds because of the timeout set earlier 
        except socket.timeout:# if accept() times out (no client connects in 5 seconds) 
            # This is the *expected* error when no client connects.
            # We just 'continue' to the top of the 'while True' loop,
            # which lets us run the zombie-reaping code again.
            continue 
        except Exception as e:
            # This is a *real* error.
            print(f"Parent: Error accepting connection: {e}")
            continue # Go back to the top and try again.

        # If we get here, a new client has successfully connected.
        print(f"Parent: Accepted connection from {addr}")

        # --- 4c. Fork a New Child Process ---
        # This is the core of the concurrent server. The process splits in two.
        forkResult = os.fork()
        
        if forkResult == 0:
            # --- CHILD PROCESS CODE ---
            # forkResult == 0 means "I am the new child process."
            s.close() # The child does not need the main listening socket. only the parent needs it. the child needs the connection socket.
            handle_client(conn, addr) # Go do the work for this client. the conn is the connection socket specific to this client and
            # The child will call sys.exit(0) inside that function.
            
        else:
            # --- PARENT PROCESS CODE ---
            # forkResult > 0 means "I am the original parent process."
            # The 'forkResult' variable holds the new child's PID.
            conn.close() # The parent does not need the client *connection* socket.
            # Store the new child's PID so we can reap it later.
            active_children[forkResult] = addr
            print(f"Parent: Spawned child (PID: {forkResult}) to handle {addr}")
            print(f"Parent: Currently {len(active_children)} active clients")

# --- Block 5: Main Execution Guard ---
# This ensures that main() is only called when you run the script directly.
if __name__ == "__main__":
    main()