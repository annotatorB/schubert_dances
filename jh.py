import os
import pandas as pd
from collections import defaultdict
from fractions import Fraction as frac



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

# def get_onset_pattern(note_list):
#     return pd.Series({'pattern': tuple(sorted(set(note_list.onset.values))), 'end': frac(note_list.timesig.values[0])})



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



def get_pattern_list(onset_patterns, n_most_frequent=None, occurring_in_min=None):
    """Summarize all patterns occurring in at least `occurring_in_min` pieces."""
    pattern_list = pd.DataFrame(onset_patterns.value_counts(), columns=['total'])
    def count_pieces(onset_patterns, pattern):
        return len(onset_patterns[onset_patterns == pattern].groupby('id').count())
    pattern_list['n_pieces'] = pattern_list.index.map(lambda i: count_pieces(onset_patterns, i)).to_list()
    if n_most_frequent is not None:
        return pattern_list.iloc[:n_most_frequent]
    if occurring_in_min is not None:
        return pattern_list[pattern_list.n_pieces >= occurring_in_min]
    return pattern_list



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
                'scalar':frac}
    types = {'tied': 'Int64',
             'volta': 'Int64'}
    types.update(dtypes)
    conv.update(converters)
    return pd.read_csv(file, sep='\t', index_col=index_col,
                                dtype=types,
                                converters=conv)



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
