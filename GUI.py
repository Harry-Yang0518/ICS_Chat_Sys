#!/usr/bin/env python3
# -*- coding: utf-8 -*-

helpTextString = r'''
- To send a message, type the message in the text box at the bottom of the window and press the "SEND" button.
Playing Gobang:
- The Gobang game is integrated into this chat platform. Here's how you can interact with the game:
    - To start viewing the game interface, press the "Game" button. This will display the chessboard where you can play Gobang.
    - To invite another user to play the game, type the command '/game start <username>'. Replace '<username>' with the actual username of the person you want to play with.
    - To place a piece on the board, type '/game move <x> <y>'. Replace '<x>' and '<y>' with the coordinates where you want to place your piece. The top-left corner is (0,0).
    - Alternatively, you can click directly on the board where you want to place your piece instead of typing the command.
    - If you wish to quit the current game session, type '/game quit'. This command will end the game.
'''


# import all the required  modules
import threading
import select
from tkinter import *
from tkinter import font
from tkinter import ttk
from tkinter import messagebox
from chat_utils import *
import json
import re
import time
import os
from tkinter import messagebox
import chessboard
# GUI class for the chat



class GUI:
    # constructor method
    def __init__(self, send, recv, sm, s):
        # chat window which is currently hidden
        self.Window = Tk()
        self.Window.withdraw()
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = ""
        self.system_msg = ""
        self.player = 0
        self.chestboard = chessboard.Board()
        self.boardWindow = None



    def login(self):
        # login window
        self.login = Toplevel()
        # set the title
        self.login.title("Gobang game")
        self.login.resizable(width=False,
                             height=False)
        self.login.configure(width=500,
                             height=400)
        
        self.pls = Label(self.login,
                         text="Gobang game",
                         justify=CENTER,
                         font="Helvetica 14 bold")

        self.pls.place(relheight=0.15,
                       relx=0.4,
                       rely=0.07)
        
        self.labelName = Label(self.login,
                               text="Username: ",
                               font="Helvetica 12")

        self.labelName.place(relheight=0.2,
                             relx=0.1,
                             rely=0.2)

        
        self.entryName = Entry(self.login,
                               font="Helvetica 14")

        self.entryName.place(relwidth=0.4,
                             relheight=0.12,
                             relx=0.35,
                             rely=0.2)

        self.labelPasswd = Label(self.login,
                               text="Password: ",
                               font="Helvetica 12")

        self.labelPasswd.place(relheight=0.2,
                             relx=0.1,
                             rely=0.4)

        
        self.entryPasswd = Entry(self.login,
                               font="Helvetica 14")

        self.entryPasswd.place(relwidth=0.4,
                             relheight=0.12,
                             relx=0.35,
                             rely=0.4)
        
        self.entryName.focus()
        
      
        self.log = Button(self.login,
                         text="Login",
                         font="Helvetica 14 bold",
                         command=lambda: self.goAhead(self.entryName.get(),self.entryPasswd.get()))
        self.signin = Button(self.login,
                         text="Register",
                         font="Helvetica 14 bold",
                         command=lambda: self.signIn(self.entryName.get(),self.entryPasswd.get()))

        self.log.place(relx=0.4,
                      rely=0.75)
        self.signin.place(relx=0.6,
                        rely=0.75)
        self.Window.mainloop()

    def signIn(self, username, password):
        """
        This function handles the sign-in process for a user.
        """

        # Validate username
        if not self.is_valid_username(username):
            messagebox.showerror('Error', 'Username contains illegal characters (can only use alphabets, numbers and underscore)')
            return

        # Send sign-in request
        self.process_sign_in(username, password)

    def is_valid_username(self, username):
        """
        Checks if the provided username is valid.
        """
        return re.match(r'^[a-zA-Z0-9_]+$', username) is not None

    def process_sign_in(self, username, password):
        """
        Processes the sign-in request to the server and handles the response.
        """
        msg = json.dumps({"action": "signin", "name": username, "passwd": password})
        self.send(msg)
        response = json.loads(self.recv())

        # Handle response
        if response["status"] == 'ok':
            messagebox.showinfo('Success', 'Sign in successfully')
        else:
            messagebox.showerror('Error', response["message"])



        
    def goAhead(self, name,passwd):
        if len(name) > 0:
            msg = json.dumps({"action": "login", "name": name, "passwd": passwd})
            self.send(msg)
            response = json.loads(self.recv())
            if response["status"] == 'ok':
                self.login.destroy()
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)
                self.layout(name)
                self.textCons.config(state=NORMAL)
                
                self.textCons.insert(END, menu + "\n\n")
                self.textCons.config(state=DISABLED)
                self.textCons.see(END)
                
                process = threading.Thread(target=self.proc)
                process.daemon = True
                process.start()
            else:
                messagebox.showerror('Error', response["message"])
        

    
    def layout(self, name):
        self.name = name
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width=False, height=False)
        self.Window.configure(width=600, height=550, bg="#D3D3D3")  

        self.labelHead = Label(self.Window, bg="#D3D3D3", fg="#2E2E2E", text=self.name, font="Times 15 bold", pady=5)
        self.labelHead.place(relwidth=1)

        self.line = Label(self.Window, width=450, bg="#546E7A")
        self.line.place(relwidth=1, rely=0.07, relheight=0.012)

        self.textCons = Text(self.Window, width=20, height=2, bg="#D3D3D3", fg="#2E2E2E", font="Times 15", padx=5, pady=5)
        self.textCons.place(relheight=0.745, relwidth=1, rely=0.08)
        self.textCons.tag_config('b', font='Times 15 bold')
        self.textCons.tag_config('i', font='Times 15 italic')

        self.labelBottom = Label(self.Window, bg="#546E7A", height=80)
        self.labelBottom.place(relwidth=1, rely=0.825)

        self.entryMsg = Entry(self.labelBottom, bg="#2C3E50", fg="#EAECEE", font="Times 13")
        self.entryMsg.place(relwidth=0.5, relheight=0.06, rely=0.008, relx=0.011)
        self.entryMsg.focus()

        self.buttonPlus = Button(self.labelBottom, text="Game", font="Times 20 bold", width=20, bg="#546E7A", command=lambda: self.openGame())
        self.buttonPlus.place(relx=0.52, rely=0.008, relheight=0.029, relwidth=0.22)






        def help():
            helpWindow = Toplevel(self.Window)
            helpWindow.config(height=350,width=600)
            helpWindow.title("Help")
            helpText = Text(helpWindow, width=20, height=2, bg="#17202A", fg="#EAECEE", font="Helvetica 14", padx=5, pady=5)
            helpText.place(relheight=1,relwidth=1)
            helpText.insert(END, helpTextString)
            helpText.config(state=DISABLED)

        self.buttonHelp = Button(self.labelBottom,
                                text="Need Help?",
                                font="Times 20 bold",
                                width=20,
                                bg="#ABB2B9",
                                command=lambda: help())

        self.buttonHelp.place(relx=0.52,rely = 0.039,relheight=0.029,relwidth=0.22)
        self.buttonMsg = Button(self.labelBottom,
                                text="SEND",
                                font="Times 30 bold",
                                width=20,
                                bg="#ABB2B9",
                                command=lambda: self.sendButton(self.entryMsg.get()))

        self.buttonMsg.place(relx=0.75,
                             rely=0.008,
                             relheight=0.06,
                             relwidth=0.24)


        self.textCons.config(cursor="arrow")
        

   
        scrollbar = Scrollbar(self.textCons)

        scrollbar.place(relheight=1,
                        relx=0.974)

        scrollbar.config(command=self.textCons.yview)

        self.textCons.config(state=DISABLED)


    def parseOutput(self, msg):
        """
        Processes the input message by replacing specific sequences with timestamps,
        handling special character replacements, and applying text styles like
        bold and italic. The processed message is then inserted into a text widget
        with appropriate styling.
        """

        # Replace special sequences with time and date
        msg = re.sub(r'\\t', time.strftime("%H:%M:%S", time.localtime()), msg)
        msg = re.sub(r'\\d', time.strftime("%b %d %Y", time.localtime()), msg)

        # Replace '\*' with a temporary placeholder and then back to '*'
        temp_char = chr(27)
        msg = msg.replace('\\*', temp_char)

        # Apply text styling (bold and italic) and insert into GUI element
        is_bold = False
        for segment in re.split(r'\*\*', msg):
            if is_bold:
                self.insert_styled_text(segment, 'b', temp_char)
                is_bold = False
            else:
                self.insert_styled_text(segment, None, temp_char)
                is_bold = True

        # Append a newline at the end
        self.textCons.insert(END, '\n')
        return msg

    def insert_styled_text(self, text, style, temp_char):
        """
        Inserts text into the text widget with specified style, handling the replacement
        of the temporary character used for special formatting.
        """
        is_italic = False
        for sub_segment in re.split(r'\*', text):
            # Replace temporary character back to '*'
            sub_segment = sub_segment.replace(temp_char, '*')
            if style == 'b' or (style is None and is_italic):
                self.textCons.insert(END, sub_segment, 'i' if is_italic else 'b')
            else:
                self.textCons.insert(END, sub_segment)
            is_italic = not is_italic


    def sendButton(self, msg):
        
        self.my_msg = msg
        self.entryMsg.delete(0, END)
        self.textCons.config(state=NORMAL)
        self.parseOutput(msg)
        self.textCons.config(state=DISABLED)
        self.textCons.see(END)

    def proc(self):
        while True:
            read, write, error = select.select([self.socket], [], [], 0)
            peer_msg = []
            
            if self.socket in read:
                peer_msg = self.recv()
            if len(self.my_msg) > 0 or len(peer_msg) > 0:
                
                self.system_msg = self.sm.proc(self.my_msg, peer_msg)
                self.my_msg = ""
                self.textCons.config(state=NORMAL)
                
                if self.boardWindow:
                    self.updateChessboard()
                if 'game ended' in self.system_msg:
                    if self.boardWindow:
                        self.closeGame()
                self.parseOutput(self.system_msg+'\n')
                self.textCons.config(state=DISABLED)
                self.textCons.see(END)

    def closeGame(self):
        self.boardWindow.destroy()
        self.boardWindow = None

    def openGame(self):
        if not self.sm.game_peer:
            messagebox.showerror("Error", "Not in a game right now")
            return

        if not self.boardWindow:
            self.initializeGameWindow()
            self.updateChessboard()

    def initializeGameWindow(self):
        self.boardWindow = Toplevel(self.Window)
        self.boardWindow.protocol("WM_DELETE_WINDOW", self.closeGame)
        self.myCanvas = Canvas(self.boardWindow, bg="#e6e6e6", height=450, width=450)  # 更亮的背景色
        self.myCanvas.bind("<Button-1>", self.on_click)
        self.myCanvas.pack()
        self.chessboardInit()

    def on_click(self, event):
        p = lambda t: int((t-25+22.222)//44.444)
        x, y = p(event.x), p(event.y)
        self.entryMsg.delete(0, END)
        self.entryMsg.insert(END, "/game move " + str(x) + " " + str(y))

    def chessboardInit(self):
        self.myCanvas.delete("all")
        for i in range(10):
            
            self.myCanvas.create_line(25, 25 + i * 44.444, 425, 25 + i * 44.444, fill='#808080', width=1)
            self.myCanvas.create_line(25 + i * 44.444, 25, 25 + i * 44.444, 425, fill='#808080', width=1)

    def addChess(self, x, y, color):
        self.myCanvas.create_oval(25+x*44.444-15, 25+y*44.444-15, 25+x*44.444+15, 25+y*44.444+15, fill=color, outline=color)

    def updateChessboard(self):
        if self.sm.game_peer:
            self.boardWindow.title("Game with " + self.sm.game_peer)
        self.chessboardInit()
        for i in range(10):
            for j in range(10):
                if self.sm.chessboard[i][j] == 0:
                    self.addChess(i, j, self.sm.colors[self.sm.initiating])
                elif self.sm.chessboard[i][j] == 1:
                    self.addChess(i, j, self.sm.colors[1-self.sm.initiating])

    def run(self):
        self.login()


# create a GUI class object
if __name__ == "__main__":
    # g = GUI()
    pass
