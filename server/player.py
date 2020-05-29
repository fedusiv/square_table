import queue
import communication_protocol as CP

class PlayerStats:
    gold = None
    king_points = None
    people_points = None

    def __init__(self):
        # set default points
        self.gold = 10
        self.king_points = 0
        self.people_points = 0

class Player:

    name = None
    role = None
    request_role = None
    message_queue = None    # queue for sending messages
    player_stats = None     # object for player stats
    id = None   # id in Game Manager

    def __init__(self, player_name):
        self.name = player_name
        self.message_queue = queue.Queue()
        self.player_stats = PlayerStats()
    def send_start_game(self):
        message = {"type": CP.START_GAME,"player_name" : self.name, "role": self.role}
        self.message_queue.put(message)