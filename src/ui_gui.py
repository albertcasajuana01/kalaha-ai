#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kalaha GUI  —  animated interface.

Animations
----------
- Seed-by-seed sowing: each pit lights up as a seed lands, count updates live
- "AI is thinking..." status while alpha-beta runs
- Capture flash: pit pulses red when seeds are captured
- Extra-turn banner: brief gold flash + message
- All animations are non-blocking (uses root.after / root.update)
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import rules
from players import AIPlayer

# ── Colour palette ───────────────────────────────────────────────────────────
BG          = "#1a1a2e"
BOARD_BG    = "#16213e"
P0_COLOR    = "#c84b31"
P0_LIGHT    = "#e86b51"
P1_COLOR    = "#2b6cb0"
P1_LIGHT    = "#4a90d9"
ACTIVE_RING = "#f5c518"
CAPTURE_CLR = "#ff2244"
EXTURN_CLR  = "#44ffaa"
DISABLED_FG = "#44445a"
TEXT_LIGHT  = "#e8e8f0"
TEXT_DIM    = "#7070a0"

SOWING_DELAY_MS  = 180   # ms between each seed landing
FLASH_DURATION   = 220   # ms a flash stays on
CAPTURE_FLASHES  = 3     # number of blink cycles for capture


class KalahaGUI:

    def __init__(self, mode="hvai", player0_name="You",
                 player1_name="AI", ai_depth=6):
        self.mode          = mode
        self.player0_name  = player0_name
        self.player1_name  = player1_name
        self.state         = rules.initial_state()
        self.ai            = AIPlayer(depth=ai_depth, perspective_player=1) if mode == "hvai" else None
        self._input_locked = False   # prevents clicks during animation

        self.root = tk.Tk()
        self.root.title("Kalaha")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.f_title  = tkfont.Font(family="Georgia", size=22, weight="bold")
        self.f_header = tkfont.Font(family="Georgia", size=12, weight="bold")
        self.f_pit    = tkfont.Font(family="Courier",  size=17, weight="bold")
        self.f_store  = tkfont.Font(family="Courier",  size=24, weight="bold")
        self.f_status = tkfont.Font(family="Georgia",  size=12, slant="italic")
        self.f_small  = tkfont.Font(family="Georgia",  size=10)

        self._build_ui()
        self.update_board()
        self.root.mainloop()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG, padx=28, pady=16)
        outer.pack()

        tk.Label(outer, text="K A L A H A", font=self.f_title,
                 bg=BG, fg=TEXT_LIGHT).pack(pady=(6, 2))

        self.status_var = tk.StringVar()
        self.status_lbl = tk.Label(outer, textvariable=self.status_var,
                                   font=self.f_status, bg=BG, fg=ACTIVE_RING, width=52)
        self.status_lbl.pack(pady=(0, 10))

        board_frame = tk.Frame(outer, bg=BOARD_BG, padx=14, pady=12,
                               bd=2, relief="ridge")
        board_frame.pack()

        # Player 1 header
        p1_row = tk.Frame(board_frame, bg=BOARD_BG)
        p1_row.grid(row=0, column=0, columnspan=9, sticky="ew", pady=(0, 6))
        self.p1_arrow = tk.Label(p1_row, text="▼", font=self.f_small, bg=BOARD_BG, fg=P1_COLOR)
        self.p1_arrow.pack(side="left", padx=(2, 4))
        tk.Label(p1_row, text=f"{self.player1_name}", font=self.f_header,
                 bg=BOARD_BG, fg=P1_LIGHT).pack(side="left")
        tk.Label(p1_row, text="  (top row · plays right → left)",
                 font=self.f_small, bg=BOARD_BG, fg=TEXT_DIM).pack(side="left")
        self.p1_seeds_var = tk.StringVar()
        tk.Label(p1_row, textvariable=self.p1_seeds_var, font=self.f_small,
                 bg=BOARD_BG, fg=TEXT_DIM).pack(side="right", padx=6)

        grid = tk.Frame(board_frame, bg=BOARD_BG)
        grid.grid(row=1, column=0, columnspan=9)

        # Stores
        self.store_p1 = tk.Label(grid, width=6, height=6, bg=P1_COLOR,
                                  fg=TEXT_LIGHT, font=self.f_store, relief="groove", bd=3, text="0")
        self.store_p1.grid(row=0, column=0, rowspan=2, padx=(0, 10), pady=4)
        tk.Label(grid, text=f"{self.player1_name}\nStore", font=self.f_small,
                 bg=BOARD_BG, fg=P1_LIGHT).grid(row=2, column=0, pady=(2, 0))

        self.store_p0 = tk.Label(grid, width=6, height=6, bg=P0_COLOR,
                                  fg=TEXT_LIGHT, font=self.f_store, relief="groove", bd=3, text="0")
        self.store_p0.grid(row=0, column=8, rowspan=2, padx=(10, 0), pady=4)
        tk.Label(grid, text=f"{self.player0_name}\nStore", font=self.f_small,
                 bg=BOARD_BG, fg=P0_LIGHT).grid(row=2, column=8, pady=(2, 0))

        # Pit number labels
        for col in range(6):
            tk.Label(grid, text=str(6 - col), font=self.f_small,
                     bg=BOARD_BG, fg=P1_LIGHT).grid(row=3, column=col + 1)
        for col in range(6):
            tk.Label(grid, text=str(col + 1), font=self.f_small,
                     bg=BOARD_BG, fg=P0_LIGHT).grid(row=4, column=col + 1)

        # Player 1 pits (top row, board indices 12→7)
        self.p1_pits = []
        for col, board_idx in enumerate(range(12, 6, -1)):
            b = tk.Button(grid, width=5, height=2, font=self.f_pit,
                          bg=P1_COLOR, fg=TEXT_LIGHT, activebackground=P1_LIGHT,
                          relief="raised", bd=3,
                          command=lambda pit=board_idx: self.play_move(pit))
            b.grid(row=0, column=col + 1, padx=3, pady=3)
            self.p1_pits.append((board_idx, b))

        # Player 0 pits (bottom row, board indices 0→5)
        self.p0_pits = []
        for col, board_idx in enumerate(range(0, 6)):
            b = tk.Button(grid, width=5, height=2, font=self.f_pit,
                          bg=P0_COLOR, fg=TEXT_LIGHT, activebackground=P0_LIGHT,
                          relief="raised", bd=3,
                          command=lambda pit=board_idx: self.play_move(pit))
            b.grid(row=1, column=col + 1, padx=3, pady=3)
            self.p0_pits.append((board_idx, b))

        # Player 0 footer
        p0_row = tk.Frame(board_frame, bg=BOARD_BG)
        p0_row.grid(row=2, column=0, columnspan=9, sticky="ew", pady=(8, 0))
        self.p0_arrow = tk.Label(p0_row, text="▲", font=self.f_small, bg=BOARD_BG, fg=P0_COLOR)
        self.p0_arrow.pack(side="left", padx=(2, 4))
        tk.Label(p0_row, text=f"{self.player0_name}", font=self.f_header,
                 bg=BOARD_BG, fg=P0_LIGHT).pack(side="left")
        tk.Label(p0_row, text="  (bottom row · plays left → right)",
                 font=self.f_small, bg=BOARD_BG, fg=TEXT_DIM).pack(side="left")
        self.p0_seeds_var = tk.StringVar()
        tk.Label(p0_row, textvariable=self.p0_seeds_var, font=self.f_small,
                 bg=BOARD_BG, fg=TEXT_DIM).pack(side="right", padx=6)

        # Legend + New Game
        bottom = tk.Frame(outer, bg=BG)
        bottom.pack(pady=(10, 0), fill="x")
        legend = tk.Frame(bottom, bg=BG)
        legend.pack(side="left")
        for color, text in [(ACTIVE_RING, "Gold = your turn"),
                            (P0_COLOR, self.player0_name),
                            (P1_COLOR, self.player1_name)]:
            tk.Label(legend, text="●", fg=color, bg=BG, font=self.f_small).pack(side="left", padx=(4, 1))
            tk.Label(legend, text=text, fg=TEXT_DIM, bg=BG, font=self.f_small).pack(side="left", padx=(0, 8))
        ng = tk.Label(bottom, text="↺  New Game", font=self.f_small,
                      bg=ACTIVE_RING, fg="#1a1a2e",
                      relief="flat", padx=14, pady=6, cursor="hand2")
        ng.pack(side="right")
        ng.bind("<Button-1>", lambda e: self._new_game())
        ng.bind("<Enter>",    lambda e: ng.config(bg="#d4a800"))
        ng.bind("<Leave>",    lambda e: ng.config(bg=ACTIVE_RING))

    # ── Board rendering ──────────────────────────────────────────────────────

    def _widget_for(self, board_idx):
        """Return the Button widget for a given board index, or None for stores."""
        pits = self.state.pits_per_side
        store0 = pits
        store1 = 2 * pits + 1
        if board_idx == store0:
            return self.store_p0
        if board_idx == store1:
            return self.store_p1
        for idx, btn in self.p0_pits:
            if idx == board_idx:
                return btn
        for idx, btn in self.p1_pits:
            if idx == board_idx:
                return btn
        return None

    def _player_color(self, board_idx):
        pits = self.state.pits_per_side
        if board_idx <= pits:
            return P0_COLOR
        return P1_COLOR

    def update_board(self, board=None):
        """Refresh all widget labels/colours from current state (or a supplied board list)."""
        b = board if board is not None else self.state.board
        player   = self.state.player_to_move
        terminal = rules.is_terminal(self.state)
        legal    = set(rules.legal_actions(self.state)) if not terminal else set()

        self.store_p0.config(text=str(b[6]))
        self.store_p1.config(text=str(b[13]))
        self.p0_seeds_var.set(f"seeds in pits: {sum(b[i] for i in range(0, 6))}")
        self.p1_seeds_var.set(f"seeds in pits: {sum(b[i] for i in range(7, 13))}")

        for board_idx, btn in self.p1_pits:
            active = (player == 1) and (board_idx in legal) and not terminal and not self._input_locked
            btn.config(
                text=str(b[board_idx]),
                bg=ACTIVE_RING if active else P1_COLOR,
                fg="#1a1a2e" if active else TEXT_LIGHT,
                state="normal" if active else "disabled",
                disabledforeground=DISABLED_FG,
                relief="raised" if b[board_idx] > 0 else "flat",
            )
        for board_idx, btn in self.p0_pits:
            active = (player == 0) and (board_idx in legal) and not terminal and not self._input_locked
            btn.config(
                text=str(b[board_idx]),
                bg=ACTIVE_RING if active else P0_COLOR,
                fg="#1a1a2e" if active else TEXT_LIGHT,
                state="normal" if active else "disabled",
                disabledforeground=DISABLED_FG,
                relief="raised" if b[board_idx] > 0 else "flat",
            )

        self.p0_arrow.config(fg=ACTIVE_RING if player == 0 and not terminal and not self._input_locked else P0_COLOR)
        self.p1_arrow.config(fg=ACTIVE_RING if player == 1 and not terminal and not self._input_locked else P1_COLOR)

        if terminal:
            s0, s1 = b[6], b[13]
            if s0 > s1:
                msg = f"🏆  {self.player0_name} wins!  ({s0} – {s1})"
            elif s1 > s0:
                msg = f"🏆  {self.player1_name} wins!  ({s1} – {s0})"
            else:
                msg = f"🤝  Draw!  ({s0} apiece)"
            self.status_var.set(msg)
            self.status_lbl.config(fg=ACTIVE_RING)
        elif not self._input_locked:
            name  = self.player0_name if player == 0 else self.player1_name
            color = P0_LIGHT if player == 0 else P1_LIGHT
            self.status_var.set(f"↩  {name}'s turn — click a highlighted pit")
            self.status_lbl.config(fg=color)

    # ── Animation helpers ────────────────────────────────────────────────────

    def _flash_widget(self, widget, flash_color, restore_color, restore_fg=None, count=1, done_cb=None):
        """Blink a widget between flash_color and restore_color `count` times."""
        steps = []
        for _ in range(count):
            steps.append((flash_color, TEXT_LIGHT))
            steps.append((restore_color, restore_fg or TEXT_LIGHT))

        def step(i=0):
            if i >= len(steps):
                if done_cb:
                    done_cb()
                return
            bg, fg = steps[i]
            widget.config(bg=bg, fg=fg)
            self.root.after(FLASH_DURATION, lambda: step(i + 1))

        step()

    def _animate_sow(self, source_idx, board_before, board_after, player, done_cb):
        """
        Animate seed sowing: highlight each pit as a seed lands, update its count.
        board_before / board_after are plain lists.
        """
        pits      = self.state.pits_per_side
        n         = len(board_before)
        opp_store = self.state.store_index(1 - player)

        # Build ordered list of positions that were incremented
        seeds     = board_before[source_idx]
        sequence  = []
        i         = source_idx
        for _ in range(seeds):
            i = (i + 1) % n
            if i == opp_store:
                i = (i + 1) % n
            sequence.append(i)

        # Working copy we mutate during animation
        animated_board = list(board_before)
        animated_board[source_idx] = 0   # picked up

        p_store = self.state.store_index(player)
        p_color = P0_COLOR if player == 0 else P1_COLOR
        p_light = P0_LIGHT if player == 0 else P1_LIGHT
        store_w = self.store_p0 if player == 0 else self.store_p1

        # Highlight source pit as empty immediately
        src_widget = self._widget_for(source_idx)
        if src_widget:
            src_widget.config(text="0", bg=DISABLED_FG, fg=TEXT_LIGHT)

        self.update_board(board=animated_board)

        def drop_seed(step_idx=0):
            if step_idx >= len(sequence):
                done_cb()
                return

            pos    = sequence[step_idx]
            widget = self._widget_for(pos)
            animated_board[pos] += 1
            count_now = animated_board[pos]

            # Update text
            if widget:
                is_store = (pos == p_store or pos == opp_store)
                if is_store:
                    widget.config(text=str(count_now),
                                  bg="#ffdd55" if pos == p_store else
                                     (P1_COLOR if player == 0 else P0_COLOR),
                                  fg="#1a1a2e")
                else:
                    widget.config(text=str(count_now), bg="#ffdd55", fg="#1a1a2e")

                # Restore colour after flash
                def restore(w=widget, cnt=count_now, p=pos):
                    is_s = (p == p_store or p == opp_store)
                    if is_s:
                        orig_bg = p_color if p == p_store else (P1_COLOR if player == 0 else P0_COLOR)
                        w.config(bg=orig_bg, fg=TEXT_LIGHT)
                    else:
                        orig_col = p_color if p in range(0, pits + 1) else (P1_COLOR if player == 0 else P0_COLOR)
                        # determine which player owns this pit
                        if p < pits:
                            orig_col = P0_COLOR
                        elif p > pits:
                            orig_col = P1_COLOR
                        w.config(bg=orig_col, fg=TEXT_LIGHT, text=str(cnt))

                self.root.after(FLASH_DURATION, restore)

            # Update seed counters in header
            self.p0_seeds_var.set(f"seeds in pits: {sum(animated_board[i] for i in range(0, pits))}")
            self.p1_seeds_var.set(f"seeds in pits: {sum(animated_board[i] for i in range(pits+1, 2*pits+1))}")

            self.root.after(SOWING_DELAY_MS, lambda: drop_seed(step_idx + 1))

        drop_seed()

    def _animate_capture(self, last_idx, opp_idx, done_cb):
        """Flash the capture pits red before finalising."""
        w_last = self._widget_for(last_idx)
        w_opp  = self._widget_for(opp_idx)

        flashes_left = [CAPTURE_FLASHES * 2]

        def blink():
            flashes_left[0] -= 1
            on = (flashes_left[0] % 2 == 0)
            c  = CAPTURE_CLR if on else DISABLED_FG
            if w_last: w_last.config(bg=c)
            if w_opp:  w_opp.config(bg=c)
            if flashes_left[0] > 0:
                self.root.after(FLASH_DURATION, blink)
            else:
                done_cb()

        blink()

    # ── Move logic with animation ────────────────────────────────────────────

    def play_move(self, pit):
        if self._input_locked:
            return
        if rules.is_terminal(self.state):
            return
        if pit not in rules.legal_actions(self.state):
            return

        self._input_locked = True
        self.update_board()  # grey out all pits immediately

        board_before = list(self.state.board)
        player       = self.state.player_to_move
        new_state    = rules.result(self.state, pit)
        board_after  = list(new_state.board)

        # Detect capture: did any pit go to 0 that was sowed into (on player side)?
        pits     = self.state.pits_per_side
        opp_i    = rules._opposite_index
        capture_pit  = None
        capture_opp  = None
        for idx in self.state.pits_range(player):
            opp = opp_i(idx, pits)
            if (board_before[idx] == 0 and board_after[idx] == 0 and
                    board_before[opp] > 0 and board_after[opp] == 0 and
                    board_before[self.state.store_index(player)] < board_after[self.state.store_index(player)]):
                # seeds were captured from this pit
                # figure out which pit was the landing pit: the one that was empty before sow
                # and is now also empty (captured)
                capture_pit = idx
                capture_opp = opp
                break

        extra_turn = (new_state.player_to_move == player)

        def after_sow():
            if capture_pit is not None:
                self.status_var.set("💥  Capture!")
                self.status_lbl.config(fg=CAPTURE_CLR)

                def after_capture():
                    self.state = new_state
                    if extra_turn:
                        self._show_extra_turn_banner(lambda: self._finish_move())
                    else:
                        self._finish_move()

                self._animate_capture(capture_pit, capture_opp, after_capture)
            else:
                self.state = new_state
                if extra_turn:
                    self._show_extra_turn_banner(lambda: self._finish_move())
                else:
                    self._finish_move()

        self._animate_sow(pit, board_before, board_after, player, done_cb=after_sow)

    def _show_extra_turn_banner(self, done_cb):
        name = self.player0_name if self.state.player_to_move == 0 else self.player1_name
        self.status_var.set(f"✨  Extra turn for {name}!")
        self.status_lbl.config(fg=EXTURN_CLR)
        self.root.after(900, done_cb)

    def _finish_move(self):
        """Called after animations complete. Check terminal, then hand to AI if needed."""
        self.update_board()
        if rules.is_terminal(self.state):
            self._input_locked = False
            self.update_board()
            return

        if self.mode == "hvai" and self.state.player_to_move == 1:
            self._do_ai_turn()
        else:
            self._input_locked = False
            self.update_board()

    def _do_ai_turn(self):
        """Compute AI move in a thread, then animate it."""
        self.status_var.set(f"🤖  {self.player1_name} is thinking…")
        self.status_lbl.config(fg=P1_LIGHT)
        self.root.update()

        result_holder = [None]

        def compute():
            result_holder[0] = self.ai.choose_action(self.state)

        t = threading.Thread(target=compute, daemon=True)
        t.start()

        def wait_for_ai():
            if t.is_alive():
                self.root.after(50, wait_for_ai)
                return
            # AI done
            action = result_holder[0]
            if action is None:
                self._input_locked = False
                self.update_board()
                return
            self._play_ai_action(action)

        self.root.after(50, wait_for_ai)

    def _play_ai_action(self, pit):
        board_before = list(self.state.board)
        player       = self.state.player_to_move
        new_state    = rules.result(self.state, pit)
        board_after  = list(new_state.board)

        pits = self.state.pits_per_side
        opp_i = rules._opposite_index
        capture_pit = capture_opp = None
        for idx in self.state.pits_range(player):
            opp = opp_i(idx, pits)
            if (board_before[idx] == 0 and board_after[idx] == 0 and
                    board_before[opp] > 0 and board_after[opp] == 0 and
                    board_before[self.state.store_index(player)] < board_after[self.state.store_index(player)]):
                capture_pit = idx
                capture_opp = opp
                break

        extra_turn = (new_state.player_to_move == player)

        # Show which pit AI chose
        w = self._widget_for(pit)
        if w:
            w.config(bg="#ffdd55", fg="#1a1a2e")
        self.status_var.set(f"🤖  {self.player1_name} picks pit {pit - pits}…")
        self.status_lbl.config(fg=P1_LIGHT)

        def after_highlight():
            def after_sow():
                if capture_pit is not None:
                    self.status_var.set("💥  AI captures!")
                    self.status_lbl.config(fg=CAPTURE_CLR)

                    def after_capture():
                        self.state = new_state
                        if extra_turn:
                            self._show_extra_turn_banner(lambda: self._after_ai_move())
                        else:
                            self._after_ai_move()

                    self._animate_capture(capture_pit, capture_opp, after_capture)
                else:
                    self.state = new_state
                    if extra_turn:
                        self._show_extra_turn_banner(lambda: self._after_ai_move())
                    else:
                        self._after_ai_move()

            self._animate_sow(pit, board_before, board_after, player, done_cb=after_sow)

        self.root.after(400, after_highlight)

    def _after_ai_move(self):
        self.update_board()
        if rules.is_terminal(self.state):
            self._input_locked = False
            self.update_board()
            return
        if self.state.player_to_move == 1:
            # AI gets another extra turn
            self._do_ai_turn()
        else:
            self._input_locked = False
            self.update_board()

    def _new_game(self):
        self._input_locked = False
        self.state = rules.initial_state()
        self.update_board()


# ── Start menu ───────────────────────────────────────────────────────────────

def start_menu():
    root = tk.Tk()
    root.title("Kalaha")
    root.configure(bg=BG)
    root.resizable(False, False)

    f_title = tkfont.Font(family="Georgia", size=26, weight="bold")
    f_sub   = tkfont.Font(family="Georgia", size=12, slant="italic")
    f_btn   = tkfont.Font(family="Georgia", size=14, weight="bold")
    f_small = tkfont.Font(family="Georgia", size=10)

    outer = tk.Frame(root, bg=BG, padx=70, pady=40)
    outer.pack()

    tk.Label(outer, text="K A L A H A", font=f_title, bg=BG, fg=TEXT_LIGHT).pack(pady=(0, 4))
    tk.Label(outer, text="the ancient seed game", font=f_sub, bg=BG, fg=TEXT_DIM).pack(pady=(0, 28))

    tk.Label(outer, text="AI difficulty:", font=f_small, bg=BG, fg=TEXT_DIM).pack(anchor="w")
    depth_var = tk.IntVar(value=6)
    diff_row = tk.Frame(outer, bg=BG)
    diff_row.pack(anchor="w", pady=(2, 18))
    for label, val in [("Easy (4)", 4), ("Medium (6)", 6), ("Hard (8)", 8)]:
        tk.Radiobutton(diff_row, text=label, variable=depth_var, value=val,
                       font=f_small, bg=BG, fg=TEXT_LIGHT,
                       selectcolor=BOARD_BG, activebackground=BG
                       ).pack(side="left", padx=(0, 14))

    def _darken(hex_color):
        r = max(0, int(hex_color[1:3], 16) - 30)
        g = max(0, int(hex_color[3:5], 16) - 30)
        b = max(0, int(hex_color[5:7], 16) - 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _accent_btn(text, cmd, color):
        # Coloured border wrapper (Label respects bg on macOS, Button does not)
        wrapper = tk.Label(outer, bg=color, padx=3, pady=3, cursor="hand2")
        wrapper.pack(fill="x", pady=6)
        inner = tk.Label(wrapper, text=text, font=f_btn,
                         bg=color, fg="#ffffff",
                         relief="flat", padx=10, pady=12,
                         cursor="hand2")
        inner.pack(fill="x")
        for w in (wrapper, inner):
            w.bind("<Button-1>", lambda e: cmd())
            w.bind("<Enter>",    lambda e: [wrapper.config(bg=_darken(color)),
                                            inner.config(bg=_darken(color))])
            w.bind("<Leave>",    lambda e: [wrapper.config(bg=color),
                                            inner.config(bg=color)])

    def start_hvh():
        root.destroy()
        KalahaGUI(mode="hvh", player0_name="Player 1", player1_name="Player 2")

    def start_hvai():
        root.destroy()
        KalahaGUI(mode="hvai", player0_name="You", player1_name="AI",
                  ai_depth=depth_var.get())

    _accent_btn("⚔  Human vs Human", start_hvh, P0_COLOR)
    _accent_btn("🤖  Human vs AI",    start_hvai, P1_COLOR)

    root.mainloop()