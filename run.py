#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 13:58:35 2026

@author: usuario
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ui_gui import start_menu

if __name__ == "__main__":
    start_menu()