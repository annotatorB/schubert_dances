import os
import pandas as pd
from collections import defaultdict
from fractions import Fraction as frac

PITCH_NAMES = {0: 'F',
               1: 'C',
               2: 'G',
               3: 'D',
               4: 'A',
               5: 'E',
               6: 'B'}

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



def get_pattern_list(onset_patterns, n_most_frequent=None, occurring_in_min=None, normalize=False, round=3):
    """Summarize all patterns occurring in at least `occurring_in_min` pieces."""
    pattern_list = pd.DataFrame(onset_patterns.value_counts(), columns=['counts'])

    def count_pieces(onset_patterns, pattern=None):
        if pattern is None:
            return len(onset_patterns.groupby('id').count())
        return len(onset_patterns[onset_patterns == pattern].groupby('id').count())

    pattern_list['n_pieces'] = pattern_list.index.map(lambda i: count_pieces(onset_patterns, i)).to_list()
    if n_most_frequent is not None:
        res = pattern_list.iloc[:n_most_frequent]
    elif occurring_in_min is not None:
        res = pattern_list[pattern_list.n_pieces >= occurring_in_min]
    else:
        res = pattern_list
    if normalize:
        res.counts = res.counts / pattern_list.counts.sum()
        res.n_pieces = res.n_pieces / count_pieces(onset_patterns)
    return res.round(round)




def midi2octave(val):
    """Returns 4 for values 60-71 and correspondingly for other notes.

    Parameters
    ----------
    val : :obj:`int` or :obj:`pandas.Series` of `int`
    """
    return val // 12 - 1



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



def read_measure_list(file, index_col=[0]):
    return pd.read_csv(file, sep='\t', index_col=index_col,
                                   dtype={'volta': 'Int64',
                                          'numbering_offset': 'Int64',
                                          'dont_count': 'Int64'},
                                   converters={'duration': frac,
                                               'act_dur': frac,
                                               'offset': frac,
                                               'next': lambda l: [int(mc) for mc in l.strip('[]').split(', ') if mc != '']})



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



def split_beats(S):
    """ Split a pandas.Series containing beat strings such as '1.1/2'. """
    splitbeats = S.str.split('.', expand=True)
    splitbeats[1] = splitbeats[1].fillna(0).apply(frac)
    return splitbeats.astype({0: int})



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



# def summarize(chord_segment, col='note_names'):
#     """"""
#     notes = chord_segment[col].values
#     bass = notes[0]
#     chord_notes = set(notes[1:]) if len(notes) > 1 else {}
#     if bass in chord_notes:
#         chord_notes -= {bass}
#     return bass, tuple(sorted(chord_notes))
#
#
#
# def add_previous_ix(df, col='prev'):
#     ix = df.index
#     names = ix.names
#     prev = pd.Series(df.reset_index()[df.index.names].itertuples(index=False)).shift()
#     prev.index = ix
#     df[col] = prev
#     return df
#
# def add_previous_vals(df, prev_ix_col='prev', col_map={'intervals': 'prev_ints'}):
#     for col, new_col in col_map.items():
#         prev_vals = df.loc[df.loc[df[prev_ix_col].notna(), prev_ix_col], col]
#         ix = df[df[prev_ix_col].notna()].index
#         prev_vals.index = ix
#         df.loc[df[prev_ix_col].notna(), new_col] = prev_vals
#     return df
#
#
#
#
# def get_intervals(chord_segment, col='note_names'):
#     """"""
#     bass_name = chord_segment[col].values[0]
#     bass_tpc =  chord_segment.tpc.values[0]
#     ints = (chord_segment.tpc[chord_segment.tpc != bass_tpc] - bass_tpc).values
#     return pd.Series({'bass': bass_name, 'intervals': tuple(sorted(tpc2int(set(ints)))) })
#
#
# def summarize_ints(chord_segment, col='note_names'):
#     """"""
#     bass_note = chord_segment.iloc[0]
#     bass_name = bass_note[col]
#     bass_tpc =  bass_note.tpc
#     chord_notes = chord_segment[(chord_segment.tpc != bass_tpc) & chord_segment.gracenote.isna()].copy()
#     chord_notes['intervals'] = tpc2int(chord_notes.tpc - bass_tpc)
#     intervals = tuple(sorted(set(chord_notes.intervals.values)))
#     res = pd.Series({'bass': bass_name, 'intervals': intervals})
#     total_duration = chord_notes.duration.sum()
#     if len(intervals) == 0 or total_duration == 0:
#         return res
#     for iv in intervals:
#         sel = chord_notes[(chord_notes.intervals == iv)]
#         tot = len(sel)
#         try:
#             res[iv+'_duration'] = sel.duration.sum() / total_duration
#         except:
#             print(chord_notes)
#         onbeat = (sel.subbeat == 0) & ~sel.overlapping.isin([0, -1])
#         res[iv+'_oncount'] = len(sel[onbeat]) / tot
#         res[iv+'_offcount'] = len(sel[~onbeat]) / tot
#     return res
