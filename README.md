# nets-tcp-framing

# nets-tcp-file-transfer

For this lab, you must define a file transfer protocol and implement a
client and server.  

Part 1:
* File transfer client and server that utilizes the techniques implemented by your archiver you previously constructed.
* To teat its framing, this client and server should function correctly when the client's connection is forwarded by the stammering proxy described below.

Part 2:
* Modify the server to support multiple concurrent clients. 
* If you are enrolled in the "advanced operating systems" course, your server should be single-threaded and utilize select().


The following code should be helpful for your project

Directory `echo-demo` includes a simple tcp echo server & client

Directory `fork-demo` includes a simple tcp program with a server that forks

Directory `lib` includes the params package required for many of the programs

Directory `stammer-proxy` includes stammerProxy, which is useful for demonstrating and testing framing.  By default stammerProxy listens on port 50000 and forwards to port 50001.   Clients can connect via the stammerProxy by connecting to localhost:50000.  Forr example: helloClient.py -s localhost:50000
