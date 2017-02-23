#
# Fergal O'Shea
# 2017

import struct
from socket import *
import random

end = 0
prev_frame_num = 0
curr_frame_num = 1
nak_count = 0

def crc16(data_in):
    poly = 0xB9B1                           #We use a polynomial of 0xB9B1
    size = len(data_in)                     #find the size of the data in, for loop
    crc = 0                                 #initalise remainder
    i = 0                                   #position in data
    while i < size:                         #loop through data
        byte = ord(data_in[i])                #convert byte to binary
        j = 0                               #loop through byte
        while j < 8:                        #
            if (crc & 1) ^ (byte & 1):        #
                crc = (crc >> 1) ^ poly     #divide by polynomial
            else:
                crc >>= 1                   #shift bit into remainder
            byte >>= 1                        #
            j += 1
        i += 1
    return crc                              #return answer

def gremlin_func(crc_in):                   #gremlin function
    i = random.randint(0,3)                 #choose a random number between 0 and 3
    if i == 2:                              #if random nuber is 2
        return crc_in % 2                   #get modulus 2 of crc. Modulus was chosen,
                                            #as answer guarentted to be in correct range
    else:
        return crc_in

def data_check( frame_in_num , data, checksum_client ): #checks data
    global prev_frame_num                               #takes in last accpeted frame number
    checksum_server = crc16(data.decode('utf-8'))       #generates new checksum
    print('server = ', checksum_server , 'client = ', checksum_client)
    checksum_server = gremlin_func(checksum_server)     #gremlins checksum
    if frame_in_num == prev_frame_num + 1 and checksum_client == checksum_server :  #checks for correct frame number and correct checksum
        prev_frame_num += 1                             #if correct, updates last accpeted frame
        return 1                                        #returns 1 for ack, 0 for nak
    else:
        return 0


ack = struct.Struct('2I')                               #ack frame structure
frame = struct.Struct('2I 8s I')                        #frame in structure

serverPort = 12000                                      #port to listen in
serverSocket = socket(AF_INET,SOCK_STREAM)              #create socket
serverSocket.bind(('', serverPort))                     #bind socket to port
serverSocket.listen(1)                                  #listen on port
print ('The server is ready to receive')
connectionSocket, addr = serverSocket.accept()          #accept first connection
file = open("received_Data.txt", "w")                   #open file, in write mode



while end == 0:                                         #loop while boolean flag is true
    if prev_frame_num == curr_frame_num:                #update expexted frame number
        curr_frame_num += 1
    data_packed = connectionSocket.recv(1024)           #recieve data
    if len(data_packed)>0:
        frame_in_num, frame_insize, data, checksum_client = frame.unpack(data_packed)   #unpack data
        print(frame_in_num, data_packed)
        frame_out_ack = data_check(frame_in_num, data, checksum_client)             #verify frame in, and decide output ack
        if frame_out_ack == 1:                          #
            file.write(data.decode('utf-8'))            #if frame was valid, write to file
        frame_out = ack.pack(curr_frame_num, frame_out_ack)     #pack ack frame
        connectionSocket.send(frame_out)                    #send ack frame
    if data.decode('utf-8') == '\x00\x00\x00\x00\x00\x00\x00\x00':  #check for empty frame, to signify end
        end = 1

connectionSocket.close()                                #close socket
file.close()                                            #close file


