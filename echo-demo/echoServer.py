#! /usr/bin/env python3

# Echo server program

import socket, sys, re, time
sys.path.append("../lib")       # for params
import params

#--------------setup to determine which port to listen on ----------

switchesVarDefaults = (
    (('-l', '--listenPort') ,'listenPort', 50001),
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )


progname = "echoserver"
paramMap = params.parseParams(switchesVarDefaults)

listenPort = paramMap['listenPort']
listenAddr = ''       # Symbolic name meaning all available interfacesThis is a key detail. 
#By setting the listen address to an empty string, you are telling the socket to bind to all available network interfaces on the computer (e.g., both the Wi-Fi and the wired Ethernet)

if paramMap['usage']: # If the user provided the -? flag, print usage and exit.
    params.usage()
#--------------this creates a listerning socket that waits for clients to connect ----------------
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # This is the socket() system call. It creates the server's main socket. AF_INET specifies IPv4, and SOCK_STREAM specifies TCP.
print(f"server listening at ip addr {listenAddr} port #{listenPort}")# This prints out a message indicating where the server is listening for connections.
s.bind((listenAddr, listenPort))# This is the bind() system call. It assigns the socket to the specified address and port, so the OS knows to direct incoming connection requests for that address/port to this socket.
s.listen(1) # allow only one outstanding request This is the listen() system call. It converts the socket from an active socket to a passive "listening" socket that can accept incoming connections. The 1 means it will allow one connection to wait in the queue.
# s is a factory for connected sockets

conn, addr = s.accept()  # wait until incoming connection request (and accept it)
#conn is a new socket object usable to send and receive data on the connection
#addr is the address bound to the socket on the other end of the connection the clinets ip and port number 
print('Connected by', addr)
#Now that a connection is established (on the conn socket), 

#--------- this loop handles the server's job: read data, process it, and send a response.----
while 1:
    data = conn.recv(1024).decode()
    if len(data) == 0:# EOF from client if the client closes its sending side of the connection, the server's recv() call will return zero bytes, indicating EOF.
        print("Zero length read, nothing to send, terminating")
        break
    sendMsg = ("Echoing %s" % data).encode()# This is the "echo" logic. It takes the data it just received, adds "Echoing " to the front, and encodes it back into bytes to be sent.
    print("Received '%s', sending '%s'" % (data, sendMsg.decode())) # print what was received and what will be sent
    while len(sendMsg):# while there is still data to send
        bytesSent = conn.send(sendMsg)# send as much as possible
        sendMsg = sendMsg[bytesSent:0]# update to remove sent bytes 
conn.shutdown(socket.SHUT_WR)   # indicate that the stream is complete
print("socket shut down for writing, waiting 3s for socket to drain...")
time.sleep(3)
print("    ...closing socket")
conn.close() 

