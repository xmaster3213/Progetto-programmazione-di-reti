#!/usr/bin/env python3
from os import close, times
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread, Timer
import random
import threading
import time
from datetime import datetime
import struct

class Server:
    
    MAX_NUMBER_OF_PLAYERS = 2
    GAME_DURATION = 30

    #All clients
    clients = []
    #All IP
    indirizzi = {}
    #All clients points
    points = {}
    #Variable that rappresent the game status
    game_start = False

    server = socket(AF_INET, SOCK_STREAM)

    def __init__(self,ip,port):        
        addr = (ip, port)
        self.server.bind(addr)
        self.server.listen(self.MAX_NUMBER_OF_PLAYERS)
        print("Waiting for connections...")

    def run(self):
        accept_thread = Thread(target=self.accetta_connessioni_in_entrata)
        accept_thread.start()
        accept_thread.join()

    """Accept the connections in input, and start the game."""
    def accetta_connessioni_in_entrata(self):
        while True:
            client, client_address = self.server.accept()
            #If the number of Player connected reached the maximum or the game already started prevent other from connecting
            if(len(self.indirizzi) < self.MAX_NUMBER_OF_PLAYERS and not self.game_start):
                print("%s:%s Connected." % client_address)
                self.indirizzi[client] = client_address
                self.clients.append(client)
                Thread(target=self.gestice_client, args=(client,)).start()
                #When the lobby is full start the game
                if(len(self.indirizzi) == self.MAX_NUMBER_OF_PLAYERS):
                    time.sleep(1)
                    self.game_start = True
                    self.broadcast("GAME START!!!")
                    self.broadcast("AVETE %i SECONDI PER FARE PIU PUNTI POSSIBILI" % self.GAME_DURATION)
                    threading.Timer(self.GAME_DURATION, self.gameEnd).start()
                    Thread(target=self.gameStart).start()
            else:
                self.send_msg(client, "The Server is full, sorry...")
                self.send_msg(client, "!close")
                client.close()

    """Single client life cycle."""
    def gestice_client(self, client):
        choises = ["question", "question", "trap"]
        answer = 0
        self.points[client] = 0
        nome = str(self.indirizzi[client])
        benvenuto = 'Benvenuto %s! Servono %i giocatori!' % (nome, self.MAX_NUMBER_OF_PLAYERS)
        self.send_msg(client, benvenuto)
        msg = "%s si è unito alla partita!" % nome
        self.broadcast(msg)
        #Loop relative to the game
        while True:
            try:
                msg = self.recv_msg(client)
                #Choise message
                if(msg[:-1] == "choise_"):
                    #Shuffle the choises and the get the one in the position the client decided
                    random.shuffle(choises)
                    #If the choise == trap, the client lose and get disconnected
                    if(choises[int(msg[-1]) - 1] == "trap"):
                        self.send_msg(client, "Hai selezionato il trabocchetto... Hai perso!")
                        self.send_msg(client, "!close")
                        self.closeConnection(client)
                        break
                    #Otherwise generate 2 random numbers and answer how much is the sum of the 2
                    else:
                        a = random.randint(0, 1000)
                        b = random.randint(0, 1000)
                        answer = a + b
                        self.send_msg(client, str(a) + " + " + str(b) + " = ???")
                #Answer message
                elif(msg[0] == "&"):
                    #Convert the answer in INT if possible, otherwise give None
                    response = int(msg[1:]) if msg[1:].isdigit() else None
                    #If the answer wasn't an INT, close the connection with the client
                    if (response == None):
                        self.send_msg(client, "!close")
                        self.closeConnection(client)
                        break
                    #If the answer is correct add a point and give the feedback to the client
                    if(int(msg[1:]) == answer):
                        self.points[client] += 1
                        self.send_msg(client, "Risposta corretta!")
                    #Otherwise the answer is wrong, subtract a point and give the feedback to the client
                    else:
                        self.points[client] -= 1
                        self.send_msg(client, "Risposta sbagliata!")
                #Client send an unexpected message, disconnect
                else:
                    self.closeConnection(client)
                    break
            
            #Client disconnected
            except Exception as exc:
                self.closeConnection(client)
                break
            
    """Broadcast a given message to all clients."""
    def broadcast(self, msg):  # il prefisso è usato per l'identificazione del nome.
        for client in self.clients:
            self.send_msg(client, msg)

    """Start the game."""
    def gameStart(self):
        print("Game started.")
        self.broadcast("!start")

    """End the game."""
    def gameEnd(self):
        print("Game ended.")
        #Comunicates the winner
        if(len(self.points) != 0):
            winner = None
            for user in self.clients:
                if(max(self.points.values()) == self.points[user]):
                    winner = user
                self.send_msg(user, "You got " + str(self.points[user]) + " points!")
            self.broadcast(str(self.indirizzi[winner]) + " HA VINTO CON " + str(max(self.points.values())) + " PUNTI!!!")
        self.game_start = False    
        #Send a message to all clients to disconnect
        self.broadcast("!close")

    """Close the connection with the given client."""
    def closeConnection(self, client):
        print("%s:%s Disconnected." % self.indirizzi[client])
        self.clients.remove(client)
        del self.indirizzi[client]
        del self.points[client]
        client.close()

    """Send a given message to the given client."""
    def send_msg(self, sock, msg):
        # Prefix each message with a 4-byte length (network byte order)
        msg = struct.pack('>I', len(bytes(msg, "utf8"))) + bytes(msg, "utf8")
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
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data


server = Server("", 53000)
server.run()
    

