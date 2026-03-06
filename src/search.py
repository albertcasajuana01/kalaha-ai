#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 14:10:55 2026

@author: usuario
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import rules
from state import GameState

@dataclass
class SearchResult:
    action: Optional[int]
    value: float
    nodes: int

def alphabeta_decision(state: GameState, depth: int, perspective_player: int) -> SearchResult:
    """
    Alpha-beta minimax.
    Handles extra turns naturally because `rules.result` sets player_to_move accordingly.
    `perspective_player` is the player we evaluate from (the AI).
    """
    nodes = 0

    def value(s: GameState, d: int, alpha: float, beta: float) -> float:
        nonlocal nodes
        nodes += 1

        if rules.is_terminal(s):
            return float(rules.utility_terminal(s, perspective_player))
        if d == 0:
            return float(rules.evaluate_nonterminal(s, perspective_player))

        # If it's perspective player's turn => maximize, else minimize
        maximizing = (s.player_to_move == perspective_player)

        acts = rules.legal_actions(s)
        # Move ordering (cheap): prefer actions that give extra turn (approx by simulation)
        # You can refine later; keep simple now to avoid overhead.
        # acts = _order_actions_simple(s, acts, perspective_player)

        if maximizing:
            v = float("-inf")
            for a in acts:
                v = max(v, value(rules.result(s, a), d - 1, alpha, beta))
                alpha = max(alpha, v)
                if alpha >= beta:
                    break
            return v
        else:
            v = float("inf")
            for a in acts:
                v = min(v, value(rules.result(s, a), d - 1, alpha, beta))
                beta = min(beta, v)
                if alpha >= beta:
                    break
            return v

    best_action: Optional[int] = None
    best_value = float("-inf") if state.player_to_move == perspective_player else float("inf")

    acts0 = rules.legal_actions(state)
    if not acts0:
        return SearchResult(action=None, value=0.0, nodes=nodes)

    if state.player_to_move == perspective_player:
        alpha, beta = float("-inf"), float("inf")
        for a in acts0:
            v = value(rules.result(state, a), depth - 1, alpha, beta)
            if v > best_value:
                best_value = v
                best_action = a
            alpha = max(alpha, best_value)
        return SearchResult(action=best_action, value=best_value, nodes=nodes)
    else:
        alpha, beta = float("-inf"), float("inf")
        for a in acts0:
            v = value(rules.result(state, a), depth - 1, alpha, beta)
            if v < best_value:
                best_value = v
                best_action = a
            beta = min(beta, best_value)
        return SearchResult(action=best_action, value=best_value, nodes=nodes)