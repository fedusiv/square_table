import queue
import communication_protocol as CP

class PlayerStats:
    points_value = None

    def __init__(self):
        # set default points
        self.points_value = 0
	 
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
    def send_start_round(self, description):
        message = {"type": CP.ROUND_BEGIN, "description": description}
        self.message_queue.put(message)
