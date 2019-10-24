# -*- coding: utf-8 -*-
"""
Our custom-format, simplified sheet music class.
"""

import fractions
import pandas
import pathlib
import pickle

# ---------------------------------------------------------------------------- #
# Sheet music and section storage classes

class Sheet:
    """ Sheet music storage class.

    Attributes
    ----------
    sections : list of pandas.DataFrame
        List of sections in played order, each possibly appearing several times.

    Notes
    -----
    Compared to a standard music sheet:
    - repetitions of (contiguous) sections are specified separately.
    - many informative elements (like ties between notes) are optionally stored.

    See Also
    --------
    sheet.Section : section storage class.

    Examples
    --------
    These examples illustrate how to build a sheet with repetitions of sections.
    Once the sheet and sections are built, it is then:
    - easy to playback a sheet, by just iterating over the stored sections.
    - possible to iterate over the sections as they (plausibly) were on paper, e.g.:
        - A B B C D E D E F => A 𝄆 B 𝄇 C 𝄆 D E 𝄇 F
        - A B C B D E       => A 𝄆 B C¹ 𝄇 D² E
        - A B C A D E A C F => 𝄆 A B¹ C¹³ D² E² 𝄇 F³

    >>> # Make a new sheet
    >>> my_sheet = sheet.Sheet()

    >>> # Make three sections
    >>> A, B, C = (sheet.Section(signature=(4, 4)) for _ in range(3))
    >>> # Parse and fill the columns of the sections (see 'help(sheet.Section)' for the format)
    >>> # ...
    >>> # Optional validity asserts each section once they have been fully built
    >>> for section in (A, B, C):
    ...     section.assert_format()
    ...
    >>> # Make the repetition A-B-A-C-C
    >>> for section in (A, B, A, C, C):
    ...     my_sheet.append(section)
    ...

    >>> # Iterate over the sections in playing order (i.e.: A-B-A-C-C)
    >>> for section in my_sheet.as_played():
    ...     pass
    ...
    >>> # Iterate over the sections in (plausible) written order
    >>> for section, (voltas, rep_begin, rep_end) in my_sheet.as_written():
    ...     # As the structure is (𝄆 A B¹ 𝄇𝄆 C² 𝄇), the loop will iterate over:
    ...     # - A, ([], True, False)
    ...     # - B, ([1], False, True)
    ...     # - C, ([-2], True, True)  <- volta value from previous pair of repetition bars is noted as negative (if any)
    ...     pass
    ...

    >>> # Save and load again the sheet
    >>> sheet.save(my_sheet, "my_sheet.sht")
    >>> my_sheet = sheet.load("my_sheet.sht")
    >>> my_sheet.assert_format()  # Optional, checks both the sheet and its sections

    """

    def __init__(self):
        """ Initialize an empty sheet.
        """
        self.sections = list()

    def append(self, section):
        """ Append/repeat a section into the sheet.

        Parameters
        ----------
        section : :obj:`sheet.Section`
            Section to append to the sheet.

        Returns
        -------
        Section
            The section passed as parameter, untouched

        """
        # Append section
        self.sections.append(section)
        # Return passed section
        return section

    def as_played(self):
        """ Return a list over the sections in played order.

        Returns
        -------
        list of Section
            List over the sections in played order.

        Notes
        -----
        The behavior is undefined if the sheet is modified while using the returned value.

        """
        return self.sections

    def as_written(self):
        """ Make a list over the sections in written order.

        Returns
        -------
        list of tuple of (Section, tuple of (list of int, bool, bool))
            List over the sections in written order, with additional information.
            The additional tuple of information contains:
            - The list of voltas (positive integers) of the section
            - Whether the section is preceeded by a "begin" repetition bar
            - Whether the section is followed by an "end" repetition bar

        Raises
        ------
        RuntimeError
            When the notation to achieve the existing repetition is unknown.

        Notes
        -----
        The behavior is undefined if the sheet is modified while using the returned value.

        A (probably not representable) sheet with reordered sections in a repetition (e.g. ABCACB)
        will not raise an error and be consistently output as in the first repetition (e.g. 𝄆 ABC 𝄇).

        """
        # Recover the position of each section instance, in first seen order
        poses = list()  # Cannot be a 'dict' as a DataFrame is not hashable
        for i, section in enumerate(self.sections):
            # Make or get list of positions for the current section
            for sec, pos in poses:
                if sec is section:
                    break
            else:
                pos = list()
                poses.append((section, pos))
            # Update the list of positions for the current section
            pos.append(i)
        # Build the result list from the position of each section instance
        result = list()
        repeat = None  # Current controling repeat position block, if any
        lvolta = 0     # Last volta value from previous repetition
        def consume_lvolta():
            nonlocal lvolta
            volta  = list() if lvolta == 0 else [-lvolta]
            lvolta = 0
            return volta
        for idx, (sec, pos) in enumerate(poses):
            if repeat is None: # Outside any repetition
                if pos[-1] - pos[0] + 1 > len(pos): # Has repetition(s) with at least one other section
                    result.append((sec, (consume_lvolta(), True, False)))
                    repeat = pos
                    lvolta = len(pos)
                else: # No other section involved
                    if len(pos) == 1:
                        result.append((sec, (consume_lvolta(), False, False)))
                    elif len(pos) == 2:
                        result.append((sec, (consume_lvolta(), True, True)))
                    else:
                        raise RuntimeError("unable to write more than two repetitions using the same section")
            else: # Inside a repetition
                # Solve the number of time the section appears per volta
                seens = [0] * len(repeat)
                for p in pos:
                    seens[max(volta if p > repeat[volta] else 0 for volta in range(len(repeat)))] += 1
                # Solve the voltas for this section
                voltas = list()
                if min(seens) == 0: # If sometimes not repeated
                    for vid in range(len(seens)):
                        if seens[vid] == 1:
                            voltas.append(vid + 1)  # +1 simply because a volta starts counting at 1
                        elif seens[vid] > 1:
                            raise RuntimeError("unable to write section such that it is repeated more than once from inside a single repetition")
                # Emit the section
                idx += 1
                is_last = True if idx >= len(poses) else poses[idx][1][0] > repeat[-1]  # Next section starts after the last repeated position
                result.append((sec, (voltas, False, is_last)))
                if is_last:
                    repeat = None
        # Return the generated list
        return result

    def assert_format(self):
        """ Assert that this instance follows the specified format.

        Raises
        ------
        AssertionError
            If the format is not followed, with an explanatory error message.
            This is raised even when not in debug mode (i.e. '__debug__ == False').

        """
        global Section
        # Assert section is a list
        if not isinstance(self.sections, list):
            raise AssertionError("member 'sections' is not a list, it is a %s" % type(self.sections).__qualname__)
        # Assert each section
        for i, section in enumerate(self.sections):
            if not isinstance(section, Section):
                raise AssertionError("section %d in member 'sections' is not a Section, it is a %s" % (i, type(section).__qualname__))
            section.assert_format()

class Section(pandas.DataFrame):
    """ Section of notes storage class.

    A section is merely a pandas.DataFrame, augmented with a time signature.
    It is to be though as "the ink on the paper" for a continuous segment of notes,
    and absolutely not as a period; finding periods is left to subsequent analysis.

    Mandatory columns:
    - note (str)
        Note letter, one of {"A", "B", ..., "G"}.
    - octave (int)
        Octave number, any integer.
    - accidental (int)
        Accidental value, in particular: -1 for flat, 0 for natural, 1 for sharp.
    - start (:obj:`fractions.Fraction`)
        Non-negative start time point (in beats), relative to the beginning of the section.
    - duration (:obj:`fractions.Fraction`)
        Positive duration (in beats).

    Optional columns:
    - velocity (int in [1 .. 127])
        Velocity at which the note must be played.
    - hand (int)
        Which hand (or more generally which voice) is supposed to play this note.
        (To be formalized, probably something like: 0 for unknown, -1 for left, 1 for right.)

    A final silence (to play at the end of the section) is available in the member 'silence'.

    Additional metadata can be stored, available in the member dictionary 'metadata'.
    They can be used to specify details that do not directly impact the produced playback,
    as for instance if the section begins (or ends) with a double bar, etc.

    See Also
    --------
    sheet.Sheet : sheet music storage class.

    """

    def __init__(self, signature, silence=fractions.Fraction(0, 1), metadata=None, **kwargs):
        """ Section constructor.

        Parameters
        ----------
        signature : tuple of two positive int
            Time signature of the section.
        silence : :obj:`fractions.Fraction`, optional
            Silence duration to play at the very end of the section
        metadata : dict or NoneType, optional
            Additional metadata dictionary, or None for none.
        **kwargs
            Keyword arguments forwarded to the parent constructor.
            Notes:
            · If the 'columns' keyword argument is passed (expected a list),
              the given values are appended to the list of mandatory columns.
            · If the 'data' keyword argument is passed,
              no 'columns' argument is forwarded by default and no check is made.

        """
        # Assertions
        assert isinstance(signature, tuple) and len(signature) == 2 and all(isinstance(x, int) and x > 0 for x in signature), "invalid time signature, expected a tuple of two positive int, got %r" % (signature,)
        assert isinstance(silence, fractions.Fraction) and silence >= 0, "invalid silence duration, expected a non-negative fraction, got %r" % (silence,)
        assert metadata is None or isinstance(metadata, dict), "invalid metadata, expected a dictionary or 'None', got %r" % (metadata,)
        # Parent constructor
        if "data" not in kwargs:
            kwargs["columns"] = ["note", "octave", "accidental", "start", "duration"] + kwargs.get("columns", list())
        super().__init__(**kwargs)
        # Set the signature
        self.__dict__["_signature"] = signature
        self.__dict__["silence"]    = silence
        self.__dict__["metadata"]   = dict() if metadata is None else metadata

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
            This is raised even when not in debug mode (i.e. '__debug__ == False').

        """
        # Tuple of mandatory columns, with their respective type or value checker
        mandatories = (
            ("note", lambda x: isinstance(x, str) and (ord(x) >= ord("A") and ord(x) <= ord("G"))),
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
                    checker = lambda x: isinstance(x, dtype)
                else:
                    checker = dtype
                if not self[name].apply(checker).all():
                    raise AssertionError("some row(s) for %s column %r do(es) not have a valid type/value" % (("mandatory" if mandatory else "optional"), name))
        # Check that the note start timestamps are monotonically increasing, starting no before than 0
        clock = fractions.Fraction(0, 1)
        for start in self["start"]:
            if start < clock:
                raise AssertionError("note start timestamps are not monotonically increasing or start before clock 0")
            clock = start

# ---------------------------------------------------------------------------- #
# Load and save sheets

def load(path_or_fd):
    """ Load a sheet from a file.

    Parameters
    ----------
    path : str or pathlib.Path (or equivalent)
        Path to the file to load from.

    Returns
    -------
    Sheet
        Loaded sheet instance.

    """
    if any(isinstance(path_or_fd, cls) for cls in (str, pathlib.PurePath)):
        with open(str(path_or_fd), "rb") as fd:
            return pickle.load(fd, fix_imports=False)
    else:
        return pickle.load(path_or_fd, fix_imports=False)

def save(sheet, path_or_fd):
    """ Save a sheet to a file.

    Parameters
    ----------
    sheet : :obj:`sheet.Sheet`
        Instance of the sheet to save.
    path_or_fd : str or pathlib.PurePath, or io.BytesIO (or equivalent)
        Path to the file to save to.

    """
    if any(isinstance(path_or_fd, cls) for cls in (str, pathlib.PurePath)):
        with open(str(path_or_fd), "wb") as fd:
            pickle.dump(sheet, fd, pickle.HIGHEST_PROTOCOL, fix_imports=False)
    else:
        pickle.dump(sheet, path_or_fd, pickle.HIGHEST_PROTOCOL, fix_imports=False)
