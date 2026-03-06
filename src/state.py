# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class GameState:
    """
    Immutable representation of a Kalaha (Kalah) state.

    Board indexing (classic 6 pits per side):
      0..5   : Player 0 pits
      6      : Player 0 store
      7..12  : Player 1 pits
      13     : Player 1 store
    """
    board: Tuple[int, ...]          # length = 2*pits_per_side + 2
    player_to_move: int             # 0 or 1
    pits_per_side: int              # usually 6

    @property
    def n_positions(self) -> int:
        return len(self.board)

    def store_index(self, player: int) -> int:
        return self.pits_per_side if player == 0 else (2 * self.pits_per_side + 1)

    def pits_range(self, player: int) -> range:
        if player == 0:
            return range(0, self.pits_per_side)
        else:
            start = self.pits_per_side + 1
            return range(start, start + self.pits_per_side)

    def opponent(self, player: int) -> int:
        return 1 - player