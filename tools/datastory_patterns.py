import collections
import math
import matplotlib.pyplot as plt
import os
import pandas
import pickle
import plotly
import plotly.figure_factory
import numpy as np

from .ms3 import *
from .helpers import *
from . import xcor as cx

# ---------------------------------------------------------------------------- #
# Preprocessing

# Configuration
data     = "data"
data_ms3 = os.path.join(data, "MuseScore_3")
data_tsv = os.path.join(data, "tsv")

# Load the datasets
files = pd.read_csv(os.path.join(data_ms3, 'merged_ids.tsv'), sep='\t', index_col=0)
note_list = pd.read_csv(os.path.join(data_tsv, "note_list_complete.tsv"), sep='\t', index_col=[0,1,2],
                        dtype={"tied": "Int64",
                               "volta": "Int64"},
                        converters={"onset":frac,
                                    "duration":frac,
                                    "nominal_duration":frac,
                                    "scalar":frac})
measure_list = pd.read_csv(os.path.join(data_tsv, "measure_list_complete.tsv"), sep="\t", index_col=[0,1],
                           dtype={"volta": "Int64",
                                  "numbering_offset": "Int64",
                                  "dont_count": "Int64"},
                           converters={"duration": frac,
                                       "act_dur": frac,
                                       "offset": frac,
                                       "next": lambda l: [int(mc) for mc in l.strip("[]").split(", ") if mc != ""]})
section_order = pd.read_csv(os.path.join(data_tsv, "section_order_complete.tsv"), sep="\t", index_col = [0])\
                  .rename(columns={"object": "sections"})

# ---------------------------------------------------------------------------- #
# Auto-correlation of all the pieces with each of the two products

# Using 'harmorhythm'
path_xcors_pitch = os.path.join(data_ms3, 'xcors-pitch.dat')
if os.path.exists(path_xcors_pitch):
    # Load the cross-correlations
    with open(path_xcors_pitch, "rb") as fd:
        xcors_pitch = pickle.load(fd, fix_imports=False)
else:
    # Compute and save the cross-correlations
    xcors_pitch = dict()
    for pid, notes in note_list.groupby(level=0):
        print(".", end="", flush=True)
        xcors_pitch[pid] = cx.CrossCorrelation(cx.product_harmorhythm, (meas for _, meas in iter_measures(notes, volta=-1)))
    with open(path_xcors_pitch, "wb") as fd:
        pickle.dump(xcors_pitch, fd, protocol=-1, fix_imports=False)

# Using 'tonalrhythm'
path_xcors_tpc = os.path.join(data_ms3, 'xcors-tpc.dat')
if os.path.exists(path_xcors_tpc):
    # Load the cross-correlations
    with open(path_xcors_tpc, "rb") as fd:
        xcors_tpc = pickle.load(fd, fix_imports=False)
else:
    # Compute and save the cross-correlations
    xcors_tpc = dict()
    for pid, notes in note_list.groupby(level=0):
        print(".", end="", flush=True)
        xcors_tpc[pid] = cx.CrossCorrelation(cx.product_tonalrhythm, (meas for _, meas in iter_measures(notes, volta=-1)))
    with open(path_xcors_tpc, "wb") as fd:
        pickle.dump(xcors_tpc, fd, protocol=-1, fix_imports=False)

# ---------------------------------------------------------------------------- #
# Detect the structure of all the pieces, and for each of the two products

def trigger_to_name(trig):
    """ Map trigger levels to human-readable names.

    Parameters
    ----------
    trig: :obj:`float`
        Trigger level

    Returns
    -------
    :obj:`str`
        Associated human-readable name

    """
    if trig > 0.:
        if trig < 0.2:
            return "wild guess"
        if trig < 0.4:
            return "unsure"
        if trig < 0.6:
            return "presumably"
        if trig < 0.8:
            return "confident"
        return "certain"
    else:
        return "---"

structures = pandas.DataFrame(columns=["name", "HR-structure", "TR-structure", "HR-confidence", "TR-confidence", "HR-trigger", "TR-trigger"])
for pid, xcor_ptc in xcors_pitch.items():
    # Recover cross-correlation with the TPC product
    xcor_tpc = xcors_tpc[pid]
    # Build the associated piece name
    pinfo = files.loc[pid]
    name = "D%s %s n°%s" % (pinfo["D"], pinfo["dance"], pinfo["no"])
    # Detect the structure, using each product
    def detect_structure_wrapper(xcor):
        try:
            return cx.detect_structure(xcor)
        except RuntimeError as err:
            msg = str(err)
            if msg == "No spike found in given auto-correlation":
                return ("A", 0.)
            raise
    struct_ptc, trig_ptc = detect_structure_wrapper(xcor_ptc)
    struct_tpc, trig_tpc = detect_structure_wrapper(xcor_tpc)
    # Fill a new row for this piece
    structures.loc[len(structures)] = (name, struct_ptc, struct_tpc, trigger_to_name(trig_ptc), trigger_to_name(trig_tpc), trig_ptc, trig_tpc)

# ---------------------------------------------------------------------------- #
# Produce the named figures used in the data story

heatmap_piece1_pitch = cx.acor_heatmap(xcors_pitch[1], name_for="D41 menuett n°1 using the key-product")
heatmap_piece1_class = cx.acor_heatmap(xcors_tpc[1],   name_for="D41 menuett n°1 using the class-product")

autocor_piece1, _ax = plt.subplots()
cx.acor_lineplot(xcors_pitch[1], ax=_ax, legend="key-product", name_for="D41 menuett n°1")
cx.acor_lineplot(xcors_tpc[1], ax=_ax, legend="class-product", name_for="D41 menuett n°1")
