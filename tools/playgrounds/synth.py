# -*- coding: utf-8 -*-
"""
Playground testing most functions of 'tools/synth.py' and some of 'tools/notes.py'.
"""

import os
import pathlib
import time

from libs import notes
from libs import synth

# ---------------------------------------------------------------------------- #
# Playground

def main():
    """ Playground entry point.
    """
    # Load the default FluidSynth library and a given SoundFont file
    path = str(pathlib.Path.cwd() / "piano.sf2")
    while not os.access(path, os.R_OK, effective_ids=True):
        print("SoundFont file %r does not exist or is unreadable" % path)
        try:
            path = input("Please specify a new SoundFont path: ")
        except EOFError:
            print("<aborted>")
            exit(1)
    piano = synth.FluidSynth().make(path)
    # Press a flat A4 then release it after 0.5 second
    key = notes.alpha_to_midi("A4", -1)
    piano.press(key)
    time.sleep(0.5)
    piano.release(key)
    # Play all the A between A7 to A0 (included)
    for i in range(7, -1, -1):
        piano.press(notes.alpha_to_midi("A%d" % i))
        time.sleep(0.15)
    # Silence all currently playing notes after 2 seconds
    time.sleep(2)
    piano.silence()
    time.sleep(0.5)
    # Play all the "blues" notes from C4 to C5 (included)
    base  = notes.alpha_to_midi("C4")
    delta = (0, 3, 5, 6, 7, 10, 12)
    piano.press(base + delta[0])
    for i in range(len(delta) - 1):
        time.sleep(0.05 * (delta[i + 1] - delta[i]) + 0.05)
        piano.press(base + delta[i + 1])
    for d in reversed(delta[:-1]):
        time.sleep(0.1)
        piano.press(base + d)
    time.sleep(2)
    piano.silence()
    time.sleep(0.5)

# Call main if main module
if __name__ == "__main__":
    main()
