#!/usr/bin/env python3
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter as tkt
import time
import struct
import argparse
import sys

class Client:

    client_socket = None
    finestra = None
    msg_list = None
    text_input_frame = None
    my_msg = None
    choise_button_frame = None
    
    def __init__(self):
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        options = self.get_arguments()
        addr = (options.server_ip, options.server_port)
        self.client_socket.connect(addr)

    def run(self):
        self.createGraphicInterface()
        receive_thread = Thread(target=self.receive)
        receive_thread.start()
        tkt.mainloop()

    def get_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-ip","--address",dest="server_ip", help="[+] Insert the Server IP Address", default="localhost")
        parser.add_argument("-port", dest="server_port", type=int, help="[+] Insert the Server Port", default=53000)
        option = parser.parse_args()
        return option

    def createGraphicInterface(self):
        #Create game window
        self.finestra = tkt.Tk()
        self.finestra.title("Chat_Game")
        #Frame for messages
        messages_frame = tkt.Frame(self.finestra)
        self.my_msg = tkt.StringVar()
        self.my_msg.set("Scrivi qui i tuoi messaggi.")
        scrollbar = tkt.Scrollbar(messages_frame)
        self.msg_list = tkt.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tkt.RIGHT, fill=tkt.Y)
        self.msg_list.pack(side=tkt.LEFT, fill=tkt.BOTH)
        self.msg_list.pack()
        messages_frame.pack()
        #Frame for text input
        self.text_input_frame = tkt.Frame(self.finestra)
        entry_field = tkt.Entry(self.text_input_frame, width=30, textvariable=self.my_msg)
        entry_field.bind("<Return>", lambda x: self.sendMsg(prefix="&"))
        entry_field.pack(side=tkt.LEFT)
        send_button = tkt.Button(self.text_input_frame, width=10, text="Invio", command=lambda: self.sendMsg(prefix="&")) 
        send_button.pack(side=tkt.RIGHT)
        send_button.pack()
        entry_field.pack()
        #Frame for choises buttons
        self.choise_button_frame = tkt.Frame(self.finestra)
        choise_label = tkt.Label(self.choise_button_frame, width=30, text="Scegli una delle 3 opzioni!")
        choise_label.pack(side=tkt.TOP)
        choise1_button = tkt.Button(self.choise_button_frame, width=10, text="1", command=lambda: self.sendChoise(1)) 
        choise1_button.pack(side=tkt.LEFT)
        choise2_button = tkt.Button(self.choise_button_frame, width=10, text="2", command=lambda: self.sendChoise(2)) 
        choise3_button = tkt.Button(self.choise_button_frame, width=10, text="3", command=lambda: self.sendChoise(3)) 
        choise3_button.pack(side=tkt.RIGHT)
        choise_label.pack()
        choise1_button.pack()
        choise2_button.pack()
        choise3_button.pack()
        #Function to be called on closing window
        self.finestra.protocol("WM_DELETE_WINDOW", self.on_closing)

    """Recive message from the server."""
    def receive(self):
        while True:
            try:
                msg = self.recv_msg(self.client_socket)
                #Utility messages
                if(msg[0] == "!"):
                    if(msg == "!close"):
                        self.client_socket.close()
                        self.text_input_frame.pack_forget()
                        self.choise_button_frame.pack_forget()
                        time.sleep(3)
                        self.finestra.quit()
                        break
                    elif(msg == "!start"):
                        self.choise_button_frame.pack()
                #All other messages
                else:    
                    self.msg_list.insert(tkt.END, msg)
            except OSError:  
                break

    """Send a message."""
    def send(self, msg):
        self.send_msg(self.client_socket, msg)

    """Send a message from the text input"""
    def sendMsg(self, event=None, prefix=""):
        self.choise_button_frame.pack()
        self.text_input_frame.pack_forget()
        msg = self.my_msg.get()
        self.my_msg.set("")
        self.send(prefix + msg)

    """Send a choise made by the user troughth a button"""
    def sendChoise(self, choise):
        self.choise_button_frame.pack_forget()
        self.text_input_frame.pack()
        msg = "choise_" + str(choise)
        self.send(msg)

    """Close the user window."""
    def on_closing(self, event=None):
        self.client_socket.close()
        self.finestra.quit()

    """Send a given message to the given client."""
    def send_msg(self, sock, msg):
        # Prefix each message with a 4-byte length (network byte order)
        msg = struct.pack('>I', len(msg)) + bytes(msg, "utf8")
        sock.sendall(msg)

    """Recive a message to the given client."""
    def recv_msg(self, sock):
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(sock, msglen).decode("utf8")

    """Recive N bytes from the stream to the given client"""
    def recvall(self, sock, n):
        #Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

try:
    client = Client()
    client.run()
except Exception:
    print("No server with this IP and PORT found.")
    sys.exit()

