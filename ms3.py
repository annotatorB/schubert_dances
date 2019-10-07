""" Coding rules: Feel free to add!

###############################################################################
#                                  DOCSTRINGS
###############################################################################

NumPy style for use with Sphinx with Napoleon extension. Rules:

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

###############################################################################
#                               STRING CREATION
###############################################################################

f-Strings avoid type conversion and make the code more readble:
    >>> print(f"The value of this integer is {some_integer_variable}, which is quite {'small' if some_integer_variable < 100 else 'big'}!")
    The value of this integer is 10, which is quite small!

###############################################################################
#                                   LOGGING
###############################################################################

Use logging.debug('Message') abundantly to easily follow the programs workflow.
Use logging.info('Message') for messages that users would want to see in everyday use.

"""
###################
#Internal libraries
###################
import os, re, argparse, logging


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
            logging.warning(f"{self.filename} was created with MuseScore {ms_version}. Auto-conversion will be implemented in the future.")
        # ToDo: Auto-conversion

        # Extract staves
        for staff in self.score.find('Part').find_next_siblings('Staff'):
            staff_id = int(staff['id'])
            self.staff_nodes[staff_id] = staff
            self.measure_nodes[staff_id] = {}
            logging.debug(f"Stored staff with ID {staff_id}.")

        # Extract measures
        for staff_id, staff in self.staff_nodes.items():
            for i, measure in enumerate(staff.find_all('Measure')):
                self.measure_nodes[staff_id][i] = measure
                logging.debug(f"Stored the {i}th measure of staff {staff_id}.")


S = score('./scores/980/D980walzer02.mscx')
S.measure_nodes[1][0]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description = '''\
-------------------------------------
| Parser for MuseScore3 MSCX files. |
-------------------------------------

At the moment, this is just a skeleton. Later, the commandline can be used to
quickly parse entire folders and store files with the computed data.''')
    parser.add_argument('file',metavar='FILE',help='Absolute or relative path to the MSCX file you want to parse.')
    parser.add_argument('-l','--logging',default='INFO',help="Set logging to one of the levels {DEBUG, INFO, WARNING, ERROR, CRITICAL}.")
    args = parser.parse_args()

    logging_levels = {
        'DEBUG':    logging.DEBUG,
        'INFO':     logging.INFO,
        'WARNING':  logging.WARNING,
        'ERROR':    logging.ERROR,
        'CRITICAL':  logging.CRITICAL
        }
    logging.basicConfig(level=logging_levels[args.logging])
    S = score(args.file)
    print("Successfully parsed.")
