# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import List, Optional, Tuple
from state import GameState

Action = int  # we represent a move as "choose pit index" in the global board indexing

def initial_state(pits_per_side: int = 6, seeds_per_pit: int = 4) -> GameState:
    """
    Creates the standard initial state.
    """
    n = 2 * pits_per_side + 2
    board = [seeds_per_pit] * n
    board[pits_per_side] = 0              # P0 store
    board[2 * pits_per_side + 1] = 0      # P1 store
    return GameState(board=tuple(board), player_to_move=0, pits_per_side=pits_per_side)

def legal_actions(state: GameState) -> List[Action]:
    """
    Legal actions are pits on current player's side with > 0 seeds.
    """
    actions: List[Action] = []
    for i in state.pits_range(state.player_to_move):
        if state.board[i] > 0:
            actions.append(i)
    return actions

def is_terminal(state: GameState) -> bool:
    """
    Terminal when either player's pits are all empty.
    """
    p0_empty = all(state.board[i] == 0 for i in state.pits_range(0))
    p1_empty = all(state.board[i] == 0 for i in state.pits_range(1))
    return p0_empty or p1_empty

def _sweep_remaining_to_stores(board: List[int], pits_per_side: int) -> None:
    """
    When terminal, move remaining seeds in pits into respective stores.
    """
    p0_store = pits_per_side
    p1_store = 2 * pits_per_side + 1

    # Sweep P0 side
    rem0 = sum(board[i] for i in range(0, pits_per_side))
    for i in range(0, pits_per_side):
        board[i] = 0
    board[p0_store] += rem0

    # Sweep P1 side
    start1 = pits_per_side + 1
    rem1 = sum(board[i] for i in range(start1, start1 + pits_per_side))
    for i in range(start1, start1 + pits_per_side):
        board[i] = 0
    board[p1_store] += rem1

def _opposite_index(i: int, pits_per_side: int) -> Optional[int]:
    """
    For classic Kalah mapping, opposite pits mirror around the stores.
    Returns None for stores.
    Example with 6 pits:
      0 <-> 12, 1 <-> 11, ..., 5 <-> 7
    """
    p0_store = pits_per_side
    p1_store = 2 * pits_per_side + 1
    if i == p0_store or i == p1_store:
        return None
    return (2 * pits_per_side) - i

def result(state: GameState, action: Action) -> GameState:
    """
    Applies a move and returns the new state.
    Must implement:
      - sowing
      - skipping opponent store
      - extra turn if last seed in own store
      - capture if last seed lands in empty pit on own side and opposite has seeds
      - terminal sweeping
    """
    if action not in legal_actions(state):
        raise ValueError(f"Illegal action {action} for player {state.player_to_move}")

    pits = state.pits_per_side
    board = list(state.board)
    player = state.player_to_move
    opp = state.opponent(player)

    p_store = state.store_index(player)
    opp_store = state.store_index(opp)

    seeds = board[action]
    board[action] = 0

    i = action
    while seeds > 0:
        i = (i + 1) % len(board)
        # skip opponent store
        if i == opp_store:
            continue
        board[i] += 1
        seeds -= 1

    last_index = i

    # Capture rule
    opp_i = _opposite_index(last_index, pits)
    if opp_i is not None:
        landed_on_own_side = last_index in state.pits_range(player)
        if landed_on_own_side and board[last_index] == 1 and board[opp_i] > 0:
            # capture opposite + last seed
            captured = board[opp_i] + board[last_index]
            board[opp_i] = 0
            board[last_index] = 0
            board[p_store] += captured

    # Extra turn?
    extra_turn = (last_index == p_store)
    next_player = player if extra_turn else opp

    new_state = GameState(board=tuple(board), player_to_move=next_player, pits_per_side=pits)

    # Terminal sweep if needed
    if is_terminal(new_state):
        board2 = list(new_state.board)
        _sweep_remaining_to_stores(board2, pits)
        new_state = GameState(board=tuple(board2), player_to_move=next_player, pits_per_side=pits)

    return new_state

def utility_terminal(state: GameState, perspective_player: int) -> int:
    """
    Terminal utility: store difference from perspective.
    """
    if not is_terminal(state):
        raise ValueError("utility_terminal called on non-terminal state")

    me = state.store_index(perspective_player)
    opp = state.store_index(state.opponent(perspective_player))
    return state.board[me] - state.board[opp]

def evaluate_nonterminal(state: GameState, perspective_player: int) -> float:
    """
    Heuristic evaluation for depth-limited search.
    Keep it fast.
    You can upgrade this later.
    """
    pits = state.pits_per_side
    me_store = state.store_index(perspective_player)
    opp_store = state.store_index(state.opponent(perspective_player))

    me_pits_sum = sum(state.board[i] for i in state.pits_range(perspective_player))
    opp_pits_sum = sum(state.board[i] for i in state.pits_range(state.opponent(perspective_player)))

    store_diff = state.board[me_store] - state.board[opp_store]
    pit_diff = me_pits_sum - opp_pits_sum

    # Simple weighted sum
    return 2.0 * store_diff + 0.5 * pit_diff