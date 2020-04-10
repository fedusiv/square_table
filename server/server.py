import socket
import sys
from _thread import *
import threading
import time
import json
import algorithms
import communication_protocol as CP
from player import Player
import parser

class GameManager:

    PLAYERS_AMOUNT = 2  # Size of players in game
    game_run = False # if False, it means game waits for players to connect and choose roles; becomes True when all players will choose role
    players = []
    def __init__(self):
        self.thread_lock = threading.Lock()

    def add_player(self, player):
        if len(self.players) + 1 > self.PLAYERS_AMOUNT:
            # request to add more players than required
            print("Can not accept more players")
            return -1
        # check if name is already used
        for p in self.players:
            if p.name == player.name:
                # name is already used. Unacceptable
                return -2
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
            # Main loop for game
            # If game is not running. Game is waiting for players
            if self.game_run :
                pass
            else:
                # Check request
                player_ready_count = 0
                for player in self.players:
                    if player.request_role is not None:
                        player_ready_count += 1
                        continue
                    else:
                        # Someone is not ready for game. 
                        break
                if player_ready_count == self.PLAYERS_AMOUNT:
                    # START GAME
                    self.start_game()    

    # player send requst role for him in game
    def request_role(self, p_id, role):
        self.thread_lock.acquire()
        self.players[p_id].request_role = role
        print("player: " + self.players[p_id].name + " requested role: " + self.players[p_id].request_role)
        self.thread_lock.release()

    # If player is disconnected, so remove player
    def delete_player(self, p_id):
        self.thread_lock.acquire()
        print("player: " + self.players[p_id].name + " is deleting")
        del self.players[p_id]
        # reassign id for players 
        for i in range(len(self.players)):
            self.players[i].id = i
        # print players and role request
        players_list=""
        for p in self.players:
            if p is not None:
                players_list += p.name + " "
        print("players list : " + players_list)
        self.thread_lock.release()
    
    # Funtion to START GAME
    def start_game(self):
        # choose roles for players
        choices = []
        for player in  self.players:
            choices.append(player.request_role)
        # Only For Debug
        if self.PLAYERS_AMOUNT < 5:
            roles = algorithms.choose_roles_debug(len(self.players))
        else:
            roles = algorithms.choose_roles(choices)
        print("Set roles:")
        for i in range(self.PLAYERS_AMOUNT):
            self.players[i].role = roles[i]
            print(self.players[i].role)
        # prepare messages for players
        self.thread_lock.acquire()
        for player in self.players:
            player.send_start_game()    
        self.thread_lock.release()
        self.game_run = True



# thread function
# sock - sock client connection
# GM - game manager pointer
def threaded(sock, GM: GameManager):
    thread_lock = threading.Lock()
    init_message = False  # did receive init message?
    keep_alive_period = 1  # in seconds
    keep_alive_count = 10  # count of missed keep_alive_communications
    keep_alive_counter = 0
    player = None
    player_accepted = False  # If player was added to Game Manager 
    try:
        while True:
            # greeting part. loop should wait until receive greeting message
            if init_message is False:
                g_message = json.loads(sock.recv(1024).decode('UTF-8'))
                if g_message["type"] == CP.GREETING_TYPE:
                    player = Player(g_message["player_name"])
                    thread_lock.acquire()
                    player.id = GM.add_player(player)
                    if player.id == -1:
                        # means that required num of players already added. Exit from connection. Exit from thread
                        print("All players are already connected. Disconnect name: " + player.name)
                        break
                    if player.id == -2:
                        # player name is unacceptable. player name is already used
                        print("Can not accept player name: " + player.name + "  Player Name should be uniq")
                        sock.send(bytes(json.dumps({"type": CP.NAME_UNACCEPTABLE, "player_name": player.name}),'UTF-8'))
                        break
                    player_accepted = True
                    sock.send(bytes(json.dumps({"type": CP.GREETING_TYPE, "player_name": player.name, "status": CP.STATUS_OK}),
                                 'UTF-8'))
                    init_message = True
                    print("Greeting player : " + player.name)
                    # set timeout for receiving messages equal to keepalive. It means, that communication betweem server
                    # and client should occurs each keepalive period
                    sock.settimeout(keep_alive_period)
                else:
                    continue
            # send messages
            if not player.message_queue.empty():
                # if queue messages is not empty
                delivery = player.message_queue.get()
                sock.send(bytes(json.dumps(delivery), 'UTF-8')) # send message to client
            # receive messages
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
                # choose role request message
                if parsing.enum == parser.ParsingEnum.CHOOSE_ROLE_REQUEST:
                    GM.request_role(player.id, parsing.role)
                    sock.send(bytes(json.dumps({"type": CP.CHOOSE_ROLE_REQUEST, 
                                                "player_name": player.name, 
                                                "role": player.request_role}),'UTF-8'))
                    continue
                # player send answer, that game is really start
                if parsing.enum == parser.ParsingEnum.START_GAME:
                    print("  start game for player: " + player.name)

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
            if player_accepted:
                print("Disconnected player :  " + player.name)
                GM.delete_player(player.id)
            del player    
        else:
            print("Disconnected unknown client")
        sock.close()
    
    # if was any unexpected exeption
    except Exception as e:
        print(str(e))
        print("Closing connection and del player cause was exeption")
        if player is not None:
            if player_accepted:
                GM.delete_player(player.id)
            del player    
        sock.close()

def parse_received_message(info):
    type_switch = {
        CP.KEEPALIVE_TYPE: parser.parse_keepalive,
        CP.EXIT_TYPE: parser.parse_exit,
        CP.CHOOSE_ROLE_REQUEST: parser.parse_choose_role,
        CP.START_GAME: parser.parse_start_game
    }

    parse = type_switch.get(info.message["type"], parser.parse_error_parse)
    return parse(info)

def Main(s):
    host = ""
    port = 12345
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
        _thread_list.append(x)
    s.close()

_thread_list = []

if __name__ == '__main__':
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Main(s)
    except KeyboardInterrupt:
        print("Catch Keyboard Interrupt")
        s.close ()
        sys.exit(0)
    except Exception:
        print("Exeption exit")
    s.close()
    sys.exit(0)
