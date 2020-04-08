import queue
import communication_protocol as CP
class Player:

    name = None
    role = None
    request_role = None
    message_queue = None    # queue for sending messages
    id = None   # id in Game Manager

    def __init__(self, player_name):
        self.name = player_name
        self.message_queue = queue.Queue()

    def send_start_game(self):
        message = {"type": CP.START_GAME,"player_name" : self.name, "role": self.role}
        self.message_queue.put(message)