# -*- coding: utf-8 -*-
"""
Playground generating "Frère Jacques" on stdout.

Usages
------
You can pipe its output to a file or directly to 'play.py'

$ python3 frere_jacques.py | python3 play.py --soundfont <some_soundfont.sf2>

$ python3 frere_jacques.py > frere_jacques.sht && python3 play.py --soundfont <some_soundfont.sf2> --sheet frere_jacques.sht

"""

import fractions
import sys

from libs import notes
from libs import sheet

# ---------------------------------------------------------------------------- #
# Build the sheet

def main():
    """ Playground entry point.
    """
    def push_section(section=None, **kwargs):
        nonlocal sections
        nonlocal current
        if section is None:
            # Make section and push if any
            if current is None:
                section = None
            else:
                names = ("note", "start", "duration")
                section = sheet.Section(data=dict(zip(names, current)), **kwargs)
                sections.append(section)
            # Reset current
            current = None
        else:
            # Just push the given section again
            sections.append(section)
        return section
    def push_note(*args):
        nonlocal current
        # Initialize current if needed
        if current is None:
            current = tuple(list() for _ in range(3))
        # Transform the note
        args = (notes.alpha_to_circle("%s%d" % (args[0], args[1]), args[2]),) + args[3:]
        # Just push the transformed arguments in the corresponding list
        for l, v in zip(current, args):
            l.append(v)
        # Return the timestamp right after the note finishes
        return args[1] + args[2]
    # Data
    sections = sheet.Sheet()
    current  = None
    # First part (twice)
    i = fractions.Fraction(0, 1)
    for n in ("G", "A", "B", "G"):
        i = push_note(n, 4, 0, i, fractions.Fraction(1, 4))
    push_section(push_section(tempo=60, signature=(2, 4)))
    # Second part (twice)
    i = fractions.Fraction(0, 1)
    for n, o, d in (("B", 0, 1), ("C", 1, 1), ("D", 1, 2)):
        i = push_note(n, 4 + o, 0, i, fractions.Fraction(d, 4))
    push_section(push_section(tempo=60, signature=(2, 4)))
    # Third part (twice)
    i = fractions.Fraction(0, 1)
    for n, o, d, e in (("D", 1, 3, 16), ("E", 1, 1, 16), ("D", 1, 1, 8), ("C", 1, 1, 8), ("B", 0, 1, 4), ("G", 0, 1, 4)):
        i = push_note(n, 4 + o, 0, i, fractions.Fraction(d, e))
    push_section(push_section(tempo=60, signature=(2, 4)))
    # Fourth part (twice)
    i = fractions.Fraction(0, 1)
    for n in ("G", "D", "G"):
        i = push_note(n, 4, 0, i, fractions.Fraction(1, 4))
    push_section(push_section(tempo=60, signature=(2, 4), silence=fractions.Fraction(1, 4)))  # Silence on purpose here
    # Save sheet
    sections.assert_format()
    sheet.save(sections, sys.stdout.buffer)

# Call main if main module
if __name__ == "__main__":
    main()
