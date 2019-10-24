# -*- coding: utf-8 -*-
"""
Play our custom-format sheet music file.

Examples
--------
"""

import argparse
import heapq
import logging
import os
import pathlib
import sys
import time

from libs import synth
from libs import sheet

# ---------------------------------------------------------------------------- #
# Miscellaneous initializations

# Logging management
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ---------------------------------------------------------------------------- #
# Argument parsing

def cmdline_process():
    """ Parse the command-line and perform checks.

    Returns
    -------
    argparse.Namespace
        Parsed configuration.

    """
    # Description
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--tempo",
        type=int,
        default=120,
        help="Tempo at which to play the music")
    parser.add_argument("--soundfont",
        type=str,
        required=True,
        help="SoundFont file to use")
    parser.add_argument("--library",
        type=str,
        default="fluidsynth",
        help="Path to/name of the FluidSynth library to use")
    parser.add_argument("--audio-driver",
        type=str,
        default="pulseaudio",
        help="Audio driver to use")
    parser.add_argument("sheet",
        type=str,
        help="Sheet file to play, '-' for stdin")
    # Parse command line
    args = parser.parse_args(sys.argv[1:])
    # Check command line
    if args.tempo <= 0:
        raise RuntimeError("invalid '--tempo' value, expected a positive integer, got %d" % args.tempo)
    if not os.access(args.soundfont, os.R_OK, effective_ids=True):
        raise RuntimeError("given '--soundfont' file %r does not exist or cannot be read" % str(args.soundfont))
    args.soundfont = pathlib.Path(args.soundfont).resolve()
    if args.sheet == "-":
        args.sheet = sys.stdin.buffer
    else:
        args.sheet = open(args.sheet, "rb")  # Let it raise on problem
    # Return checked command line
    return args

# Parse and check command line
try:
    cmdline_args = cmdline_process()
except Exception as err:
    logging.critical("parsing/checking of the command line failed: %s" % err)
    exit(1)

# ---------------------------------------------------------------------------- #
# Loading

# Load piano synthesizer
try:
    piano = synth.FluidSynth(library=cmdline_args.library).make(cmdline_args.soundfont, settings={"audio.driver": cmdline_args.audio_driver})
except Exception as err:
    logging.critical("piano synthesizer loading failed: %s" % err)
    exit(1)
except KeyboardInterrupt:
    exit(0)

# Load music sheet
try:
    piece = sheet.load(cmdline_args.sheet)
except Exception as err:
    logging.critical("music sheet loading failed: %s" % err)
    exit(1)
except KeyboardInterrupt:
    exit(0)

# ---------------------------------------------------------------------------- #
# Playback

# Play each section in playing order
try:
    offset  = fractions.Fraction(0, 1)  # Offset timestamp for the current section
    current = fractions.Fraction(0, 1)  # Current timestamp
    playing = list()  # List of (timestamp, midi/None), sorted by increasing timestamp
    def play(duration, midi=None, velocity=100):
        nonlocal current
        nonlocal playing
        # Play note
        if midi is not None:
            piano.press(midi, vel=velocity)
        # Insert into playing list
        heapq.heappush(playing, (duration, midi))
    def flow(start):
        nonlocal offset
        nonlocal current
        nonlocal playing
        # Flow through time, releasing elapsed keys on the way
        while duration > 0:
            pass  # TODO: Flow
    for section in sheet.as_played():
        # Play each note while flowing through time
        for idx, row in section.iterrows():
            note, octave, accidental, start, duration = row[:5]
            # Flow through time to the start timestamp of the current note
            flow(start)
            # Now play the current note
            if note != "-":
                note     = synth.note_midi("%s%d" % (note, octave)) + accidental
                velocity = row.get("velocity", 100)
                play(duration, note, velocity)
            else:
                play(duration)
        # Update the offset timestamp, warn about any missing silence in the current measure
        pass  # TODO: Update offset timestamp
    if len(playing) > 0:
        flow(playing[-1])
except KeyboardInterrupt:
    piano.silence()
