#! /usr/bin/env python3

# Echo client program
import socket, sys, re, os
sys.path.append("../lib")       # for params
import params 

switchesVarDefaults = (
    # command line switches, variable name, default value
    #These are the command-line flags. It means the user can type either -s or --server.
    # "127.0.0.1:50001" This is the default value. If the user doesn't provide a -s flag, the variable 'server' will automatically get this value.
    (('-s', '--server'), 'server', "127.0.0.1:50001"),
    (('-?', '--usage'), "usage", False), # boolean (set if present) -? flag that controls a boolean variable named usage
    )


progname = "framedClient"
paramMap = params.parseParams(switchesVarDefaults) #his is the function from your teacher's library. It does all the hard work of reading the command line (sys.argv), understanding the flags based on the rules you defined, and returning the results.
#The results are returned as a dictionary. It might look like this: {'server': 'localhost:50002', 'usage': False}.

#pull the values out of the paramMap dictionary and put them into local variables that are easier to use.
server, usage  = paramMap["server"], paramMap["usage"] #The variable server now holds the server address string.The variable usage now holds True or False.

if usage:#If the user provided the -? flag, or if they didn't provide enough arguments, print a usage message and exit.
    params.usage()#This is a function from your teacher's library that prints out the usage message based on the switchesVarDefaults you defined earlier.

#takes the server address string and splits it into the host and the port.
try:
    serverHost, serverPort = re.split(":", server)#This uses a regular expression to split the string at the colon into two parts. The first part is the hostname or IP address, and the second part is the port number.
    serverPort = int(serverPort)# This converts the serverPort string (e.g., "50001") into an integer number so it can be used by the socket functions.
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)

#/////////////////////////////////////////////////////////////////////////////////////////////////////////////////
s = None # This is a flag. After the loop is finished, we can check if s is None: to see if we failed to connect. If it's still None, it means none of our connection attempts worked
# Try each of the possible addresses until one works.This is a powerful helper function, not a direct system call. Its job is to figure out all the possible ways to connect to a given server.

# serverHost, serverPort: The destination address. socket.AF_UNSPEC: A flag that means "Address Family Unspecified." This tells getaddrinfo to find both IPv4 (AF_INET) and IPv6 (AF_INET6) addresses for the server.
# socket.SOCK_STREAM: This specifies that we want TCP (stream-oriented) sockets, as opposed to UDP (datagram-oriented) sockets.
# The function returns a list of tuples, each describing a possible way to connect to the server.
# Each tuple contains (address family, socket type, protocol, canonical name, socket address).
# We loop through each of these tuples, trying to create a socket and connect to the server
for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
    #af: The Address Family (e.g., AF_INET for IPv4).
    #socktype: The Socket Type (e.g., SOCK_STREAM for TCP).
    #proto: The Protocol (usually 0).
    #sa: The Socket Address. This is the fully prepared address structure (like the sockaddr_in we read about) that the connect() call needs.
    af, socktype, proto, canonname, sa = res
    # Create a new socket.
    try:
        print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
        s = socket.socket(af, socktype, proto)#This is the actual system call that creates a new socket. It uses the address family, socket type, and protocol from the current tuple to create a socket that can connect to the server.
    except socket.error as msg:#If the socket creation fails (for example, if the system runs out of file descriptors), it catches the exception, prints an error message, and sets s back to None to indicate failure.
        print(" error: %s" % msg)
        s = None# Set s to None to indicate failure
        continue# Try the next address
    try:# Try to connect to the server using the created socket and the socket address from the tuple.
        print(" attempting to connect to %s" % repr(sa))
        s.connect(sa)# This is the actual system call that attempts to connect the socket to the server address.
    except socket.error as msg:# If the connection attempt fails (for example, if the server is unreachable), it catches the exception, prints an error message, closes the socket to free up resources, sets s back to None, and continues to the next address.
        print(" error: %s" % msg)
        s.close()# Close the socket to free up resources
        s = None# Set s to None to indicate failure
        continue# Try the next addressg
    break

if s is None:# didnt connect to any address 
    print('could not open socket')
    sys.exit(1)# Exit the program with an error code 
#/////////////////////////////////////////////////////////////////////////////////////////

outMessage = "Hello world!".encode()# this is the data to be sent 
while len(outMessage):# while there is still data to send 
    print("sending '%s'" % outMessage.decode())#% s is a placeholder for a string value. The % operator is used to format the string by replacing the placeholder with the actual value of outMessage.decode().
    bytesSent = os.write(s.fileno(), outMessage)# s.fileno() gets the file descriptor (an integer) associated with the socket s. os.write writes the bytes in outMessage to the file descriptor, which sends them over the network through the socket.
    outMessage = outMessage[bytesSent:]# This updates outMessage to remove the bytes that were successfully sent. If only part of the message was sent, this ensures that the remaining part will be sent in the next iteration of the loop.

# Now read back the echoed data from the server 
data = os.read(s.fileno(), 1024).decode()#It is a blocking call, meaning your program will pause here until it receives data from the server.
print("Received '%s'" % data)# print the received data 

# Another way to do the same thing using socket methods instead of os methods 
outMessage = "Hello world!".encode()
while len(outMessage):
    print("sending '%s'" % outMessage.decode())
    bytesSent = s.send(outMessage)
    outMessage = outMessage[bytesSent:]

#reads from the server until the server closes the connection.
s.shutdown(socket.SHUT_WR)      # alert connected socket that no more data will be sent but still can receive data 

while 1:
    data = s.recv(1024).decode()#  This is the high-level equivalent of os.read. It waits for and receives data from the server.
    print("Received '%s'" % data)
    if len(data) == 0: # When recv() returns 0 bytes, it is the network equivalent of an End-of-File (EOF). This signals that the conversation is over, and the break command exits the loop.
        break
print("Zero length read.  Closing")

s.close()# Close the socket file descriptor s.send and s.recv are higher-level socket methods that internally use the lower-level os.write and os.read system calls to perform the actual data transmission over the network.