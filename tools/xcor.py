import collections
import pandas

from .helpers import iter_measures

# ---------------------------------------------------------------------------- #
# Cross- and auto-correlation code

class CrossCorrelation:
    """ Arbitrary cross-correlation of two signals.
    """

    def __init__(self, product, sig_a, sig_b=None):
        """ Initial processing of the signals.

        Parameters
        ----------
        product: function
            A symmetric function taking two "signal instances" and returning a summable.
        sig_a: generator
            Signal A, a generator on instances that product can process.
        sig_b: generator, optional
            Signal B, a generator on instances that product can process.
            Use signal A if not provided.

        """
        # Generate signals
        sig_a = tuple(sig_a)
        if sig_b is None:
            sig_b = sig_a
        else:
            sig_b = tuple(sig_b)
        # Get lengths
        len_a = len(sig_a)
        len_b = len(sig_b)
        # Compute unit cross-correlations: unit[len_b * i_a + i_b] = xcor(i_a, i_b)
        units = [None] * (len_a * len_b)
        pos   = 0
        for unit_a in sig_a:
            for unit_b in sig_b:
                units[pos] = product(unit_a, unit_b)
                pos += 1
        # Finalization
        self.len_a = len_a
        self.len_b = len_b
        self.units = units

    def get(self, a, b):
        """ Get the unit cross-correlation for the given instance indices.

        Parameters
        ----------
        a: :obj:`int`
            Index of the instance in signal A.
        b: :obj:`int`
            Index of the instance in signal B.

        Returns
        -------
        summable
            Cross-correlation unit for instances A[a] and B[b].

        """
        return self.units[self.len_b * a + b]

    def compute(self, offset, seg_b=None, seg_a=None):
        """ Compute the cross-correlation of (a segment of) signal B over (a segment of) signal A.

        Parameters
        ----------
        offset: :obj:`int`
            Offset to apply on signal B.
        seg_b: `tuple` of two `int`, optional
            Segment of signal B to select, all signal B if `None`.
        seg_a: `tuple` of two `int`, optional
            Segment of signal A to select, all signal A if `None`.

        Returns
        -------
        summable
            Cross-correlation of signal B over signal A for the requested offset.
            `None` if segments do not overlap.

        """
        # Replace defaults
        if seg_a is None:
            seg_a = (0, self.len_a)
        if seg_b is None:
            seg_b = (0, self.len_b)
        # Prepare computation
        off_a, len_a = seg_a
        len_a -= off_a
        off_b, len_b = seg_b
        len_b -= off_b
        # Compute cross-correlation
        res = None
        for x in range(max(0, offset), min(len_a, len_b + offset)):
            v = self.get(off_a + x, off_b + x - offset)
            if res is None:
                res = v
            else:
                res += v
        return res

    def slide(self, seg_b=None, seg_a=None, no_neg=False):
        """ Compute the cross-correlation of B over A for every overlapping offsets.

        Parameters
        ----------
        seg_b: `tuple` of two `int`, optional
            Segment of signal B to select, all signal B if `None`.
        seg_a: `tuple` of two `int`, optional
            Segment of signal A to select, all signal A if `None`.
        no_neg: :obj:`bool`
            Whether not to map negative offsets

        Returns
        -------
        dict of offset -> summable
            Map between overlapping offset and associated cross-correlation.

        """
        return dict((offset, self.compute(offset, seg_b, seg_a)) for offset in range(0 if no_neg else (1 - self.len_b), self.len_a))

class AutoCorrelation:
    """ Arbitrary "interior" auto-correlation of a signal.
    """

    def __init__(self, signal):
        """ Full fast, interior auto-correlation initialization.

        Parameters
        ----------
        signal: generator
            Signal, a generator on instances that product can process.

        """
        pass # TODO

# ---------------------------------------------------------------------------- #
# Product functions

def product_harmorhythm(meas_a, meas_b):
    """ Hard onset and pitch matching product function.

    Parameters
    ----------
    meas_a: :obj:`pandas.DataFrame`
        Measure A, internal format
    meas_b: :obj:`pandas.DataFrame`
        Measure B, internal format

    Returns
    -------
    float
        How many times at least two notes from the two measures start at the same time and match pitches
    """
    res = 0
    # Get iterators
    cols = ["onset", "midi"]
    iter_a = meas_a[cols].iterrows()
    iter_b = meas_b[cols].iterrows()
    try:
        # Current onsets, for each measure A and B
        _, state_a = next(iter_a)
        _, state_b = next(iter_b)
        while True:
            if state_a[0] < state_b[0]: # A is late and must be advanced
                _, state_a = next(iter_a)
            elif state_a[0] > state_b[0]: # B is late and must be advanced
                _, state_b = next(iter_b)
            else: # Both A and B at the same onset
                # NB: notes are ordered by 'onset' then by 'midi' pitch
                if state_a[1] < state_b[1]: # A is at a lower note and must be advanced
                    _, state_a = next(iter_a)
                elif state_a[1] > state_b[1]: # B is at a lower note and must be advanced
                    _, state_b = next(iter_b)
                else: # Matching notes, process accordingly
                    res += 1
                    _, state_a = next(iter_a)
                    _, state_b = next(iter_b)
    except StopIteration:
        return float(res)

# ---------------------------------------------------------------------------- #
# Detection functions

def detect_spikes(signal):
    """ Identify offset of (rising edge) spikes in a given cross-correlation.

    Parameters
    ----------
    signal: generator of `tuple` of (`int`, '<, >='-comparable)
        Signal generator, producing tuples of (index, value) by strictly increasing index

    Returns
    -------
    generator of `int`
        Indices of all the (rising edge) spikes

    """
    try:
        window = collections.deque(maxlen=3)
        # Initialize window
        for _ in range(3):
            window.append(next(signal))
        # Roll over signal, feeding window
        while True:
            # Detect (rising edge) spike
            if window[0][1] < window[1][1] and window[1][1] >= window[2][1]:
                yield window[1][0]
            # Continue rolling
            window.append(next(signal))
    except StopIteration:
        return

def detect_form(piece, ac_hr=None):
    """ Detect the form of a piece.

    Parameters
    ----------
    piece: :obj:`pandas.DataFrame`
        Piece, internal formal.
    ac_hr: :obj:`AutoCorrelation`, optional
        "Harmo-rhythm" auto-correlation of the piece, computed if not provided

    Returns
    -------
    `tuple` of `str`
        List of letters representing the form of the piece

    """
    # Get piece length (in measures)
    length = notes["mc"].max() - notes["mc"].min() + 1
    # Compute auto-correlation (if not already done)
    if xcor_hr is None:
        xcor_hr = notes_xcor(product_harmorhythm, notes, notes, no_neg=True, name="hr")
    # Compute spike positions (if not already done)
    if spikes is None:
        spikes = xcor_spikes(ahr)
    spikes = tuple(spikes)
    # Gather the patterns
    patterns = dict() # pid -> (notes, start, length)
    start = 0
    for pid, stop in enumerate(spikes + (length,)):
        patterns[pid] = (notes[(notes["mc"] >= start) & (notes["mc"] < stop)], start, stop - start)
        start = stop
    # Compute the spikes and association matching proportions for each patterns
    props = dict() # spike positions -> list of (spike match proportion, pid)
    for pid, (pattern, start, _) in patterns.items():
        xcor = notes_xcor(product_harmorhythm, pattern, notes, no_neg=True) / len(pattern)
        xspk = tuple(pos for pos in xcor_spikes(xcor) if pos != start)
        for pos, val in zip(xspk, xcor.loc[xspk, xcor.columns[0]]):
            # Get associated list
            prop = props.get(pos)
            if prop is None:
                prop = list()
                props[pos] = prop
            # Append proportion
            prop.append((val, pid))
    # Sort the spikes by decreasing match proportions
    for prop in props.values():
        prop.sort(key=lambda x: x[0], reverse=True)
    # NOTE: Debug (return proportions)
    return props
