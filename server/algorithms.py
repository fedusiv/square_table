import random
# Set roles for player
# @arg choices - array which role player wants
def choose_roles(choices):
    roles = ["general", "diplomat", "treasurer","bishop", "manufacturer" ]
    roles_request = {}   # dict stores which role players want
    player_id = 0
    for role in roles:
        temp = []
        for choice in choices:
            if choice == role:
                temp.append(player_id)
                player_id += 1
        roles_request[role] = temp 
 
    players = [0, 1, 2 , 3, 4]
    roles_sorted = {}
    for request in roles_request:
        if len(roles_request[request]) > 0 : 
            roles_sorted[request] = random.choice(roles_request[request])
            roles.pop(roles.index(request))
            players.pop(players.index(roles_sorted[request]))
    # for all roles who left after sorting
    for role in roles:
        roles_sorted[role] = random.choice(players)
        players.pop(players.index(roles_sorted[role]))
    
    roles_choose = [None] * 3 # 5
    for role in roles_sorted:
        roles_choose[roles_sorted[role]] = role
    return roles_choose
    
def choose_roles_debug(count):
    if count == 1:
        return ["general"]
    elif count == 2:
        return ["general", "diplomat"]
    elif count == 3 :
        return ["general", "diplomat", "treasurer"]
    else:
        return ["general", "diplomat", "treasurer","bishop"]
    