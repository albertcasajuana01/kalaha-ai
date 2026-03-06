#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 14:12:46 2026

@author: usuario
"""

import pytest
from src.kalaha import rules

def test_initial_state_shape():
    s = rules.initial_state()
    assert len(s.board) == 14

def test_legal_actions_nonempty():
    s = rules.initial_state()
    acts = rules.legal_actions(s)
    assert len(acts) == 6

def test_terminal_false_initial():
    s = rules.initial_state()
    assert not rules.is_terminal(s)