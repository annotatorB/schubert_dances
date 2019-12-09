""" TO USE SOME OF THE FUNCTIONS YOU NEED TO EXPAND YOUR NOTE_LIST:

    git = '/e/Documents/GitHub/schubert_dances'

    note_list = pd.read_csv(os.path.join(git,'data/tsv/note_list_complete.tsv'), sep='\t', index_col=[0,1,2],
                                dtype={'tied': 'Int64',
                                       'volta': 'Int64'},
                                converters={'onset':frac,
                                            'duration':frac,
                                            'nominal_duration':frac,
                                            'scalar':frac})
    measure_list = pd.read_csv(os.path.join(git,'data/tsv/measure_list_complete.tsv'), sep='\t', index_col=[0,1],
                                   dtype={'volta': 'Int64',
                                          'numbering_offset': 'Int64',
                                          'dont_count': 'Int64'},
                                   converters={'duration': frac,
                                               'act_dur': frac,
                                               'offset': frac,
                                               'next': lambda l: [int(mc) for mc in l.strip('[]').split(', ') if mc != '']})
    note_list = transpose_expand(note_list, measure_list)
"""

from ms3 import *





def beat_info(note_list, measure_list):
    """Adds columns ['timesig', 'beatsize', 'beat', 'subbeat']"""
    note_list = note_list.copy()
    compute_beat_column(note_list, measure_list, inplace=True)
    note_list[['beat', 'subbeat']] = split_beats(note_list.beats)
    return note_list

def expand(note_list, measure_list):
    """Adds columns ['timesig', 'beatsize', 'beat', 'subbeat', 'note_names', 'octaves']"""
    note_list = beat_info(note_list, measure_list)
    note_list['note_names'] = tpc2name(note_list.tpc)
    note_list['octaves'] = midi2octave(note_list.midi)
    return note_list

def transpose_expand(note_list, measure_list):
    """Transpose note_list to C and add columns ['timesig', 'beatsize', 'beat', 'subbeat', 'note_names', 'octaves']"""
    transposed = transpose_to_C(note_list, measure_list)
    transposed = expand(note_list, measure_list)
    return transposed


def get_lowest(note_list):
    """Get all notes sharing the lowest midi pitch.

    Example
    -------
        note_list.groupby('mc').apply(get_lowest)
    """
    lowest = note_list.midi.min()
    return note_list[note_list.midi == lowest]


def get_slice(note_list, mc=None, mn=None, onset=None, beat=None, staff=None,):
    """ Returns all sounding notes at a given onset or beat.
    Function relies on the columns ['beats', 'beatsize', 'beat', 'subbeat'] which you can add using beat_info(note_list, measure_list)
    Function does not handle voltas. Regulate via `note_list`

    Parameters
    ----------
    note_list : :obj:`pd.DataFrame`
        From where to retrieve the slice
    mc : :obj:`int`
        Measure count
    mn : :obj:`int`
        Measure number
    onset : numerical
    beat : numerical or str
    staff : :obj:`int`
        Return slice from this staff only.

    Examples
    --------
        get_slice(test, mn=3, beat=3.5)         # slice at measure NUMBER 3 at half of beat 3
        get_slice(test, mc=3, beat='2.1/8')     # slice at measure COUNT 3 at 1/8th of beat 2
        get_slice(test, mn=7, onset=1/8)        # slice at measure NUMBER 7 at the second eight
    """
    if mc is None:
        assert mn is not None, "Pass either mn or mc"
        res = note_list[note_list.mn == mn].copy()
    else:
        assert mn is None, "Pass either mn or mc"
        res = note_list[note_list.mc == mc].copy()

    if staff is not None:
        res = res[res.staff == staff]

    if beat is None:
        assert onset is not None, "Pass either onset or beat"
        coocurring = res.onset == onset
        still_sounding = (res.onset < onset) & (onset < (res.onset + res.duration))
    else:
        assert onset is None, "Pass either onset or beat"
        beats = val2beat(beat)
        beat, subbeat = split_beat(beats)
        b = beat2float(beats)
        dec_beats = res.beats.apply(beat2float)
        endings = dec_beats + (res.duration / res.beatsize)
        coocurring = (res.beat == beat) & (res.subbeat == subbeat)
        still_sounding = (dec_beats < b) & (b < endings)

    return res[coocurring | still_sounding]



def iter_measures(note_list, volta=None, staff=None):
    """ Iterate through measures' note lists by measure number.

    Parameters
    ----------
    note_list : :obj:`pandas.DataFrame()`
        Note list which you want to iterate through.
    volta : :obj:`int`, optional
        Pass -1 to only see the last volta, 1 to only see the first, etc.
        Defaults to `None`: In that case, if measure number 8 has two voltas, the result
        holds index 8 with all voltas, index '8a' for volta 1 only and '8b' for
        volta 2 including other parts of this measure number (e.g. following anacrusis).
    staff : :obj:`int`, optional
        If you want to iterate through one staff only.

    Examples
    --------
        numbers, measures = zip(*iter_measures(note_list))
        pd.concat(measures, keys=numbers, names=['mn'] + note_list.index.names)

    """
    mns = [int(mn) for mn in note_list.mn.unique()]
    if note_list.volta.notna().any() and volta is None:
        voltas = note_list[note_list.volta.notna()]
        to_repeat = []
        for mn in voltas.mn.unique():
            to_repeat.extend([mn] * len(voltas.volta[voltas.mn == mn].unique()))
        mns.extend(disambiguate_repeats(to_repeat))
        mns = sorted(mns, key=lambda k: k if type(k)==int else int(k[:-1]))
    if volta is None:
        volt = None
    if staff is not None:
        note_list = note_list[note_list.staff == staff]

    for number in mns:
        if number.__class__ == str:
            mn = int(number[:-1])
            volt = ord(number[-1])-96 # 'a' -> 1, 'b' -> 2
        else:
            mn = number
        sl = note_list[note_list.mn == mn]
        if sl.volta.notna().any():
            last_volta = sl.volta.max()
            if volta is not None:
                volt = volta_parameter(volta, last_volta)
                sl = sl[(sl.volta == volt) | sl.volta.isna()]
            elif volt is not None:
                if volt == last_volta:
                    sl = sl[(sl.volta == volt) | sl.volta.isna()]
                else:
                    sl = sl[(sl.volta == volt)]
                volt = None
        yield number, sl



def get_bass(note_list, onsets=None, by='mn', resolution=None):
    """If onsets=None, iterate through beats and return the lowest note respectively.
    Set `resolution=1/8` (for example) to get the lowest note on an eighth note grid.
    Use function bass_per_beat() for convenience.

    Parameters
    ----------
    onsets : :obj:`list`
        Onsets you want to iterate through in every measure.
    by : {'mn', 'mc'}
        Go through measure numbers (default) or measure counts (`resolution not implemented`)
    resolution : numerical
        If `by='mn'`, you can get a smaller division of every beat, e.g. set
        `resolution=1/16` to divide every beat in sixteenth note steps

    Returns
    -------
    generator
        A MultiIndex tuple and a note list for every mc or mn
    """
    if onsets is not None:
        onsets = [frac(os) for os in onsets]
    if resolution is not None:
        resolution = frac(resolution)
    if by == 'mn':
        for mn, notes in iter_measures(note_list, volta=-1):
            if onsets is None:
                timesig = notes.timesig.unique()[0]
                beatsize = notes.beatsize.unique()[0]
                for beat in range(1, int(1 + frac(timesig) / beatsize)):
                    if resolution is None:
                        yield (mn, beat), get_lowest(get_slice(notes, mn=mn, beat=beat))
                    else:
                        n_steps = int(beatsize / resolution)
                        for sub in range(n_steps):
                            b = f"{beat}.{frac(sub / n_steps)}" if sub > 0 else str(beat)
                            yield (mn, b), get_lowest(get_slice(notes, mn=mn, beat=b))
            else:
                for os in onsets:
                    yield (mn, os), get_lowest(get_slice(note_list, mn=mn, onset=os))
    elif by == 'mc':
        mcs = note_list.mc.unique()
        for mc in mcs:
            notes = note_list[note_list.mc == mc]
            if onsets is None:
                timesig = notes.timesig.unique()[0]
                beatsize = notes.beatsize.unique()[0]
                for beat in range(1, int(1+frac(timesig)/beatsize)):
                    yield (mc, beat), get_lowest(get_slice(note_list, mc=mc, beat=beat))
            else:
                for os in onsets:
                    yield (mc, os), get_lowest(get_slice(note_list, mc=mc, onset=os))
    else:
        raise ValueError("by needs to be 'mc' or 'mn'")



def bass_per_beat(df, resolution=None):
    """ Convenience function to see the result of the generator get_bass().
    Use for one piece at a time."""
    if 'id' in df.index.names:
        df = df.droplevel(df.index.names.index('id'))
    ix, rows = zip(*get_bass(df, resolution=resolution))
    bass = pd.concat(rows, keys=ix, names=['mn', 'beat'] + df.index.names)
    return bass.reset_index(['section', 'ix']).drop_duplicates(['section', 'ix']).set_index(['section', 'ix'], append=True)


class SliceMaker(object):
    """ This class serves for passing slice notation such as :3 as function arguments.

    Example
    -------
        SL = SliceMaker()
        some_function( slice_this, SL[3:8] )
    """
    def __getitem__(self, item):
        return item

SL = SliceMaker()

def index_tuples(df, sl=SL[:], nested=False):
    """ Get tuples representing a slice of multiindex levels."""
    def separate(frame):
        S = frame.iloc[:,-1]
        beginnins = list(frame[S - S.shift() != 1].itertuples(index=False,name=None))
        endings = list(frame[S.shift(-1) - S != 1].itertuples(index=False,name=None))
        sections = list(zip(beginnins,endings))
        return sections

    def get_tuples(frame):
        return [t[sl] for t in frame.index.to_list()]

    lvls = len(df.index.names)

    if nested:
        if lvls == 2:
            res = sorted([t[sl] for t in df.index.to_list()])
            res_df = pd.DataFrame(res)
            return res_df.groupby(0).apply(separate).sum()
        elif lvls > 2:
            return df.groupby(level=list(range(lvls-2))).apply(get_tuples).to_dict()
        else:
            print("Not implemented for single index.")
            return []
    else:
        res = sorted([t[sl] for t in df.index.to_list()])
        return res



def get_harmonic_collections(note_list, bass):
    """ Partition `note_list` via the bass computed by bass_per_beat().
    Use for one piece at a time."""
    if 'id' in note_list.index.names:
        note_list = note_list.droplevel(note_list.index.names.index('id'))
    starts = pd.Series(False, index=note_list.index)
    fro = index_tuples(bass, SL[2:4])
    starts.loc[fro] = True
    i = 0
    first = starts.iloc[i]
    while not first:
        i += 1
        first = starts.iloc[i]
    if i > 0:
        starts.drop(starts.iloc[:i].index, inplace=True)
    to = starts.shift(-1)
    to.iloc[-1] = True
    ranges = list(zip(starts[fro].index.to_list(), starts[to].index.to_list()))
    return pd.concat([note_list.loc[fro:to] for fro, to in ranges], keys=index_tuples(bass, SL[:2]))
