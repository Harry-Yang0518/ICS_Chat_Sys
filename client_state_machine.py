"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import json


class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s
        self.flag = 0
        self.initiating = 0
        self.colors = ['black','white']
        self.chessboard = [[-1 for i in range(10)] for j in range(10)]
        self.game_peer = ''

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'Successfully connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'This user is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'You cannot talk to yourself!\n'
        else:
            self.out_msg += 'User is not online and please try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'Disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''

        if self.flag == 1:
            if my_msg == 'y':
                mysend(self.s, json.dumps({"action":"game_accept", "target":self.game_peer}))
                self.initiating = 1
            else:
                mysend(self.s, json.dumps({"action":"game_reject", "target":self.game_peer}))
            self.flag=0
            return ''
            


        if my_msg[:5] == '/game':
            operators = my_msg.split()
            try:
                if operators[1] == 'start':
                    if operators[2] == self.me:
                        raise Exception
                    else:
                        mysend(self.s, json.dumps({"action":"game_start", "target":operators[2]}))
                elif operators[1] == 'move':
                    mysend(self.s, json.dumps({"action":"game_move", "x":operators[2], "y":operators[3],"target":self.game_peer}))
                elif operators[1] == 'quit':
                    mysend(self.s, json.dumps({"action":"game_quit", "target":self.game_peer}))
                else:
                    self.out_msg += "Invalid command\n"
            except:
                self.out_msg += 'Invalid command\n'
            return self.out_msg

        if len(peer_msg) > 0:
            pm = json.loads(peer_msg)
            if pm["action"] == "game_start":
                self.out_msg += "Start Playing with {}, play as {}!".format(pm["from"],self.colors[self.initiating])
                self.game_peer = pm["from"]
            elif pm["action"] == "game_reject":
                self.out_msg += '{} rejected your request\n'.format(pm["from"])
            elif pm["action"] == "game_invite":
                self.out_msg += "{} invites you to play game, want to join in?   TYPE (y/N)\n".format(pm["from"])
                self.game_peer = pm["from"]
                self.flag = 1
            elif pm["action"] == "game_win":
                self.game_peer == ''
                self.out_msg += 'GAME OVER, {} wins!\n'.format(pm["from"])
                self.chessboard = [[-1 for i in range(10)] for j in range(10)]
            elif pm["action"] == "game_move":
                if pm["from"] == self.game_peer:
                    self.chessboard[int(pm["x"])][int(pm["y"])] = 1
                else:
                    self.chessboard[int(pm["x"])][int(pm["y"])] = 0
                self.out_msg += '{} placed on ({},{})'.format(pm["from"], pm["x"], pm["y"])
            elif pm["action"] == "game_error":
                self.out_msg += 'game error: ' + pm["status"]+'\n'
            elif pm["action"] == "game_quit":
                self.game_peer = ''
                self.out_msg += 'game ended, {} quits!\n'.format(pm["from"])
                self.chessboard = [[-1 for _ in range(10)] for _ in range(10)]
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    # print(poem)
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.peer = peer_msg["from"]
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += 'Successfully connected with ' + self.peer
                    self.out_msg += '. Let\'s chat!\n\n'
                    self.out_msg += '------------------------------------\n'
                    self.state = S_CHATTING


        elif self.state == S_CHATTING:
            if len(my_msg) > 0:   
                mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            if len(peer_msg) > 0:    
                peer_msg = json.loads(peer_msg)
                if 'game' in peer_msg["action"]:
                    pass
                elif peer_msg["action"] == "connect":
                    self.out_msg += "(" + peer_msg["from"] + " joined)\n"
                elif peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                else:
                    self.out_msg += peer_msg["from"] + peer_msg["message"]


            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
