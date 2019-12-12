import collections
import math
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

    def slide(self, seg_b=None, seg_a=None, no_out=False):
        """ Compute the cross-correlation of B over A for every overlapping offsets.

        Parameters
        ----------
        seg_b: `tuple` of two `int`, optional
            Segment of signal B to select, all signal B if `None`.
        seg_a: `tuple` of two `int`, optional
            Segment of signal A to select, all signal A if `None`.
        no_out: :obj:`bool`
            Whether not to map offsets for which the two signals do not fully overlap.

        Returns
        -------
        generator of (offset, summable)
            Map between overlapping offset and associated cross-correlation.

        """
        # Compute effective lengths
        len_a = self.len_a if seg_a is None else seg_a[1] - seg_a[0]
        len_b = self.len_b if seg_b is None else seg_b[1] - seg_b[0]
        # Make generator
        return ((offset, self.compute(offset, seg_b, seg_a)) for offset in range(min(0, len_a - len_b) if no_out else (1 - len_b), (max(0, len_a - len_b) + 1) if no_out else len_a))

# ---------------------------------------------------------------------------- #
# Product functions

def product_harmorhythm(meas_a, meas_b):
    """ Hard onset and pitch matching product function.

    Parameters
    ----------
    meas_a: :obj:`pandas.DataFrame`
        Measure A, internal format.
    meas_b: :obj:`pandas.DataFrame`
        Measure B, internal format.

    Returns
    -------
    float
        How many times at least two notes from the two measures start at the same time and match pitches.
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
        Signal generator, producing tuples of (index, value) by strictly increasing index.

    Returns
    -------
    generator of `int`
        Indices of all the (rising edge) spikes.

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

def detect_structure(acor, trig=None, prec=10):
    """ Detect the form of a signal given its auto-correlation.

    Parameters
    ----------
    acor: :obj:`CrossCorrelation`
        Auto-correlation of the signal to use.
        For a piece, you want to use the "harmo-rhythm" auto-correlation.
    trig: :obj:`float`, optional
        Match trigger factor, fraction of matching notes above which two segments are considered to belong from the same part.
        If not specified, it will be line-searched until the output contains at least two parts with the least different parts.
    prec: :obj:`int`, optional
        "Precision" to use when line-searching 'trig'.

    Returns
    -------
    `list` of `int`
        List of integers representing the form of the piece.
    `float`
        Trigger used or found.

    """
    if trig is None:
        best  = None
        trig  = 0.5
        level = 1
        for trig in range(1, prec):
            trig /= prec
            # Compute with current trigger
            struct = detect_structure(acor, trig=trig)
            ccmp = len(set(struct))
            clen = len(struct)
            # Check if better
            if ccmp > 1 and (best is None or ccmp < bcmp or (ccmp == bcmp and clen >= blen)):
                best = (struct, trig)
                bcmp = ccmp
                blen = clen
        if best is None:
            return struct, trig
        else:
            return best
    # Run with non-None 'trig'
    assert acor.len_a == acor.len_b, "Expected an auto-correlation, got cross-correlation between signals of different lengths"
    # Make spike position generator
    spikes = detect_spikes((off, val) for (off, val) in acor.slide() if off >= 0)
    # Gather the pattern segments
    patterns = dict() # pid -> (start, stop, size)
    start = 0
    for pid, stop in enumerate(spikes):
        pos = (start, stop)
        patterns[pid] = (*pos, acor.compute(start, pos))
        start = stop
    pos = (start, acor.len_a)
    patterns[pid + 1] = (*pos, acor.compute(start, pos))
    # Compute total score and which segments match, for each pid
    scores   = dict((pid, 0.) for pid in patterns.keys()) # pid -> total score
    explains = dict((start, (stop - start, [pid])) for pid, (start, stop, _) in patterns.items()) # segment -> (length, list of pids)
    for ref, dst in patterns.items():
        len_dst = dst[1] - dst[0]
        for pid, src in patterns.items():
            # Ignore native pattern
            if pid == ref:
                continue
            # Check if pattern roughly fit
            len_src = src[1] - src[0]
            if abs(len_src - len_dst) > 1:
                continue
            # Compute score
            score = acor.compute(dst[0], src[:2]) / src[2]
            scores[pid] = scores.get(pid, 0) + score
            if score >= trig:
                explains[dst[0]][1].append(pid)
    # Keep only highest-scoring pid per segment
    segments = list((segment, (length, max(pids, key=lambda pid: scores[pid]))) for segment, (length, pids) in explains.items())
    del explains
    segments.sort(key=lambda x: x[0])
    # Simplification (find constrains)
    constrains = dict() # pid -> (size, single)
    prev_pid = None
    prev_len = None
    for segment, (this_len, this_pid) in segments:
        if prev_pid is None:
            prev_pid = this_pid
            prev_len = this_len
        else:
            if prev_pid == this_pid:
                prev_len += this_len
            else:
                if prev_pid in constrains:
                    constrains[prev_pid] = (math.gcd(prev_len, constrains[prev_pid][0]), False)
                else:
                    constrains[prev_pid] = (prev_len, True)
                prev_pid = this_pid
                prev_len = this_len
    if prev_pid in constrains:
        spec_len = max(math.gcd(prev_len - i, constrains[prev_pid][0]) for i in range(2))
        constrains[prev_pid] = (spec_len, False) # NOTE: Special reduce length as end might be truncated due to positive offset inside the first measure
    else:
        constrains[prev_pid] = (prev_len, True)
    # Simplification (make final structure)
    struct = list()
    pidmap = dict() # Pid number mapping
    def emit(pid):
        if pid in pidmap:
            struct.append(pidmap[pid])
        else:
            let = chr(ord("A") + len(pidmap))
            pidmap[pid] = let
            struct.append(let)
    cursor = None
    for start, (_, pid) in segments:
        # Get constrains for current pid
        pid_length, pid_single = constrains[pid]
        # Special case: first iteration
        if cursor is None:
            emit(pid)
            cursor = pid_length
            single = pid_single
            continue
        # Segment already accounted for
        if start < cursor:
            continue
        # Merge if single and prev single
        if single and pid_single:
            cursor += pid_length
            continue
        # Just emit pid and progress
        emit(pid)
        single = pid_single
        cursor += pid_length
    return struct
