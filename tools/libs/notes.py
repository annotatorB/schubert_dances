# -*- coding: utf-8 -*-
"""
Convertion between note formats.

The list of supported formats are the following:
· alpha : "A5", "B3", "G4", ... (they do not include "#"; accidental is given aside)
· circle: -2, -1, 0, 1, 2, ... (see: https://en.wikipedia.org/wiki/Circle_of_fifths)
· midi:   0, 1, 2, ...

Only the few translations that we need are supported.
The naming convention of the convertion functions is: <format>_to_<format>

Accidentals are always represented with an integer:
·  0 (natural)
·  1 (sharp),  2 (double sharp), ...
· -1 (flat),  -2 (double flat), ...

Our circle-of-fifth notation is augmented with containing the octave as well.
With 'note' the standard circle-of-fifth notation and 'octave' the octave number,
our augmented circle-of-fifth notation corresponds to: 'note + 11 + 23 * octave'.

"""

# ---------------------------------------------------------------------------- #
# Switch between note format

def alpha_to_midi(alpha, accidental=0):
    """ Compute the MIDI number from the alpha notation.

    Parameters
    ----------
    alpha : str
        Note name, format: /[ABCDEFG]-?[0-9]+/.
    accidental : int, optional
        Accidental to include, if any possible.

    Returns
    -------
    int
        Associated MIDI number.

    """
    note   = (ord(alpha[0]) - ord("C")) % 7
    octave = int(alpha[1:])
    return (12 if note < 3 else 11) + 12 * octave + 2 * note + accidental

def alpha_to_circle(alpha, accidental=0):
    """ Compute the circle notation from the alpha notation.

    Parameters
    ----------
    alpha : str
        Note name, format: /[ABCDEFG]-?[0-9]+/.
    accidental : int, optional
        Accidental to include, if any possible.

    Returns
    -------
    int
        Circle-of-fifth notation

    """
    # Recover note (incl. accidental)
    note = (ord(alpha[0]) - ord("C")) % 7
    note = (2 * note if note < 3 else 2 * note - 1) + accidental
    # Recover the octave
    octave = int(alpha[1:])
    # Correct note and octave
    octave += note // 12
    note = note % 12
    # Convert note to (11-offset) circle notation
    if accidental < 0:
        note = 11 - note * 5 % 12
    else:
        note = 11 + note * 7 % 12
    # Return encoded note with octave
    return note + 23 * octave

def circle_to_midi(circle):
    """ Compute the MIDI number from the circle notation.

    Parameters
    ----------
    circle : int
        Circle-of-fifth notation.

    Returns
    -------
    int
        Associated MIDI number.

    """
    # Decode note and octave
    note   = circle % 23 - 11
    octave = circle // 23
    # Compute associated midi code
    midi = 12 + 12 * octave
    if note < 0:
        midi += (-note) * 5 % 12
    else:
        midi += note * 7 % 12
    return midi
