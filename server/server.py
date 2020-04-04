import tkinter as tk
from tkinter import ttk
import socket
from _thread import *
import threading
import time
import json
import communication_protocol as CP
from player import Player
import parser

class Manager:
    def __init__(self):
        pass



# thread function
def threaded(c):
    init_message = False  # did receive init message?
    previous_time_point = None
    current_time_point = None
    keep_alive_period = 2  # in seconds
    keep_alive_count = 5  # count of missed keep_alive_communications
    keep_alive_counter = 0
    while True:
        # greeting part. loop should wait until receive greeting message
        if init_message is False:
            g_message = json.loads(c.recv(1024).decode('UTF-8'))
            if g_message["type"] == CP.GREETING_TYPE:
                player = Player(g_message["player_name"])
                c.send(bytes(json.dumps({"type": CP.GREETING_TYPE, "player_name": player.name, "status": CP.STATUS_OK}),
                             'UTF-8'))
                init_message = True
                previous_time_point = time.time()
                print("Greeting player : " + player.name)
                # set timeout for receiving messages equal to keepalive. It means, that communication betweem server
                # and client should occurs each keepalive period
                c.settimeout(keep_alive_period)
            else:
                continue
        # receive message
        try:
            message = json.loads(c.recv(1024).decode('UTF-8'))
            keep_alive_counter = 0  # message receive keep_alive counter set to 0
            info = parser.parserInput(message, player.name)
            parsing = parse_received_message(info)

            # exit message
            if parsing.enum == parser.ParsingEnum.EXIT:
                print(" Received exit from player : " + player.name)
                break
            # keep_alive message
            if parsing.enum == parser.ParsingEnum.KEEP_ALIVE:
                # just to be in touch with client
                pass


        except socket.timeout:
            # if does not recieve need to send keepalive message to check is client alive.
            keep_alive_counter += 1
            if keep_alive_counter > keep_alive_count:
                # client does not respones
                print("Client of player : " + player.name + " disconnected via keep alive")
                break
            servertime = time.asctime(time.localtime(time.time()))
            c.send(bytes(json.dumps({"type": CP.KEEPALIVE_TYPE, "player_name": player.name, "server_time": servertime}),
                         'UTF-8'))

        # end of loop
    # connection closed
    if player is not None:
        print("Disconnected player :  " + player.name)
    else:
        print("Disconnected unknown client")
    c.close()

def parse_received_message(info):
    type_switch = {
        CP.KEEPALIVE_TYPE: parser.parse_keepalive,
        CP.EXIT_TYPE: parser.parse_exit
    }

    parse = type_switch.get(info.message["type"], parser.parse_error_parse)
    return parse(info)

def Main():
    host = ""
    port = 12345
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("socket binded to port", port)
    s.listen(5)
    print("socket is listening")
    # a forever loop until client wants to exit
    client_count = 0
    manager = Manager()
    while True:
        c, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])
        x = threading.Thread(name="client" + str(client_count), target=threaded, args=(c,))
        x.start()
        client_count += 1
    s.close()


if __name__ == '__main__':
    Main()
