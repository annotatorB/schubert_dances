"""MuseScore3 Parser"""
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
#                     HELPER FUNCTIONS in alphabetical order
################################################################################

def get_repeat_structure(section_breaks):
    """Checks a list of (mc, break_tag_list)-tuples or the respective dict
       for closure and returns repetition structure.

    Example
    -------
        >>> check = {
                     0: ['start'],
                     8: ['endRepeat'],
                     9: ['startRepeat'],
                     12: ['Volta'],
                     13: ['endRepeat'],
                     14: ['Volta','startRepeat'],
                     30: ['end']
                    }
        >>> get_repeat_structure(check)
        [(0, 8), (9, 13)]
        WARNING:Section begins with a volta: (14, ['Volta', 'startRepeat']). Trouble follows.
        WARNING:Repeat structure so far: [(0, 8), (9, 13)]. Stack: [(14,)]. Closure missing.
    """
    stack, repeat_structure = [], []
    iterate = list(section_breaks.items()) if section_breaks.__class__ == dict else\
              list(section_breaks)         if section_breaks.__class__ != list else section_breaks
    for i, (mc, break_tag_list) in enumerate(iterate):

        # First measure can be beginning of a repeated section even without repeat sign
        if i == 0 and mc == 0:
            if 'endRepeat' in iterate[1][1]:
                repeated = True
            elif not 'startRepeat' in iterate[1][1] and 'endRepeat' in iterate[2][1]:
                repeated = True
            else:
                repeated = False

            if repeated:
                stack.append((0,))
                continue

        if 'startRepeat' in break_tag_list:
            if 'Volta' in break_tag_list:
                logging.warning(f"Section begins with a volta: {iterate[i]}. Trouble follows.")
            stack.append((mc,))
        elif 'endRepeat' in break_tag_list:
            if (len(stack) == 0) or (len(stack[-1]) != 1):
                logging.warning(f"Correct up to {iterate[i-1]}, the following {iterate[i]} has no explicit beginning. Repeat structure so far: {repeat_structure}")
                return repeat_structure
            else:
                section_start = stack.pop(-1)
                repeat_structure.append(section_start + (mc,))

    if len(stack) > 0:
        logging.warning(f"Repeat structure so far: {repeat_structure}. Stack: {stack}. Closure missing.")
        return repeat_structure
    else:
        logging.debug(f"Calculated consistent repeat structure {repeat_structure}.")
        return repeat_structure



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



def sort_dict(D):
    """ Returns a new dictionary with sorted keys. """
    return {k: D[k] for k in sorted(D)}




################################################################################
#                             SECTION CLASS
################################################################################
class Section(object):
    """ Holds the properties of a section.

    Attributes
    ----------
    first_measure, last_measure : :obj:`int`
        Measure counts of the section's first and last measure nodes.
    start_break, end_break : :obj:`str`
        What causes the section breaks at either side.
    index : :obj:`int`
        Index (running number) of this section.
    parent : :obj:`Score`
        The parent `Score` object that is creating this section.
    repeated : :obj:`bool`
        Whether or not this section is repeated.
    voltas : :obj:`list` of :obj:`range`
        Ranges of voltas. Default: empty list

    """

    def __init__(self, parent, first_measure, last_measure, index, repeated, start_break, end_break):
        self.first_measure, self.last_measure = first_measure, last_measure
        self.index = index
        self.repeated = repeated
        self.start_break, self.end_break = start_break, end_break
        self.voltas = []



    def __repr__(self):
        return f"{'Repeated s' if self.repeated else 'S'}ection from node {self.first_measure} ({', '.join(self.start_break) if self.start_break.__class__ == list else self.start_break}) to node {self.last_measure} ({', '.join(self.end_break) if self.end_break.__class__ == list else self.end_break}), {'with ' + str(len(self.voltas)) if len(self.voltas) > 0 else 'without'} voltas."




################################################################################
#                             SCORE CLASS
################################################################################
class Score(object):
    """ Parser for MuseScore3 MSCX files.

    NOTE: Measure count ``mc`` refers to the `mc` th measure node, whereas measure
    number ``mn`` refers to the `mn` th measure in the score. The latter can consist
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
    measure_nodes : :obj:`dict` of :obj:`dict` of :class:`bs4.element.Tag`
        Keys of the first dict are staff IDs, keys of each inner dict are incremental
        measure counts (NOT measure numbers) and values are XML nodes.
    score : :class:`bs4.BeautifulSoup`
        The complete XML structure of the parsed MSCX file.
    section_breaks : :obj:`dict`
        Keys are the counts of the measures that have a section break, values are
        lists of the breaking elements {startRepeat, endRepeat, BarLine}
    section_order : :obj:`list` of :obj:`int`:
        List of section IDs representing in which the sections in ``section_structure``
        are presented and repeated.
    section_structure : :obj:`list` of :obj:`tuple` of :obj:`int`
        Keys are section IDs, values are a tuple of two measure counts, the
        (inclusive) boundaries of the section. That is to say, no measure count
        can appear in two different value tuples since every measure can be part
        of only one section.
    sections : :obj:`dict` of `Section`
        The sections of this score.
    staff_nodes : :obj:`dict` of :class:`bs4.element.Tag`
        Keys are staff IDs starting with 1, values are XML nodes.
    super_sections : :obj:`dict` of :obj:`list`
        This dictionary has augmenting keys standing for one of the super_sections,
        i.e. sections that are grouped in the score by an englobing repetition,
        represented by lists of section IDs.
    super_section_order : :obj:`list` of :obj:`int`
        A more abstract version of section_order, using the keys from super_sections.
    test : :obj:`pandas.DataFrame`
        Mal schaun.
    """

    def __init__(self,file):

        # Initialize attributes
        self.file = file
        self.dir, self.filename = os.path.split(os.path.abspath(file))
        self.staff_nodes = {}
        self.measure_nodes = {}
        self.section_breaks = defaultdict(list)
        self.sections = {}
        self.section_structure = {}
        self.section_order = []
        self.super_sections = {}
        self.super_section_order = []

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
        break_tags = ['startRepeat', 'endRepeat', 'Volta', 'BarLine']

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

        section_counter, super_counter = 0, 0

        def create_section(f, t, repeated):
            nonlocal section_counter, super_counter

            section_breaks = {mc: break_tag_list for mc, break_tag_list in self.section_breaks.items() if f <= mc <= t}
            mcs = list(section_breaks.keys())
            if len(mcs) == 0:
                SB, EB = 'startNormal', 'endNormal'
            elif len(mcs) == 1:
                k = mcs[0]
                if k == f:
                    SB = section_breaks[k]
                    EB = 'endNormal'
                elif k == t:
                    SB = 'startNormal'
                    EB = section_breaks[k]
                else:
                    print(f"NOT IMPLEMENTED. CHECK WHAT THIS ELEMENT IS: {section_breaks}")
            else:
                SB, EB = section_breaks[mcs[0]], section_breaks[mcs[-1]]

            inner_breaks = [mc for mc, break_tag_list in section_breaks.items() if f < mc < t and 'BarLine' in break_tag_list]
            L = len(inner_breaks)
            if L > 0:

                inner_breaks.append(t)
                last_t = f-1
                subsections = []
                breaks = {}
                for i, br in enumerate(inner_breaks):
                    if i == 0:
                        start_break = SB
                        end_break = 'BarLine'
                        breaks[br] = end_break
                    elif i == L:
                        start_break = breaks[last_t]
                        end_break = EB
                    else:
                        start_break = breaks[last_t]
                        end_break = 'BarLine'
                        breaks[br] = end_break
                    self.section_structure[section_counter] = (last_t+1, br)
                    self.sections[section_counter] = Section(self, last_t+1, br, section_counter, repeated, start_break, end_break)
                    subsections.append(section_counter)
                    section_counter += 1
                    last_t = br
            else:
                self.section_structure[section_counter] = (f,t)
                self.sections[section_counter] = Section(self, f, t, section_counter, repeated, SB, EB)
                subsections = [section_counter]
                section_counter += 1

            self.section_order.extend(subsections * (repeated + 1))
            self.super_sections[super_counter] = subsections
            self.super_section_order.extend([super_counter] * (repeated + 1))
            super_counter += 1
            logging.debug(f"Created {'repeated ' if repeated else ''}section from {f} to {t}.")


        self.section_breaks[0].append('start')
        self.section_breaks[self.last_node].append('end')
        self.section_breaks = sort_dict(self.section_breaks)
        breaks = list(self.section_breaks.items())
        repeat_structure = get_repeat_structure(breaks)


        last_to  = -1
        for (i, (fro, to)) in enumerate(repeat_structure):

            if fro == last_to:
                logging.error(f"Overlapping sections in measure count {fro}")

            elif fro != last_to+1:
                create_section(last_to+1, fro-1, False)

            next_mc = to+1
            if next_mc in self.section_breaks and 'Volta' in self.section_breaks[next_mc]:
                node = self.measure_nodes[1][next_mc].find('Volta')
                length = int(node.find_next('next').location.measures.string)
                to += length

            create_section(fro, to, True)
            last_to = to

        if last_to != self.last_node:
            create_section(last_to+1, self.last_node, False)






# S = Score('../scores/testscore.mscx')
# S.sections
# S.section_structure
# S.section_order
# S.super_sections
# S.super_section_order




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
