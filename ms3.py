""" Coding rules: Feel free to add!

Docstrings in NumPy style for use with Sphinx with Napoleon extension. Rules:

Section                         #Line of ---- same length as title. No blank line underneath.
-------
parameter1 : :obj:`str`         #The colon after the parameter is separated by a space on each side.
parameter2 : :obj:`int`         #The :obj:`type` notation is only for standard python objects and creates links.
parameter3 : pd.DataFrame, optional

Example
-------
    >>> indented(function, call)
    'Indented result.'

    >>> other_example()
    'Result.'

f-Strings avoid type conversion and make the code more readble:
    >>> print(f"The value of this integer is {some_integer_variable}, which is quite {'small' if some_integer_variable < 100 else 'big'}!")
    The value of this integer is 10, which is quite small!
"""
###################
#Internal libraries
###################
import os, re

###################
#External libraries
###################
from bs4 import BeautifulSoup as bs         # python -m pip install beautifulsoup4
import pandas as pd
import numpy as np

#########
# Globals
#########
NEWEST_MUSESCORE = '3.2.3'

################################################################################
#                             SCORE CLASS
################################################################################
class score(object):
    """ Parser for MuseScore3 MSCX files.

    Attributes
    ----------
    dir : :obj:`str`
        Directory where the parsed file is stored.
    file : :obj:`str`
        Absolute or relative path to the MSCX file you want to parse.
    filename : :obj:`str`
        Filename of the parsed file.
    measure_nodes = :obj:`dict` of :obj:`dict` of bs4.BeautifulSoup
        Keys of the first dict are staff IDs, keys of each inner dict are incremental
        measure counts (NOT measure numbers) and values are XML nodes.
    score : bs4.BeautifulSoup
        The complete XML structure of the parsed MSCX file.
    staff_nodes : :obj:`dict` of bs4.BeautifulSoup
        Keys are staff IDs starting with 1, values are XML nodes.

    """

    def __init__(self,file):

        # Initialize attributes
        self.file = file
        self.dir, self.filename = os.path.split(os.path.abspath(file))
        self.staff_nodes = {}
        self.measure_nodes = {}

        # Load file
        with open(self.file, 'r') as file:
            self.score = bs(file.read(), 'xml')

        # Check Musescore version
        ms_version = self.score.find('programVersion').string
        if ms_version != NEWEST_MUSESCORE:
            print(f"{self.filename} was created with MuseScore {ms_version}. Auto-conversion will be implemented in the future.")
        # ToDo: Auto-conversion

        # Extract staves
        for staff in self.score.find('Part').find_next_siblings('Staff'):
            id = int(staff['id'])
            self.staff_nodes[id] = staff
            self.measure_nodes[id] = {}

        # Extract measures
        for staff_id, staff in self.staff_nodes.items():
            for i, measure in enumerate(staff.find_all('Measure')):
                self.measure_nodes[staff_id][i] = measure



S = score('/home/hentsche/Documents/phd/ADA/schubert_dances/scores/980/D980walzer02.mscx')
S.measure_nodes[1][0]
print(f"The value of this integer is {some_integer_variable}, which is quite {'small' if some_integer_variable < 100 else 'big'}!")
