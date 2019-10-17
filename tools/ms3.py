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
from collections import defaultdict


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
#                            HELPER FUNCTIONS
################################################################################
def search_in_list_of_tuples(L, pos, search, add=0):
    """ Returns a list of indices.

    Parameters
    ----------
    L : :obj:`list` of :obj:`tuple`
        List of tuples in which you want elements with value `search`.
    pos : :obj:`int`
        In which position of the tuples to search.
    search : :obj:`object`
        What to look for.
    add : :obj:`int`, opt
        How much you want to add to each index value.
    """
    return [i+add for i, item in enumerate(L) if search in item[pos]]








################################################################################
#                             SCORE CLASS
################################################################################
class Score(object):
    """ Parser for MuseScore3 MSCX files.

    NOTE: Measure count `mc` refers to the `mc`th measure node, whereas measure
    number `mn` refers to the `mn`th measure in the score. The latter can consist
    of several measure nodes and can be split across sections.

    Attributes
    ----------
    dir : :obj:`str`
        Directory where the parsed file is stored.
    file : :obj:`str`
        Absolute or relative path to the MSCX file you want to parse.
    filename : :obj:`str`
        Filename of the parsed file.
    last_node : :obj:`int`
        Count of the score's last measure node.
    measure_nodes : :obj:`dict` of :obj:`dict` of bs4.BeautifulSoup
        Keys of the first dict are staff IDs, keys of each inner dict are incremental
        measure counts (NOT measure numbers) and values are XML nodes.
    score : bs4.BeautifulSoup
        The complete XML structure of the parsed MSCX file.
    section_breaks : :obj:`dict`
        Keys are the counts of the measures that have a section break, values are
        lists of the breaking elements {startRepeat, endRepeat, BarLine}
    sections : :obj:`dict` of `Section`
        The sections of this score.
    staff_nodes : :obj:`dict` of bs4.BeautifulSoup
        Keys are staff IDs starting with 1, values are XML nodes.

    """

    def __init__(self,file):

        # Initialize attributes
        self.file = file
        self.dir, self.filename = os.path.split(os.path.abspath(file))
        self.staff_nodes = {}
        self.measure_nodes = {}
        self.section_breaks = defaultdict(list)
        self.sections = {}

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
        break_tags = ['startRepeat', 'endRepeat', 'BarLine', 'Volta']

        for staff_id, staff in self.staff_nodes.items():
            for i, measure in enumerate(staff.find_all('Measure')):
                self.measure_nodes[staff_id][i] = measure
                logging.debug(f"Stored the {i}th measure of staff {staff_id}.")

                # Detect section breaks
                breaks = [tag.name for tag in measure.find_all(break_tags)]
                if len(breaks) > 0:
                    self.section_breaks[i].extend(breaks)
                    logging.debug(f"Found section break(s) {breaks} in the {i}th measure of staff {staff_id}.")

        # Store last measure, presupposing that the first staff spreads throughout the piece.
        self.last_node =  max(self.measure_nodes[1].keys())

        self.parse_section_breaks()



    def parse_section_breaks(self):

        self.section_breaks[0].append('start')
        self.section_breaks[self.last_node].append('end')
        breaks = sorted(self.section_breaks.items())

        section_start = 0
        for splitpoint in search_in_list_of_tuples(breaks, 1, 'endRepeat', 1):
            if splitpoint == len(breaks):
                section = breaks[section_start:]
            else:
                voltas = search_in_list_of_tuples(breaks[:splitpoint], 1, 'Volta')
                if len(voltas) > 0:
                    while ('Volta' in breaks[splitpoint][1]) and (splitpoint < len(breaks)):
                        splitpoint += 1
                section = breaks[section_start:splitpoint]

            S = Section()
            next_mc = S.init(section, self, repeated=True)
            self.add_section(S)
            if next_mc <= self.last_node and breaks[splitpoint][0] != next_mc:
                breaks.insert(splitpoint, (next_mc, ['after_volta']))
            section_start = splitpoint



    def add_section(self, section):
        k = self.sections.keys()
        if len(k) > 0:
            next_key = max(k) + 1
        else:
            next_key = 0
        section.index = next_key
        self.sections[next_key] = section

S = Score('../scores/testscore.mscx')
S.sections

################################################################################
#                             SECTION CLASS
################################################################################
class Section(object):
    """ Holds the properties of a section.

    Attributes
    ----------
    first_measure, last_measure : :obj:`int`
        Measure counts of the section's first and last measure nodes.
    first_break, last_break : :obj:`str`
        What causes the section breaks at either side.
    index : :obj:`int`
        Index (running number) of this section.
    subsections : :obj:`list` of :obj:`int`
        Indices of smaller sections that are included in this one.
    voltas : :obj:`list` of :obj:`range`
        Ranges of voltas. Default: empty list
    repeated : :opj:`bool`
        Whether or not this section is repeated.
    """

    def __init__(self):
        self.first_measure, self.last_measure, self.index = 0, 0, 0
        self.first_break, self.last_break = '', ''
        self.subsections, self.voltas = [], []
        self.repeated = False

    def init(self, breaks, parent_score, repeated=False):

        if repeated:
            self.repeated = True

        self.first_measure, self.first_break = breaks[0]
        voltas = search_in_list_of_tuples(breaks, 1, 'Volta')
        if len(voltas) == 0:
            self.last_measure, self.last_break   = breaks[-1]
            following = self.last_measure + 1
        else:
            for volta in voltas:
                mc = breaks[volta][0]
                node = parent_score.measure_nodes[1][mc].find('Volta')
                length = int(node.find_next('next').location.measures.string)
                following = mc + length
                self.voltas.append(range(mc, following))
            self.last_measure = following - 1
            self.last_break = breaks[-1][1]

        self.first_break = list(set(self.first_break))
        self.last_break = list(set(self.last_break))
        return following



    def __repr__(self):
        return f"{'Repeated s' if self.repeated else 'S'}ection from node {self.first_measure} ({', '.join(self.first_break)}) to node {self.last_measure} ({', '.join(self.last_break)}), {'with ' + str(len(self.voltas)) if len(self.voltas) > 0 else 'without'} voltas."




################################################################################
#                           COMMANDLINE USAGE
################################################################################
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
