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

class GameManager:

    PLAYERS_AMOUNT = 5  # Size of players in game
    game_run = False # if False, it means game waits for players to connect and choose roles; becomes True when all players will choose role
    players = []
    def __init__(self):
        self.thread_lock = threading.Lock()

    def add_player(self, player):
        if len(self.players) > self.PLAYERS_AMOUNT:
            # request to add more players than required
            return -1
        self.players.append(player)
        p_id = len(self.players)
        p_id -= 1
        print(" add new player to GM with id: " + str(p_id) + " player name: " + player.name)
        players_list = ""
        for p in self.players:
            if p is not None:
                players_list += p.name + " "
        print("players list : " + players_list)
        return p_id

    def game_thread(self):
        while True:
            pass

    # player send requst role for him in game
    def request_role(self, p_id, role):
        self.thread_lock.acquire()
        self.players[p_id].request_role = role
        print("player: " + self.players[p_id].name + " requested role: " + self.players[p_id].request_role)
        self.thread_lock.release()
    
    def delete_player(self, p_id):
        self.thread_lock.acquire()
        print("player: " + self.players[p_id].name + " is deleting")
        del self.players[p_id]
        # reassign id for players 
        for i in range(len(self.players)):
            self.players[i].id = i
        # print players and role request
        players_list=""
        role_list=""
        for p in self.players:
            if p is not None:
                players_list += p.name + " "
                role_list += p.request_role + " "
        print("players list : " + players_list)
        print("request role list : " + role_list)
        self.thread_lock.release()

# thread function
# sock - sock client connection
# GM - game manager pointer
def threaded(sock, GM: GameManager):
    thread_lock = threading.Lock()
    init_message = False  # did receive init message?
    keep_alive_period = 1  # in seconds
    keep_alive_count = 5  # count of missed keep_alive_communications
    keep_alive_counter = 0
    while True:
        # greeting part. loop should wait until receive greeting message
        if init_message is False:
            g_message = json.loads(sock.recv(1024).decode('UTF-8'))
            if g_message["type"] == CP.GREETING_TYPE:
                player = Player(g_message["player_name"])
                thread_lock.acquire()
                player.id = GM.add_player(player)
                if player.id == -1:
                    # means that required num of players already added. Exit from connection
                    print("All players are already connected")
                    break
                sock.send(bytes(json.dumps({"type": CP.GREETING_TYPE, "player_name": player.name, "status": CP.STATUS_OK}),
                             'UTF-8'))
                init_message = True
                previous_time_point = time.time()
                print("Greeting player : " + player.name)
                # set timeout for receiving messages equal to keepalive. It means, that communication betweem server
                # and client should occurs each keepalive period
                sock.settimeout(keep_alive_period)
            else:
                continue
        # receive message
        try:
            message = json.loads(sock.recv(1024).decode('UTF-8'))
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
            # choose role message
            if parsing.enum == parser.ParsingEnum.CHOOSE_ROLE:
                GM.request_role(player.id, parsing.role)
                continue

        except socket.timeout:
            # if does not recieve need to send keepalive message to check is client alive.
            keep_alive_counter += 1
            if keep_alive_counter > keep_alive_count:
                # client does not respones
                print("Client of player : " + player.name + " disconnected via keep alive")
                break
            servertime = time.asctime(time.localtime(time.time()))
            sock.send(bytes(json.dumps({"type": CP.KEEPALIVE_TYPE, "player_name": player.name, "server_time": servertime}),
                         'UTF-8'))

        # end of loop
    # connection closed
    if player is not None:
        print("Disconnected player :  " + player.name)
        GM.delete_player(player.id)
    else:
        print("Disconnected unknown client")
    sock.close()

def parse_received_message(info):
    type_switch = {
        CP.KEEPALIVE_TYPE: parser.parse_keepalive,
        CP.EXIT_TYPE: parser.parse_exit,
        CP.CHOOSE_ROLE: parser.parse_choose_role
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
    game = GameManager()
    gt = threading.Thread(name="game", target=game.game_thread)
    gt.start()
    while True:
        c, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])
        x = threading.Thread(name="client" + str(client_count), target=threaded, args=(c, game))
        x.start()
        client_count += 1
    s.close()


if __name__ == '__main__':
    Main()
