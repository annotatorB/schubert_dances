import os, re
import pandas as pd
import numpy as np
from collections import defaultdict
from fractions import Fraction as frac

EXACT_CHORD_MAP = {
('M3',): 'M3',
('m3',): 'm3',
('m2',): 'unison',
('P4',): 'P4',
('m6',): 'm6',
('M6',): 'M6',
('M7',): 'M7',
('M2',): 'M2',
('P5',): 'P5',
('D3',): 'D3',
}
FILTERING_CHORD_MAP = {
('M3', 'P5', 'm7'): 'dominant7',
('m3', 'D5', 'm6'): 'dominant65',
('m3', 'P4', 'M6'): 'dominant43',
('M2', 'A4', 'M6'): 'dominant2',
('M3', 'm7'): 'dominant7',
('D5', 'm6'): 'dominant65',
('m3', 'M6'): 'dominant43',
('M2', 'A4'): 'dominant2',
('m3', 'D5', 'D7'): 'diminished7',
('m3', 'D5', 'M6'): 'diminished65',
('m3', 'A4', 'M6'): 'diminished43',
('A2', 'A4', 'M6'): 'diminished2',
('m3', 'D7'): 'diminished7',
('m3', 'P5', 'm7'): 'minor7',
('m3', 'm7'): 'minor7',
('M3', 'P5'): 'major',
('m3', 'P5'): 'minor',
('m3', 'D5'): 'diminished',
('m3', 'm6'): 'major6',
('M3', 'M6'): 'minor6',
('P4', 'M6'): 'major64',
('P4', 'm6'): 'minor64',
('A4', 'M6'): 'diminished64',
('M2', 'P4', 'M6'): 'suspension',
('P4', 'M7'): 'suspension',
('P4', 'P5'): 'suspension',
('M2', 'P5'): 'suspension',
('M3', 'A4'): 'suspension',
('M2', 'M7'): 'suspension',
('M3', 'M7'): 'M3',
('P5', 'M6'): 'ambiguous',
('M3', 'P4'): 'M3',
('M2', 'm3'): 'm3',
('M3',): 'M3',
('m3',): 'm3',
('P5',): 'P5',
('D5',): 'D5',
}

NAME_TPCS = {'C': 0,
             'D': 2,
             'E': 4,
             'F': -1,
             'G': 1,
             'A': 3,
             'B': 5}

PITCH_NAMES = {0: 'F',
               1: 'C',
               2: 'G',
               3: 'D',
               4: 'A',
               5: 'E',
               6: 'B'}

TPC_MAJ_RN =  {0: 'IV',
               1: 'I',
               2: 'V',
               3: 'II',
               4: 'VI',
               5: 'III',
               6: 'VII'}
TPC_MIN_RN =  {0: 'VI',
               1: 'III',
               2: 'VII',
               3: 'IV',
               4: 'I',
               5: 'V',
               6: 'II'}

SYLLABLES = defaultdict(lambda: 'no')
SYLLABLES.update({ # https://www.epos.uni-osnabrueck.de/books/l/lehs007/pages/189.htm Lehmann, Silke: Bewegung und Sprache als Wege zum musikalischen Rhythmus
(0, 1): 'Taoao',
(0, frac(3/4)): 'Taoa',
(0, frac(1/2)): 'Tao',
(0, frac(3/8)): 'Tai',
(0, frac(1/4)): 'Ta',
(0, frac(3/16)): 'Tim',
(0, frac(1, 12)): 'Tri',
(0, frac(1/8)): 'Ti',
(0, frac(1/16)): 'Ti',
(frac(1, 16), frac(3, 16)): 'gim',
(frac(1, 16), frac(1, 8)): 'gim',
(frac(1/16), frac(1/16)): 'gi',
(frac(1, 12), frac(1, 12)): 'o',
(frac(1/8), frac(1/8)): 'ti',
(frac(1/8), frac(1/16)): 'ti',
(frac(1, 6), frac(1, 12)): 'le',
(frac(3, 16), frac(1, 8)): 'gim',
(frac(3/16), frac(1/16)): 'gi',
(frac(3, 16), frac(1, 32)): 'gi',
(frac(7, 32), frac(1, 32)): 'ri',
})

TPC_INT_NUM = [4, 1, 5, 2, 6, 3, 7]
TPC_INT_QUA = {0: ['P', 'P', 'P', 'M', 'M', 'M', 'M'],
               -1:['D', 'D', 'D', 'm', 'm', 'm', 'm']}

class defaultfunctiondict(defaultdict):
    """This class lets you create a defaultdict which applies a custom function on missing keys.

    Example
    -------
        d = defaultfunctiondict(C)
        d[x] # returns C(x)
    """
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError( key )
        else:
            ret = self[key] = self.default_factory(key)
            return ret

TIMESIG_BEAT = defaultfunctiondict(lambda x: f"1/{str(x).split('/')[1]}")
TIMESIG_BEAT.update({'4/8':  '1/4',})

# def get_onset_pattern(note_list):
#     return pd.Series({'pattern': tuple(sorted(set(note_list.onset.values))), 'end': frac(note_list.timesig.values[0])})



def add_chord_boundaries(chord_list, measure_list, next_ids='chord_id', multiple_pieces=False):
    """Single piece!"""
    if multiple_pieces:
        ix = chord_list.index.get_level_values(0)[0]
        chord_list = chord_list.droplevel(0)
        measure_list = measure_list.loc[ix]
    chord_list = chord_list.copy()
    ix = chord_list.index
    shifted = chord_list.reset_index()[['mc', 'onset', next_ids]].shift(-1).astype({'mc': 'Int64', next_ids:'Int64'})
    shifted.index = ix
    chord_list[['mc_next', 'onset_next', 'next_'+next_ids]] = shifted
    pos_cols = [chord_list.columns.get_loc('mc_next'), chord_list.columns.get_loc('onset_next')]
    chord_list.iloc[-1, pos_cols] = [measure_list.index.get_level_values('mc').max() + 1, 0]
    chord_list['chord_length'] = chord_list.apply(lambda r: get_onset_distance((r.mc, r.onset), (r.mc_next, r.onset_next), measure_list['act_dur']), axis=1)
    return chord_list



def all_chord_notes(chord_list, note_list, by='chord_id', multiple_pieces=False):
    """
    Parameters
    ----------
    """
    if multiple_pieces:
        id = chord_list.index.get_level_values(0)[0]
        chord_list = chord_list.droplevel(0)
        note_list = note_list.loc[id]
    return chord_list.groupby(by=by).apply(chord_notes, note_list)



def add_previous_ix(df, col='prev', inplace=True):
    if not inplace:
        df = df.copy()
    ix = df.index
    names = ix.names
    prev = pd.Series(df.reset_index()[df.index.names].itertuples(index=False, name=None)).shift()
    prev.index = ix
    df[col] = prev
    return df



def add_previous_vals(df, prev_ix_col='prev', col_map={'intervals': 'prev_ints'}, inplace=True):
    if not inplace:
        df = df.copy()
    if prev_ix_col not in df.columns:
        add_previous_ix(df, prev_ix_col)
    for col, new_col in col_map.items():
        prev_vals = df.loc[df.loc[df[prev_ix_col].notna(), prev_ix_col], col]
        ix = df[df[prev_ix_col].notna()].index
        prev_vals.index = ix
        df.loc[df[prev_ix_col].notna(), new_col] = prev_vals
    return df



def add_following_ix(df, col='next', inplace=True):
    if not inplace:
        df = df.copy()
    ix = df.index
    names = ix.names
    prev = pd.Series(df.reset_index()[df.index.names].itertuples(index=False, name=None)).shift(-1)
    prev.index = ix
    df[col] = prev
    return df



def add_following_vals(df, next_ix_col='next', col_map={'intervals': 'next_ints'}, inplace=True):
    if not inplace:
        df = df.copy()
    if next_ix_col not in df.columns:
        add_following_ix(df, next_ix_col)
    for col, new_col in col_map.items():
        next_vals = df.loc[df.loc[df[next_ix_col].notna(), next_ix_col], col]
        ix = df[df[next_ix_col].notna()].index
        next_vals.index = ix
        df.loc[df[next_ix_col].notna(), new_col] = next_vals
    return df



def apply_function(f, val, *args, **kwargs):
    """Applies function f to a collection."""
    if val.__class__ == float and isnan(val):
        return val
    if val.__class__ == pd.core.frame.DataFrame:
        if len(args) == 0 and len(kwargs) == 0:
            return val.applymap(f)
        else:
            logging.warning(f"Cannot map function {f} with arguments to entire DataFrame. Pass Series instead.")
    if val.__class__ == pd.core.series.Series:
        return val.apply(f, *args, **kwargs)
    result = [f(pc, *args, **kwargs) for pc in val]
    if val.__class__ == np.ndarray:
        return np.array(result).reshape(val.shape)
    if val.__class__ == tuple:
        return tuple(result)
    if val.__class__ == set:
        return set(result)
    return result



def apply_to_pieces(f, df, *args, **kwargs):
    """ Applies a function `f` which works on single pieces only to a dataframe of
    concatenated pieces distinguished by the first MultiIndex level.
    """
    return df.groupby(level=0).apply(f, *args, **kwargs)



def chord_notes(df, notes, **kwargs):
    """ Helper function for all_chord_notes()
    Parameters
    ----------
    df : :obj:`pandas.DataFrame`:
        A DataFrame with chord information, as created by a groupby('chord_id') on
        a chord list that has been treated with add_chord_boundaries(). Only the
        first row of `df` is being used.
    notes : :obj:`pandas.DataFrame`:
        Note list from which the harmony block is extracted
    """
    S = df.iloc[0]
    # try:
    notes = get_block(notes, (S.mc, S.onset), (S.mc_next, S.onset_next), cut_durations=True)
    # except:
    #     print(S)
    if 'rel_label' in S:
        notes.chords = S.rel_label
    return notes.sort_values(['mc', 'onset', 'midi'])



def compute_beat(r, beatsizedict=None):
    """ r = row of note_list"""
    if beatsizedict is None:
        beatsizedict = TIMESIG_BEAT
    assert r.timesig.__class__ == str, f"Time signatures should be strings, not {r.timesig.__class__}"
    size = frac(beatsizedict[r.timesig])
    onset = r.onset + r.offset
    beat = onset // size + 1
    subbeat = (onset % size) / size
    if subbeat > 0:
        return f"{beat}.{subbeat}"
    else:
        return str(beat)



def compute_beat_column(note_list, measure_list, inplace=False):
    """ Either `note_list` needs column `timesig` or you need to pass `measure_list` for merge."""
    if not 'timesig' in note_list.columns:
        if note_list.index.__class__ == pd.core.indexes.multi.MultiIndex and 'id' in note_list.index.names:
            notes = note_list.join(measure_list['timesig'], on=['id', 'mc'])
        else:
            notes = note_list.join(measure_list['timesig'], on='mc')
    else:
        notes = note_list.copy()
    beats = notes[['mc', 'onset', 'timesig']].merge(measure_list['offset'], on=['id', 'mc'], right_index=True).apply(compute_beat, axis=1)
    if not inplace:
        return beats
    if not 'timesig' in note_list.columns:
        note_list['timesig'] = notes['timesig']
    note_list['beats'] = beats
    note_list['beatsize'] = note_list['timesig']
    beatsizedict = {k: frac(v) for k, v in TIMESIG_BEAT.items()}
    note_list['beatsize'].replace(beatsizedict, inplace=True)



def count_accidentals(l):
    L = len(l)
    res = pd.Series()
    res['sharps'] = sum((e.count('#') for e in l)) / L
    res['flats']  = sum((e.count('b') for e in l)) / L
    res['sum'] = res['sharps'] + res['flats']
    return res



def create_os_features(onset_patterns, measure_counts):
    """Compute the fraction of every occurring onset pattern per piece.

    Parameters
    ----------
    onset_patterns : :obj:`pandas.Series`
        The measures with th eonset patterns you want to count.
    measure_counts : :obj:`pandas.Series`
        For every id, the amount of measures in the piece.
    """
    def os_fraction(patterns):
        id = patterns.index.levels[0][0]
        counts = patterns.value_counts()
        n = measure_counts[id]
        return counts / n
    res = pd.DataFrame(onset_patterns.groupby('id').apply(os_fraction)).unstack()
    res = res.droplevel(0, axis=1)
    return res



def get_block(note_list, start, end, cut_durations=False, staff=None, merge_ties=True):
    """ Whereas get_slice() gets sounding notes at a point, get_block() retrieves
    sounding notes within a range.
    The function adds the column `overlapping` whose values follow the same logic as `tied`:
        NaN for events that lie entirely within the block.
        -1  for events crossing `start` and ending within the block.
        1   for events crossing `end`.
        0   for events that start before and end after the block.

    Parameters
    ----------
    note_list : :obj:`pandas.DataFrame`
        Note list from which to retrieve the block.
    start, end : :obj:`tuple` of (:obj:int, numerical)
        Pass (mc, onset) tuples. `end` is exclusive
    cut_durations : :obj:`bool`, optional
        Set to True if the original note durations should be cut at the block boundaries.
    staff : :obj:`int`, optional
        Return block from this staff only.
    merge_ties : :obj:`bool`, optional
        By default, tied notes are merged so that they do not appear as two different onsets.
    """
    a_mc, a_onset = start
    b_mc, b_onset = end
    a_mc, b_mc = int(a_mc), int(b_mc)
    assert a_mc <= b_mc, "Start MC needs to be at most end MC."
    a_onset, b_onset = frac(a_onset), frac(b_onset)
    if a_mc == b_mc:
        assert a_onset <= b_onset, "Start onset needs to be at most end onset."

    res = note_list[(note_list.mc >= a_mc) & (note_list.mc <= b_mc)]

    if staff is not None:
        res = res[res.staff == staff]

    in_a = (res.mc == a_mc)
    in_b = (res.mc == b_mc)
    endpoint = res.onset + res.duration
    crossing_left = in_a & (res.onset < a_onset) & (a_onset < endpoint)
    on_onset = in_a & (res.onset == a_onset)
    crossing_right = in_b & (endpoint > b_onset)

    if a_mc == b_mc:
        in_between = in_a & (res.onset >= a_onset) & (res.onset < b_onset)
    else:
        onset_in_a = in_a & (res.onset >= a_onset)
        onset_in_b = in_b & (res.onset < b_onset)
        in_between = onset_in_a | onset_in_b
    if a_mc + 1 < b_mc:
        in_between = in_between | ((res.mc > a_mc) & (res.mc < b_mc))


    res = res[crossing_left | in_between].copy()
    res['overlapping'] = pd.Series([np.nan]*len(res.index), index=res.index, dtype='Int64')

    start_tie = lambda S: S.replace({np.nan:  1, -1:  0, 0: 0, 1: 1})
    end_tie   = lambda S: S.replace({np.nan: -1, -1: -1, 0: 0, 1: 0})

    if crossing_left.any():
        res.loc[crossing_left, 'overlapping'] = end_tie(res.loc[crossing_left, 'overlapping'])

    if crossing_right.any():
        res.loc[crossing_right, 'overlapping'] = start_tie(res.loc[crossing_right, 'overlapping'])

    if res.tied.notna().any():
        tied_from_left = on_onset & res.tied.isin([-1, 0])
        if tied_from_left.any():
            res.loc[tied_from_left, 'overlapping'] = end_tie(res.loc[tied_from_left, 'overlapping'])
        tied_to_right = in_b & (endpoint == b_onset) & res.tied.isin([0, 1])
        if tied_to_right.any():
            res.loc[tied_to_right, 'overlapping'] = start_tie(res.loc[tied_to_right, 'overlapping'])


    if cut_durations:
        if crossing_left.any():
            res.loc[crossing_left, 'duration'] = res.loc[crossing_left, 'duration'] - a_onset + res.loc[crossing_left, 'onset']
            res.loc[crossing_left, ['mc', 'onset']] = [a_mc, a_onset]
        if crossing_right.any():
            res.loc[crossing_right, 'duration'] = b_onset - res.loc[crossing_right, 'onset']

    if merge_ties & res.tied.any():
        merged, changes = merge_tied_notes(res, return_changed=True)
        if len(changes) > 0:
            new = [ix for ix, index_list in changes.items() if len(index_list) > 0 and res.at[index_list[-1], 'overlapping'] in [0,1] ]
            tie_over = merged.index.isin(new)
            merged.loc[tie_over] = start_tie(merged.loc[tie_over])
            res = merged

    return res



def get_lowest(note_list):
    lowest = note_list.midi.min()
    return note_list[note_list.midi == lowest]



def get_onset_distance(a, b, lengths=None):
    """ Get distance in fractions of whole notes.
    Parameters
    ----------
    a, b : :obj:`tuple`
        (mc, onset) `(int, Fraction)`
    timesig : :obj:str or number, optional
        Only needed if onsets are in different measures
    lengths : :obj:`dict` or :obj:`pandas.Series`
        For every measure count, the actual length (`act_dur`) in quarter beats.
        Single level index!
    """
    mc_a, os_a = a
    mc_b, os_b = b
    mc_a = int(mc_a)
    mc_b = int(mc_b)
    os_a = frac(os_a)
    os_b = frac(os_b)
    if mc_a == mc_b:
        return os_b - os_a
    else:
        assert lengths is not None, "If the onsets are in different measures, you need to pass the measure lengths."
        if mc_b < mc_a:
            mc_a, mc_b = mc_b, mc_a
            swapped = True
        else:
            swapped = False
        l1 = lengths[mc_a] - os_a
        inter_mc = sum(lengths[mc] for mc in range(mc_a + 1, mc_b))
        return -frac(l1 + inter_mc + os_b) if swapped else frac(l1 + inter_mc + os_b)



def get_pattern_list(onset_patterns, n_most_frequent=None, occurring_in_min=None, normalize=False, round=3, counts_only=False):
    """Summarize all patterns occurring in at least `occurring_in_min` pieces."""
    onset_patterns.name=None
    pattern_list = pd.DataFrame(onset_patterns.value_counts(), columns=['counts'])
    def count_pieces(onset_patterns, pattern=None):
        if pattern is None:
            return len(onset_patterns.groupby('id').count())
        return len(onset_patterns[onset_patterns == pattern].groupby('id').count())
    if not counts_only:
        pattern_list['n_pieces'] = pattern_list.index.map(lambda i: count_pieces(onset_patterns, i)).to_list()
    if n_most_frequent is not None:
        res = pattern_list.iloc[:n_most_frequent]
    elif occurring_in_min is not None:
        if counts_only:
            logging.warning('Parameter occurring_in_min ignored.')
        else:
            res = pattern_list[pattern_list.n_pieces >= occurring_in_min]
    else:
        res = pattern_list
    if normalize:
        res.counts = res.counts / pattern_list.counts.sum()
        if not counts_only:
            res.n_pieces = res.n_pieces / count_pieces(onset_patterns)
    return res.round(round)



def isnan(num):
    """Return True if `num` is numpy.nan (not a number)"""
    return num != num



def merge_tied_notes(df, return_changed=False):
    """ In a note list, merge tied notes to single events with accumulated durations.
    Input dataframe needs columns ['duration', 'tied', 'midi', 'staff', 'voice']
    """
    df = df.copy()
    notna = df[df.tied.notna()]
    starts = notna[notna.tied == 1]
    drops = []

    def merge(i, midi, staff, voice):
        """Looks for the ending(s) and recursively accumulates."""
        dur = 0
        ixs = []
        if i == len(notna):
            return dur, ixs
        else:
            end = notna.iloc[i]
        while end.tied == 1 or end.midi != midi\
                            or end.staff != staff:
                           #or end.voice != voice:  <-- caused errors
           i += 1
           if i == len(notna):
               return dur, ixs
           else:
               end = notna.iloc[i]
        dur += end.duration
        ixs.append(end.name)
        if end.tied == 0:
            d, i = merge(i+1, midi, staff, voice)
            dur += d
            ixs.extend(i)
        return dur, ixs


    for ix, r in starts.iterrows():
        add_dur, ixs = merge(notna.index.get_loc(ix)+1, r.midi, r.staff, r.voice)
        df.loc[ix, 'duration'] += add_dur
        drops.append(ixs)
    df.drop([e for l in drops for e in l], inplace=True)
    if return_changed:
        return df, {k: v for k, v in zip(starts.index.to_list(), drops)}
    else:
        return df




def midi2octave(val):
    """Returns 4 for values 60-71 and correspondingly for other notes.

    Parameters
    ----------
    val : :obj:`int` or :obj:`pandas.Series` of `int`
    """
    return val // 12 - 1



def name2rn(nn, key=0, minor=False):
    if nn.__class__ == float and isnan(nn):
        return nn
    try:
        nn.upper()
    except:
        return apply_function(name2rn, nn, key=key, minor=minor)
    tpc = name2tpc(nn)
    return tpc2rn(tpc, key, minor)



def name2tpc(nn):
    if nn.__class__ == float and isnan(nn):
        return nn
    try:
        nn_step, nn_acc = split_note_name(nn)
        nn_step = nn_step.upper()
    except:
        return apply_function(name2tpc, nn)
    step_tpc = NAME_TPCS[nn_step]
    return step_tpc + 7 * nn_acc.count('#') - 7 * nn_acc.count('b')



def os_pattern(note_list):
    """Turn the onsets of a note list into rhythmical language."""
    note_list = note_list.drop_duplicates(subset='onset').sort_values('onset')
    last = note_list.iloc[-1]
    length = last.onset + last.duration
    onsets = tuple(note_list.onset.values)
    onsets_end = onsets + (length, )
    durations = tuple(sum(t) for t in zip((-e for e in onsets_end), onsets_end[1:]))
    name = ''.join(SYLLABLES[t] for t in zip((e  % frac(1/4) for e in onsets), durations))
    return name



def read_chord_profiles(file, index_col=[0,1]):
    return pd.read_csv(file, sep='\t', index_col=index_col,
            converters={'intervals': parse_tuples,
                        'onbeat': parse_tuples,
                        'offbeat': parse_tuples,
                        'next': parse_tuples,})



def read_measure_list(file, index_col=[0]):
    return pd.read_csv(file, sep='\t', index_col=index_col,
                                   dtype={'volta': 'Int64',
                                          'numbering_offset': 'Int64',
                                          'dont_count': 'Int64'},
                                   converters={'duration': frac,
                                               'act_dur': frac,
                                               'offset': frac,
                                               'next': parse_lists})



def read_note_list(file, index_col=[0,1], converters={}, dtypes={}):
    conv = {'onset':frac,
                'duration':frac,
                'nominal_duration':frac,
                'scalar':frac,
                'beatsize': frac,
                'subbeat': frac}
    types = {'tied': 'Int64',
             'volta': 'Int64'}
    types.update(dtypes)
    conv.update(converters)
    return pd.read_csv(file, sep='\t', index_col=index_col,
                                dtype=types,
                                converters=conv)





def recognize_chord(interval_tuple):
    if interval_tuple == ():
        return 'unison'
    for t, label in EXACT_CHORD_MAP.items():
        if interval_tuple == t:
            return label
    for t, label in FILTERING_CHORD_MAP.items():
        t_set = set(t)
        if set(interval_tuple).intersection(t_set) == t_set:
            return label
    return 'ambiguous'



def remove_duplicates(l):
    L = len(l)
    if L > 0:
        prev = l[0]
        res = [prev]
    else:
        return l
    if L > 1:
        for e in l[1:]:
            if e != prev:
                res.append(e)
                prev = e
    return res


parse_lists = lambda l: [int(mc) for mc in l.strip('[]').split(', ') if mc != '']
parse_tuples = lambda t: tuple(i.strip("\',") for i in t.strip("() ").split(", ") if i != '')



def split_beats(S):
    """ Split a pandas.Series containing beat strings such as '1.1/2'. """
    splitbeats = S.str.split('.', expand=True)
    splitbeats[1] = splitbeats[1].fillna(0).apply(frac)
    return splitbeats.astype({0: int})



def split_note_name(nn):
    nn = str(nn)
    m = re.match("^([A-G]|[a-g])(#*|b*)$", nn)
    assert m is not None, nn + " is not a valid note name."
    return m.group(1), m.group(2)



def transpose_to_C(note_list, measure_list=None):
    """ Either `note_list` needs column `keysig` or you need to pass `measure_list` with `keysig`"""
    if not 'keysig' in note_list.columns:
        if note_list.index.__class__ == pd.core.indexes.multi.MultiIndex and 'id' in note_list.index.names:
            note_list_transposed = note_list.join(measure_list['keysig'], on=['id', 'mc'])
        else:
            note_list_transposed = note_list.join(measure_list['keysig'], on='mc')   # Add a column with the corresponding key signature for every note
    else:
        note_list_transposed = note_list.copy()
    note_list_transposed.tpc -= note_list_transposed.keysig                                             # subtract key signature from tonal pitch class (=transposition to C)
    midi_transposition = tpc2pc(note_list_transposed.keysig)\
                         .apply(lambda x: x if x <= 6 else x % -12)                                     # convert key signature to pitch class and decide whether MIDIs are shifted downwards (if <= 6) or upwards
    up_or_down = (midi_transposition == 6)                                                              # if the shift is 6, the direction of shift depends on the key signature:
    midi_transposition.loc[up_or_down] = note_list_transposed[up_or_down].keysig\
                                         .apply(lambda x: 6 if x > 0 else -6)                           # If the key signature is F#, shift downwards, if it's Gb, shift upwards
    note_list_transposed.midi -= midi_transposition
    return note_list_transposed



def tpc2int(tpc):
    """Return interval name of a tonal pitch class where
       0 = 'P1', -1 = 'P4', -2 = 'm7', 4 = 'M3' etc.
    """
    if tpc.__class__ == float and isnan(tpc):
        return tpc
    try:
        tpc = int(tpc)
    except:
        return apply_function(tpc2int, tpc)
    tpc += 1
    pos = tpc % 7
    int_num = TPC_INT_NUM[pos]
    qual_region = tpc // 7
    if qual_region in TPC_INT_QUA:
        int_qual = TPC_INT_QUA[qual_region][pos]
    elif qual_region < 0:
        int_qual = (abs(qual_region) - 1) * 'D'
    else:
        int_qual = qual_region * 'A'
    return f"{int_qual}{int_num}"



def tpc2name(tpc):
    """Return name of a tonal pitch class where
       0 = C, -1 = F, -2 = Bb, 1 = G etc.
    """
    try:
        tpc = int(tpc)
    except:
        return apply_function(tpc2name, tpc)

    tpc += 1 # to make the lowest name F = 0 instead of -1
    if tpc < 0:
        acc = abs(tpc // 7) * 'b'
    else:
        acc = tpc // 7 * '#'
    return PITCH_NAMES[tpc % 7] + acc



def tpc2pc(tpc):
    """Turn a tonal pitch class into a MIDI pitch class"""
    try:
        tpc = int(tpc)
    except:
        return apply_function(tpc2pc, tpc)

    return 7 * tpc % 12



def tpc2rn(tpc, key=0, minor=False):
    """Return scale degree of a tonal pitch class where
       0 = I, -1 = IV, -2 = bVII, 1 = V etc.
    """
    try:
        tpc = int(tpc)
    except:
        return apply_function(tpc2rn, tpc, key=0, minor=False)

    tpc -= key - 1

    if tpc < 0:
        acc = abs(tpc // 7) * 'b'
    else:
        acc = tpc // 7 * '#'

    if minor:
        return acc + TPC_MIN_RN[tpc % 7]
    else:
        return acc + TPC_MAJ_RN[tpc % 7]
