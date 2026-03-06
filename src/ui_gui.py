#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 14:12:30 2026

@author: usuario
"""
import tkinter as tk
import rules
from players import AIPlayer


class KalahaGUI:

    def __init__(self, mode="hvai"):
        self.mode = mode
        self.state = rules.initial_state()

        if self.mode in ["hvai"]:
            self.ai = AIPlayer(depth=6, perspective_player=1)
        else:
            self.ai = None
        self.root = tk.Tk()
        self.root.title("Kalaha AI")

        self.buttons = []
        self.labels = []

        self.draw_board()
        self.update_board()

        self.root.mainloop()
    
    def draw_board(self):

        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        self.pits = []

        # top row (player 1)
        for i in range(12, 6, -1):
            b = tk.Button(frame, width=6, height=2,
                          command=lambda pit=i: self.play_move(pit))
            b.grid(row=0, column=13 - i)
            self.pits.append(b)

        # bottom row (player 0)
        for i in range(0, 6):
            b = tk.Button(frame, width=6, height=2,
                          command=lambda pit=i: self.play_move(pit))
            b.grid(row=2, column=i + 1)
            self.pits.append(b)

        # stores
        # Player 1 store (LEFT)
        self.store_p1 = tk.Label(frame, width=6, height=6, bg="lightgreen", font=("Arial",16))
        self.store_p1.grid(row=0, column=0, rowspan=3, padx=10)
        
        # Player 0 store (RIGHT)
        self.store_p0 = tk.Label(frame, width=6, height=6, bg="lightblue", font=("Arial",16))
        self.store_p0.grid(row=0, column=7, rowspan=3, padx=10)
        
    def update_board(self):

        board = self.state.board

        for i in range(6):
            self.pits[i].config(text=str(board[12 - i]))

        for i in range(6):
            self.pits[6 + i].config(text=str(board[i]))

        self.store_p0.config(text=str(board[6]))
        self.store_p1.config(text=str(board[13]))

    def play_move(self, pit):
    
        if rules.is_terminal(self.state):
            return
    
        if pit not in rules.legal_actions(self.state):
            return
    
        # HUMAN MOVE
        self.state = rules.result(self.state, pit)
        self.update_board()
    
        # AI MOVE
        while self.mode == "hvai" and self.state.player_to_move == 1 and not rules.is_terminal(self.state):
    
            action = self.ai.choose_action(self.state)
            self.state = rules.result(self.state, action)
            self.update_board()
            
def start_menu():

    root = tk.Tk()
    root.title("Kalaha AI")

    tk.Label(root, text="Select Game Mode", font=("Arial", 18)).pack(pady=20)

    def start_hvh():
        root.destroy()
        KalahaGUI(mode="hvh")

    def start_hvai():
        root.destroy()
        KalahaGUI(mode="hvai")

    tk.Button(root, text="Human vs Human", width=20, command=start_hvh).pack(pady=10)
    tk.Button(root, text="Human vs AI", width=20, command=start_hvai).pack(pady=10)

    root.mainloop()