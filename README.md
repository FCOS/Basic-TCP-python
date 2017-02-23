# Basic-TCP-python
Simulates sending data using TCP

High level description:
The first thing to happen in my program, is the client server connect to each other, via internet sockets. Once a connection has been established, the data transfer begins. The client starts by opening a text file. It then reads in 8 bytes of data from the text file, and stores it. Using the struct library, the client then packs this data, along with a sequence number and a frame size in the header, and a checksum in the trailer. The checksum is calculated using a CRC16 function, and returns the remainder after a division. This frame is then packed up and converted into bytes, to be transmitted.
At this stage, the server will be listening for data. Once it ‘hears’ data coming in, in capture the data, and store it. Again using the struct library, this byte stream is unpacked into its constituent parts. The frame then goes into a frame check function, which decides whether to send an ack or a nak. The function checks the frame number, to make sure it’s in the right sequence, and also computes the checksum on the data. If the checksum the server calculates matches the checksum it received from the client, the frame is good. This function returns either a 1 or a 0, (ack or nak), and then sends an ack frame back to the client, with the frame number it corresponds to, and the ack or nak. If the frame was valid, the server also writes to a file at this point.
The receiver then receives this ack frame, and decides what to do. If it is a negative ack, it will remake and send the frame. If it was a positive ack, it will begin the process again. The receiver will keep sending frames until it finishes the data file, at which point it will send an empty frame, and close the connection. The server will also end when it receives the empty frame.













Low level description:
Client:
The connection to the server is opened using the socket library. We create a socket called clientSocket, and connect it to the ‘localhost’ over port 12000.
serverName = 'localhost'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))
After the connection is set up, we then entire a while loop, that loops while a Boolean flag is true. The first thing that happens in the loop is data is read in from a file.
	data = file.read(8)
We then check if this is empty, indicating the end of the file. If it is empty, we set the Boolean flag to true, and the while loop will finish.
A CRC16 is then generated off this data, using the following function.
def crc16(data_in):
    	poly = 0xB9B1
    	size = len(data_in)
    	crc = 0
   	 i = 0
   	 while i < size:
   	     ch = ord(data_in[i])
   	     j = 0
   	     while j < 8:
  	          if (crc & 1) ^ (ch & 1):
  	              crc = (crc >> 1) ^ poly
  	          else:
  	              crc >>= 1
  	          ch >>= 1
  	          j += 1
  	      i += 1
  	  return crc

This function uses a polynomial of B9B1. It works like a standard CRC, by converting the data to binary, and dividing by the polynomial (XORing, using the ‘^’ operand). It then returns the remainder.
This checksum is then passed through a gremlin function, as follows, which takes in a CRC, and changes it if a random number between 0 and 3 is 2.

def gremlin_func(crc_in):
    i = random.randint(0,3)
    if i == 2:
        return crc_in % 2
    else:
        return crc_in

This checksum, along with the rest of the frame, is then packed up into a struct, and sent out.
values = (frame_number, frame.size, data.encode('utf-8'), checksum)
frame_out = frame.pack(*values)
clientSocket.send(frame_out)
The client then waits to receive the ack or nak from the server, and when it receives an incoming frame, unpacks it as follows.

data_packed = clientSocket.recv(1024)
frame_in_num, frame_in_ack = ack.unpack(data_packed)
At this point, the program performs differently, depending on if it received an ack or a nak. If it received an ack, it checks the ack is for the correct frame, and then loops back to the beginning of the while loop. If, however, it is nak, the program regenerates a checksum, in case the previous one fell victim of the gremlin function, and repacks and sends the data. It will then again listen for an ack or a nak, and will keep doing this until it receives an ack.
while frame_in_ack == 0:
    print('To Server:', frame_number, frame_out)
    print('From Server:', frame_in_num, 'ack =', frame_in_ack)

    #new checksum (for gremlin)
    checksum_pre_gremlin = crc16(data)
    checksum = gremlin_func(checksum_pre_gremlin)
    values = (frame_number, frame.size, data.encode('utf-8'), checksum)
    frame_out = frame.pack(*values)
    clientSocket.send(frame_out)

    #receive ack
    data_packed = clientSocket.recv(1024)
    frame_in_num, frame_in_ack = ack.unpack(data_packed)
Once the while loop ends, the program will then terminate by closing the socket.











Server:
The server also starts by setting up the connection, but in a slightly different way. The server creates an open port, and listens on it for 1 connection. 
serverPort = 12000
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)
Once it receives a connection request, it accepts, and opens a line of communication between the two.

connectionSocket, addr = serverSocket.accept()
It then creates/opens a file, which it sets to ‘write’ mode, by putting a ‘w’ as the second argument.

file = open("received_Data.txt", "w")
The server then enters a while loop, which also runs based on a boolean flag, to indicate when it is no longer receiving data.
The loop first updates its expected frame number. This is done when the last valid frame number is the same as the current expected frame number, ie, after a frame has just been accepted.
if prev_frame_num == curr_frame_num:
  	  curr_frame_num += 1
The server then waits until it receives data from the client, and strores it when it comes in.

data_packed = connectionSocket.recv(1024)
The server then unpacks this data into its constituent parts, using the unpack function.
frame_in_num, frame_insize, data, checksum_client = frame.unpack(data_packed)
It then passes the relevant data into a function which checks the validity of the frame.
data_check( frame_in_num , data, checksum_client ):
    global prev_frame_num
    checksum_server = crc16(data.decode('utf-8')) 
    checksum_server = gremlin_func(checksum_server)
    if frame_in_num == prev_frame_num + 1 and checksum_client == checksum_server :
        prev_frame_num += 1
        return 1
    else:
        return 0
This function generates a checksum based off the data it receives, and checks this against the checksum the client sent. If they match, and the frame number is correct, the function returns a 1, or ack, and if not, it returns a 0, or nak.
This ack/nak is then packed up with the frame number and sent back to the client. The server either loops back to the start, or exits, and finishes by closing the file, and the socket.
