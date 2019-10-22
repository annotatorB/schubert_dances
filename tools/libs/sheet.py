# -*- coding: utf-8 -*-
"""
Our custom-format, simplified sheet music class.
"""

import fractions
import pandas
import pickle

# ---------------------------------------------------------------------------- #
# Sheet music and section storage classes

class Sheet:
    """ Sheet music storage class.

    Attributes
    ----------
    _sections : list of pandas.DataFrame
        List of sections with fixed time signature.
        The order of the elements in this list matters,
        as the index of each element are used in attribute 'repeats'.
    _repeats : list of int
        List of section indexes to be repeated when playing the partition.

    Notes
    -----
    Compared to a standard music sheet:
    - repetitions of (contiguous) sections are specified separately.
    - many informative elements (like ties between notes) are optionally stored.

    See Also
    --------
    Section : section storage class.

    """

    def __init__(self):
        """ Initialize an empty sheet.
        """
        self._sections =

    def assert_format(self):
        """
        """
        pass

class Section(pandas.DataFrame):
    """ Section of notes storage class.

    A section is merely a pandas.DataFrame.

    Mandatory columns
    -----------------
    note : str
        Note letter, one of {"A", "B", ..., "G"}.
    octave : int
        Octave number, any integer.
    accidental : int
        Accidental value, in particular: -1 for flat, 0 for natural, 1 for sharp.
    start : fractions.Fraction
        Non-negative start time point (in beats), relative to the beginning of the section.
    duration : fractions.Fraction
        Positive duration (in beats).

    Optional columns
    ----------------
    velocity : int in [1 .. 127]
        Velocity at which the note must be played.
    hand : int
        Which hand is supposed to play this note.
        (Meaning to be formalized, e.g.: 0 for unknown, -1 for left, 1 for right.)

    See Also
    --------
    Sheet : sheet music storage class.

    """

    def __init__(self, signature, *args, **kwargs):
        """ Section constructor.

        Parameters
        ----------
        signature : tuple of two positive int
            Time signature of the section.
        *args, **kwargs
            Arguments forwarded to the parent constructor.

        """
        # Parent constructor
        super().__init__(*args, **kwargs)
        # Set
        self._signature = signature

    @property
    def signature():
        """ Access the read-only signature.

        Returns
        -------
        tuple of two positive int
            Time signature of the section.

        """
        return self._signature

    def assert_format(self):
        """ Assert that this instance follows the specified format.

        Optional columns are not checked.

        Raises
        ------
        AssertionError
            If the format is not followed, with an explanatory error message.

        """
        # Tuple of mandatory columns, with their respective type or value checker
        mandatories = (
            ("note", lambda x: isinstance(x, str) and ord(x) >= ord("A") and ord(x) <= ord("G")),
            ("octave", int),
            ("accidental", int),
            ("start", lambda x: isinstance(x, fractions.Fraction) and x >= 0),
            ("duration", lambda x: isinstance(x, fractions.Fraction) and x > 0) )
        # Tuple of optional columns, with their respective type/type checker
        optionals = (
            ("velocity", lambda x: isinstance(x, int) and x >= 1 and x <= 127),
            ("hand", int) )
        # Assert that every mandatory column is here and with expected data type/values
        for columns, mandatory in ((mandatories, True), (optionals, False)):
            for name, dtype in columns:
                # Assert existence
                if name not in self.columns:
                    if mandatory:
                        raise AssertionError("missing mandatory column %r in section" % name)
                    continue
                # Assert data type
                if isinstance(dtype, type):
                    dtype = lambda x: isinstance(x, dtype)
                if not self[name].apply(dtype).all():
                    raise AssertionError("some row(s) for %s column %r do(es) not have a valid type/value" % (("mandatory" if mandatory else "optional"), name))

# ---------------------------------------------------------------------------- #
# Load/save sheets with optional checks

def load(sheet, path):
    """
    """
    pass

def save(path):
    """
    """
    pass
