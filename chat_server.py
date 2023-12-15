"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang
"""



import time
import socket
import select
import sys
import string
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp
import sqlutils
import chessboard


class Server:
    def __init__(self):
        sqlutils.sql_init()
        self.new_clients = []  # list of new sockets of which the user id is not known
        self.logged_name2sock = {}  # dictionary mapping username to socket
        self.logged_sock2name = {}  # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        # start server
        self.boards = {}
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        # initialize past chat indices
        self.indices = {}
        # sonnet
        # self.sonnet_f = open('AllSonnets.txt.idx', 'rb')
        # self.sonnet = pkl.load(self.sonnet_f)
        # self.sonnet_f.close()
        self.sonnet = indexer.PIndex("AllSonnets.txt")

    def new_client(self, sock):
        # add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)


    def login(self, sock):
        """
        Handles the login or signin process for a socket connection.

        Args:
            sock (socket): The socket through which the client is communicating.
        """
        try:
            msg = json.loads(myrecv(sock))
            print("login:", msg)
            
            if not msg:
                # client died unexpectedly
                self.logout(sock)
                return
            
            action = msg.get("action")
            name = msg.get("name")
            passwd = msg.get("passwd")

            # Handle login action
            if action == "login":
                self.handle_login(sock, name, passwd)

            # Handle signin action
            elif action == "signin":
                self.handle_signin(sock, name, passwd)

            else:
                print('Unknown action code received')
                # Unknown action, might want to send a response back to client

        except Exception as e:
            print("Error handling login:", e)
            if sock in self.all_sockets:
                self.all_sockets.remove(sock)

    def handle_login(self, sock, name, passwd):
        """Helper function to handle the login process."""
        if self.group.is_member(name):
            # a client under this name has already logged in
            self.send_login_response(sock, "duplicate", "Duplicate login!")
            print(name + ' duplicate login attempt')
            return

        if name not in sqlutils.get_users():
            # no such user
            self.send_login_response(sock, "no such user", "No such user!")
            print('No such user:', name)
            return

        # Validate user password
        key = sqlutils.get_password(name)
        if key == passwd:
            self.login_success(sock, name)
        else:
            # wrong password
            self.send_login_response(sock, "wrong password", "Wrong password!")
            print(name + ' wrong password')

    def handle_signin(self, sock, name, passwd):
        """Helper function to handle the signin process."""
        if sqlutils.create_user(name, passwd):
            self.send_login_response(sock, "ok", "Signed in successfully.")
            print(name + ' signed in')
        else:
            self.send_login_response(sock, "duplicate", "Duplicate signin!")
            print(name + ' duplicate signin attempt')

    def send_login_response(self, sock, status, message):
        """Helper function to send a login response to the client."""
        mysend(sock, json.dumps({
            "action": "login",
            "status": status,
            "message": message
        }))

    def login_success(self, sock, name):
        """Processes successful login, setting up user state and history."""
        self.new_clients.remove(sock)
        self.logged_name2sock[name] = sock
        self.logged_sock2name[sock] = name
        if name not in self.indices.keys():
            try:
                self.indices[name] = pkl.load(open(name+'.idx', 'rb'))
            except IOError:
                # chat index does not exist, then create one
                self.indices[name] = indexer.Index(name)
        print(name + ' logged in')
        self.group.join(name)
        self.send_login_response(sock, "ok", "Logged in successfully.")


    def logout(self, sock):
        # remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx', 'wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        if name in self.boards.keys():
            del self.boards[name]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

# ==============================================================================
# main command switchboard
# ==============================================================================
    def handle_msg(self, from_sock):
        # read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
            # ==============================================================================
            # handle connect request
            # ==============================================================================
            msg = json.loads(msg)
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = json.dumps({"action": "connect", "status": "self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg = json.dumps(
                        {"action": "connect", "status": "success"})
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, json.dumps(
                            {"action": "connect", "status": "request", "from": from_name}))
                else:
                    msg = json.dumps({"action": "connect", "status": "no-user"})
                mysend(from_sock, msg)
# ==============================================================================
# handle messeage exchange: one peer for now. will need multicast later
# ==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                #said = msg["from"]+msg["message"]
                said2 = text_proc(msg["message"], from_name)
                self.indices[from_name].add_msg_and_index(said2)
                for g in the_guys[1:]:
                    to_sock = self.logged_name2sock[g]
                    self.indices[g].add_msg_and_index(said2)
                    mysend(to_sock, json.dumps(
                        {"action": "exchange", "from": msg["from"], "message": msg["message"]}))
# ==============================================================================
#                 listing available peers
# ==============================================================================
            elif msg["action"] == "list":
                from_name = self.logged_sock2name[from_sock]
                msg = self.group.list_all()
                mysend(from_sock, json.dumps(
                    {"action": "list", "results": msg}))
# ==============================================================================
#             retrieve a sonnet
# ==============================================================================
            elif msg["action"] == "poem":
                poem_indx = int(msg["target"])
                from_name = self.logged_sock2name[from_sock]
                print(from_name + ' asks for ', poem_indx)
                poem = self.sonnet.get_poem(poem_indx)
                poem = '\n'.join(poem).strip()
                print('here:\n', poem)
                mysend(from_sock, json.dumps(
                    {"action": "poem", "results": poem}))
# ==============================================================================
#                 time
# ==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, json.dumps(
                    {"action": "time", "results": ctime}))
# ==============================================================================
#                 deal with game
# ==============================================================================
            elif msg["action"] in ["game_start", "game_accept", "game_reject", "game_move", "game_quit"]:
                self.handle_game_actions(msg, from_sock)
# ==============================================================================
#                 search
# ==============================================================================
            elif msg["action"] == "search":
                term = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                print('search for ' + from_name + ' for ' + term)
                # search_rslt = (self.indices[from_name].search(term))
                search_rslt = '\n'.join(
                    [x[-1] for x in self.indices[from_name].search(term)])
                print('server side search: ' + search_rslt)
                mysend(from_sock, json.dumps(
                    {"action": "search", "results": search_rslt}))
# ==============================================================================
# the "from" guy has had enough (talking to "to")!
# ==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps({"action": "disconnect"}))
# ==============================================================================
#                 the "from" guy really, really has had enough
# ==============================================================================

        else:
            # client died unexpectedly
            self.logout(from_sock)

  
#====function to handle game actions============================================
    def handle_game_actions(self, msg, from_sock):
        from_name = self.logged_sock2name[from_sock]
        to_name = msg["target"]
        print(f'game {msg["action"]} from {from_name} to {to_name}')

        if to_name not in self.group.list_all():
            self.send_game_error(from_sock, "no-user")
            if msg["action"] in ["game_move", "game_quit"]:
                self.cleanup_game_board(from_name)
            return

        if msg["action"] == "game_start":
            self.start_game(from_sock, from_name, to_name)

        elif msg["action"] == "game_accept":
            self.accept_game(from_sock, from_name, to_name)

        elif msg["action"] == "game_reject":
            self.reject_game(from_sock, to_name)

        elif msg["action"] == "game_move":
            self.move_game(from_sock, msg, from_name, to_name)

        elif msg["action"] == "game_quit":
            self.quit_game(from_sock, from_name, to_name)

    def send_game_error(self, sock, error_status):
        mysend(sock, json.dumps({"action": "game_error", "status": error_status}))

    def cleanup_game_board(self, player_name):
        if player_name in self.boards.keys():
            del self.boards[player_name]

    def start_game(self, from_sock, from_name, to_name):
        if to_name in self.boards.keys():
            self.send_game_error(from_sock, "busy")
        else:
            to_sock = self.logged_name2sock[to_name]
            mysend(to_sock, json.dumps({"action": "game_invite", "from": from_name}))

    def accept_game(self, from_sock, from_name, to_name):
        if to_name in self.boards.keys():
            self.send_game_error(from_sock, "busy")
        else:
            self.boards[to_name] = self.boards[from_name] = chessboard.Board()
            self.boards[to_name].last = from_name
            to_sock = self.logged_name2sock[to_name]
            mysend(to_sock, json.dumps({"action": "game_start", "from": from_name}))
            mysend(from_sock, json.dumps({"action": "game_start", "from": to_name}))

    def reject_game(self, from_sock, to_name):
        to_sock = self.logged_name2sock[to_name]
        mysend(to_sock, json.dumps({"action": "game_reject", "from": self.logged_sock2name[from_sock]}))

    def move_game(self, from_sock, msg, from_name, to_name):
        if to_name not in self.boards:
            self.send_game_error(from_sock, "unknown error")
            self.cleanup_game_board(from_name)
        else:
            try:
                to_sock = self.logged_name2sock[to_name]
                if from_name == self.boards[from_name].last:
                    self.send_game_error(from_sock, "not your turn")
                else:
                    x, y = int(msg["x"]), int(msg["y"])
                    # Assuming 'place' is a method to update the game board
                    self.boards[from_name].place(x, y, from_name)
                    self.boards[from_name].last = from_name
                    # Send game move to both players
                    game_move_msg = json.dumps({"action": "game_move", "from": from_name, "x": x, "y": y})
                    mysend(to_sock, game_move_msg)
                    mysend(from_sock, game_move_msg)
                    # Check for win condition
                    winner = self.boards[from_name].check() 
                    if winner != -1:
                        win_msg = json.dumps({"action": "game_win", "from": winner})
                        mysend(to_sock, win_msg)
                        mysend(from_sock, win_msg)
                        self.cleanup_game_board(from_name)
            except Exception as e:
                print("Error in move_game:", e)
                self.send_game_error(from_sock, "illegal move")

    def quit_game(self, from_sock, from_name, to_name):
        if to_name not in self.boards:
            self.send_game_error(from_sock, "unknown error")
        else:
            to_sock = self.logged_name2sock[to_name]
            quit_msg = json.dumps({"action": "game_quit", "from": from_name})
            mysend(from_sock, quit_msg)
            mysend(to_sock, quit_msg)
            self.cleanup_game_board(from_name)

    
    
# ==============================================================================
# main loop, loops *forever*
# ==============================================================================
  

    
    def run(self):
        print('starting server...')
        while(1):
            read, write, error = select.select(self.all_sockets, [], [])
            print('checking logged clients..')
            for logc in list(self.logged_name2sock.values()):
                if logc in read:
                    self.handle_msg(logc)
            print('checking new clients..')
            for newc in self.new_clients[:]:
                if newc in read:
                    self.login(newc)
            print('checking for new connections..')
            if self.server in read:
                # new client request
                sock, address = self.server.accept()
                self.new_client(sock)


def main():
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
