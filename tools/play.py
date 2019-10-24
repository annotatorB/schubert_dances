# -*- coding: utf-8 -*-
"""
Play our custom-format sheet music file.
"""

import argparse
import fractions
import logging
import os
import pathlib
import sys
import time

from libs import synth
from libs import sheet

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
    parser.add_argument("--sheet",
        type=str,
        default="-",
        help="Sheet file to play, '-' for stdin (by default)")
    parser.add_argument("--soundfont",
        type=str,
        required=True,
        help="SoundFont file to use")
    parser.add_argument("--speed-factor",
        type=float,
        default=1.,
        help="Non-negative speed factor")
    parser.add_argument("--library",
        type=str,
        default="fluidsynth",
        help="Path to/name of the FluidSynth library to use")
    parser.add_argument("--audio-driver",
        type=str,
        default="pulseaudio",
        help="Audio driver to use")
    # Parse command line
    args = parser.parse_args(sys.argv[1:])
    # Check command line
    if args.speed_factor <= 0:
        raise RuntimeError("invalid '--speed-factor' value, expected a positive float, got %s" % args.speed_factor)
    if not os.access(args.soundfont, os.R_OK, effective_ids=True):
        raise RuntimeError("given '--soundfont' file %r does not exist or cannot be read" % str(args.soundfont))
    args.soundfont = pathlib.Path(args.soundfont).resolve()
    if args.sheet == "-":
        args.sheet = sys.stdin.buffer
    else:
        args.sheet = open(args.sheet, "rb")  # Let it raise on problem
    # Return checked command line
    return args

# ---------------------------------------------------------------------------- #
# Synthesizer

def synthesize(piece, piano, speed_factor):
    """ Play a sheet with the given instrument at the given speed factor.

    Parameters
    ----------
    piece : :obj:`sheet.Sheet`
        Sheet to play
    piano : :obj:`synth.FluidSynth._Instance`
        Instance manager for playback
    speed_factor : float
        Positive speed factor

    """
    try:
        offset  = 0.      # Real time offset for the current section (time in each section is relative to the section start)
        current = 0.      # Current real timestamp
        playing = dict()  # Mapping of playing midi -> release real timestamp
        def play(factor, midi, duration, velocity):
            nonlocal current
            nonlocal playing
            # Play note
            piano.press(midi, vel=velocity)
            # Register release real timestamp
            playing[midi] = current + factor * duration
        def flow(factor, point, isreal=False):
            nonlocal piano
            nonlocal offset
            nonlocal current
            nonlocal playing
            # Convert start timestamp to real time
            if not isreal:
                point = offset + factor * point
            # Flow through time, releasing elapsed keys on the way
            while current < point:
                if len(playing) == 0:
                    time.sleep(point - current)
                    break
                else:
                    fnote = min(playing.items(), key=lambda x: x[1])
                    ntime = fnote[1]
                    if ntime > point:
                        time.sleep(point - current)
                        break
                    else:
                        time.sleep(ntime - current)
                        current = ntime
                        midi = fnote[0]
                        logging.debug("-- (%d): release" % midi)
                        piano.release(midi)
                        del playing[midi]
            # Done flowing
            current = point
        def wait(factor):
            nonlocal playing
            nonlocal current
            # Flow until the latest note release
            if len(playing) > 0:
                flow(factor, max(playing.values()), isreal=True)
        for section in piece.as_played():
            # Set real time offset at the beginning of this section
            offset = current
            # Gather info from section
            factor  = section.signature[0] * 60 / section.tempo / speed_factor
            silence = section.silence
            # Play each note while flowing through time
            start    = 0
            duration = 0
            for idx, row in section.notes.iterrows():
                note, octave, accidental, start, duration = row[:5]
                # Flow through time to the press timestamp of the current note
                flow(factor, start)
                # Now start playing the current note
                midi     = synth.note_midi("%s%d" % (note, octave)) + accidental
                velocity = row.get("velocity", 100)
                logging.debug("%s%d (%d): start = %s, duration = %s" % (note, octave, midi, start, duration))
                play(factor, midi, duration, velocity)
            # Wait for the final note + the final silence
            flow(factor, start + duration + silence)
        # Wait for the latest note
        wait(factor)
    finally:
        try:
            # In case of exception
            piano.silence()
        except Exception:
            pass

# ---------------------------------------------------------------------------- #
# Main function

def main():
    """ Main function.
    """
    # Logging management
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    # Parse and check command line
    try:
        args = cmdline_process()
    except Exception as err:
        logging.critical("parsing/checking of the command line failed: %s" % err)
        exit(1)
    # Load piano synthesizer
    try:
        piano = synth.FluidSynth(library=args.library).make(args.soundfont, settings={"audio.driver": args.audio_driver})
    except Exception as err:
        logging.critical("piano synthesizer loading failed: %s" % err)
        exit(1)
    # Load music sheet
    try:
        piece = sheet.load(args.sheet)
    except Exception as err:
        logging.critical("music sheet loading failed: %s" % err)
        exit(1)
    # Play the piece as instructed
    synthesize(piece, piano, args.speed_factor)

# Call main if main module
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
