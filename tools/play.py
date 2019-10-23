# -*- coding: utf-8 -*-
"""
Play our custom-format sheet music file.

Examples
--------
"""

import argparse
import os
import pathlib
import sys

from libs import synth

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
    # Parse command line
    args = parser.parse_args(sys.argv[1:])
    # Check command line
    if args.tempo <= 0:
        raise RuntimeError("invalid '--tempo' value, expected a positive integer, got %d" % args.tempo)
    if not os.access(args.soundfont, os.R_OK, effective_ids=True):
        raise RuntimeError("given '--soundfont' file %r does not exist or cannot be read" % str(args.soundfont))
    args.soundfont = pathlib.Path(args.soundfont).resolve()
    # Return checked command line
    return args

# Parse and check command line
try:
    cmdline_args = cmdline_process()
except Exception as err:
    print("FATAL: parsing/checking of the command line failed: %s" % err)
    exit(1)

# ---------------------------------------------------------------------------- #
# Playback
