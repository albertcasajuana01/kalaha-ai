#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 14:12:08 2026

@author: usuario
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import rules
from search import alphabeta_decision
from state import GameState
class Player:
    def choose_action(self, state: GameState) -> int:
        raise NotImplementedError

@dataclass
class HumanPlayer(Player):
    """
    Human chooses by typing a pit number relative to their side: 1..pits_per_side
    """
    name: str = "Human"

    def choose_action(self, state: GameState) -> int:
        pits = state.pits_per_side
        legal = rules.legal_actions(state)
        legal_rel = []
        if state.player_to_move == 0:
            legal_rel = [i + 1 for i in legal]  # pits 0..5 -> 1..6
        else:
            start = pits + 1
            legal_rel = [(i - start) + 1 for i in legal]  # pits 7..12 -> 1..6

        while True:
            raw = input(f"{self.name} (P{state.player_to_move}) choose pit {legal_rel}: ").strip()
            if not raw.isdigit():
                print("Type a number.")
                continue
            rel = int(raw)
            if rel not in legal_rel:
                print("Illegal move.")
                continue

            # map rel -> global index
            if state.player_to_move == 0:
                return rel - 1
            else:
                return (pits + 1) + (rel - 1)

@dataclass
class AIPlayer(Player):
    name: str = "AI"
    depth: int = 8
    perspective_player: int = 0  # set by UI depending on which side AI plays

    def choose_action(self, state: GameState) -> int:
        res = alphabeta_decision(state, depth=self.depth, perspective_player=self.perspective_player)
        if res.action is None:
            raise RuntimeError("AI found no action (should not happen unless terminal).")
        # Optional: debug
        # print(f"[AI] depth={self.depth} value={res.value:.2f} nodes={res.nodes}")
        return res.action