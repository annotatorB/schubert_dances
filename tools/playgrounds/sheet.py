# -*- coding: utf-8 -*-
"""
Playground testing some functions of 'tools/sheet.py'.
"""

from libs import sheet

# ---------------------------------------------------------------------------- #
# Playground

def test_written_named(sections):
    """ Test sheet 'as_written' iterations with spurious, named sections.

    Parameters
    ----------
    sections : str
        Order of each section, where each char is a section name

    """
    # Make a new sheet
    my_sheet = sheet.Sheet()
    # Make the given repetition
    for section in sections:
        my_sheet.append(section)
    # Try to write back the section
    print("%s => " % ("-").join(sections), end="", flush=True)
    res = ""
    for section, (voltas, begin, end) in my_sheet.as_written():
        res += "%s%s(%s)%s" % (("𝄆" if begin else ""), section, (".").join(str(x) for x in voltas), ("𝄇" if end else " "))
    print(res)

# Just call the test function several times if main module
if __name__ == "__main__":
    test_written_named("ABCD")
    test_written_named("ABACD")
    test_written_named("ABBCDEDEF")
    test_written_named("ABCBDBCBEBCBFGHIGHJK")
