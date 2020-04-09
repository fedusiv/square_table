import communication_protocol as CP
from enum import Enum


class ParsingEnum(Enum):
    EXIT = 1,
    KEEP_ALIVE = 2,
    CHOOSE_ROLE_REQUEST = 3,
    START_GAME = 4


class Parsing:
    enum = None
    data = None
    role = None
    def __init__(self, enum: ParsingEnum, data=None):
        self.enum = enum
        self.data = data


class parserInput:
    message = None
    player_name = None

    def __init__(self, message, player_name):
        self.message = message
        self.player_name = player_name


def parse_error_parse(input):
    pass


def parse_keepalive(input):
    if input.message["status"] == CP.STATUS_OK:
        return Parsing(ParsingEnum.KEEP_ALIVE)


def parse_exit(input):
    if input.message["player_name"] == input.player_name:
        return Parsing(ParsingEnum.EXIT)

def parse_choose_role(input):
    if input.message["player_name"] == input.player_name:
        res = Parsing(ParsingEnum.CHOOSE_ROLE_REQUEST)
        res.role = input.message["role"]
        return res

def parse_start_game(input):
    return Parsing(ParsingEnum.START_GAME)