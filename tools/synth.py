# -*- coding: utf-8 -*-
"""
Essentially a very limited wrapper around FluidSynth, playing notes when requested.

Examples
--------
A working example, provided both libsynthfluid and "my_piano_soundfont.sf2"
have been properly installed and downloaded.
To download piano SoundFonts, see: https://sites.google.com/site/soundfonts4u/

>>> import synth, time

>>> # Load the default FluidSynth library and a given SoundFont file
>>> piano = synth.FluidSynth().make("my_piano_soundfont.sf2")

>>> # Press a flat A4 then release it after 0.5 second
>>> key = synth.note_midi("A4") - 1  # +1 makes sharp, -1 makes flat
>>> piano.press(key)
>>> time.sleep(0.5)
>>> piano.release(key)

>>> # Play all the A between A7 to A0 (included)
>>> for i in range(7, -1, -1):
...     piano.press(synth.note_midi("A%d" % i))
...     time.sleep(0.15)
...
>>> # Silence all currently playing notes after 2 seconds
>>> time.sleep(2)
>>> piano.silence()
>>> time.sleep(0.5)

>>> # Play all the "blues" notes from C4 to C5 (included)
>>> base  = synth.note_midi("C4")
>>> delta = (0, 3, 5, 6, 7, 10, 12)
>>> piano.press(base + delta[0])
>>> for i in range(len(delta) - 1):
...     time.sleep(0.05 * (delta[i + 1] - delta[i]) + 0.05)
...     piano.press(base + delta[i + 1])
...
>>> for d in reversed(delta[:-1]):
...     time.sleep(0.1)
...     piano.press(base + d)
...
>>> time.sleep(2)
>>> piano.silence()
>>> time.sleep(0.5)

"""

import ctypes
import ctypes.util

# ---------------------------------------------------------------------------- #
# Switch between note name and MIDI number

def note_midi(name):
    """ Compute the MIDI number associated with the given note name.

    Parameters
    ----------
    name : str
        Note name, format: /[ABCDEFG]-?[0-9]+/.

    Returns
    -------
    int
        Associated MIDI number.
        Add/remove 1 to it for a sharp/flat note.

    See Also
    --------
    midi_note : for the opposite operation.

    """
    note = (ord(name[0]) - ord("A") - 2) % 7
    base = int(name[1:])
    return (12 if note < 3 else 11) + 12 * base + 2 * note

def midi_note(midi):
    """ Compute the note name associated with the given MIDI number.

    Parameters
    ----------
    midi : int
        MIDI number.

    Returns
    -------
    str
        Associated note name, international pitch notation without accidental.
        If a flat note was given, return the name of the note before.

    See Also
    --------
    note_midi : for the opposite operation.

    """
    raise NotImplementedError

# ---------------------------------------------------------------------------- #
# FluidSynth library interface

class FluidSynth:
    """ Wrapper to the FluidSynth library and some of its functions.
    """

    class _Instance:
        """ Instance manager (settings, synth and audio driver), play notes on demand.
        """

        def __init__(self, fluidsynth, soundfont, settings):
            """ Instantiate the FluidSynth settings, synth and audio driver, then load the given SoundFont.

            Parameters
            ----------
            fluidsynth : FluidSynth
                Wrapper to the FluidSynth library to use.

            See Also:
            ---------
            FluidSynth.make : for the remaining arguments.

            """
            # Register the instance first
            self._fluidsynth = fluidsynth
            # Make the settings
            self._settings = fluidsynth.new_fluid_settings()
            if self._settings is None:
                raise RuntimeError("Unable to create a new FluidSynth settings instance")
            # Set the settings
            for key, val in settings.items():
                # Check 'val' and select associated function
                cls = type(val)
                if cls is str:
                    post = "str"
                    sval = val.encode()
                elif cls is float:
                    post = "num"
                    sval = val
                elif cls is int:
                    post = "int"
                    sval = val
                else:
                    raise ValueError("Unsupported FluidSynth setting value %r for key %r" % (val, key))
                # Set setting and check if error
                res = getattr(fluidsynth, "fluid_settings_set%s" % post)(self._settings, key.encode(), sval)
                if res != 1:
                    raise RuntimeError("Unable to set FluidSynth setting value %r (%s) for key %r, error code %d" % (val, post, key, res))
            # Make the synth with the settings
            self._synth = fluidsynth.new_fluid_synth(self._settings)
            if self._synth is None:
                raise RuntimeError("Unable to create a new FluidSynth synth instance")
            soundfont = str(soundfont)
            res = fluidsynth.fluid_synth_sfload(self._synth, str(soundfont).encode(), 1)
            if res < 0:
                raise RuntimeError("Unable to load SoundFont %r into the FluidSynth synth instance, error code %d" % (soundfont, res))
            # Make the audio driver with the settings and synth
            self._audio_driver = fluidsynth.new_fluid_audio_driver(self._settings, self._synth)
            if self._audio_driver is None:
                raise RuntimeError("Unable to create a new FluidSynth synth instance")
            # Set of currently playing notes (for silence)
            self._playing = set()

        def __del__(self):
            """ Destroy the managed instances.
            """
            # Get the library wrapper
            fluidsynth = getattr(self, "_fluidsynth", None)
            if fluidsynth is None: # Nothing to do
                return
            # Destroy the managed instances (in order)
            for name in ("audio_driver", "synth", "settings"):
                instance = getattr(self, "_%s" % name, None)
                if instance is None:
                    continue
                getattr(fluidsynth, "delete_fluid_%s" % name)(instance)

        def press(self, key, vel=100):
            """ Start playing a note.

            Parameters
            ----------
            key : int
                MIDI number to start playing.
            vel : int, optional
                Velocity, i.e. number between 0 (= stop) and 127 (included).

            """
            if vel > 0:
                if self._fluidsynth.fluid_synth_noteon(self._synth, 0, key, vel) < 0:
                    raise RuntimeError("Unable to play key %d with velocity %d" % (key, vel))
                self._playing.add(key)
            else:
                self.release(key)

        def release(self, key):
            """ Stop playing a note.

            Parameters
            ----------
            key : int
                MIDI number to stop playing.

            """
            self._fluidsynth.fluid_synth_noteoff(self._synth, 0, key) # Do not check as this can return -1 if waited long enough
            self._playing.discard(key)

        def silence(self):
            """ Stop all playing notes.
            """
            for key in list(self._playing):
                self.release(key)

    # Imported functions, map <function name> -> (<return type or 'None'>, (<input type>*))
    _imported = {
        "new_fluid_settings": (ctypes.c_void_p, ()),
        "fluid_settings_setint": (ctypes.c_int, (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int)),
        "fluid_settings_setnum": (ctypes.c_int, (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_double)),
        "fluid_settings_setstr": (ctypes.c_int, (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p)),
        "delete_fluid_settings": (None, (ctypes.c_void_p,)),
        "new_fluid_synth": (ctypes.c_void_p, (ctypes.c_void_p,)),
        "fluid_synth_sfload": (ctypes.c_int, (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int)),
        "fluid_synth_noteon": (ctypes.c_int, (ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int)),
        "fluid_synth_noteoff": (ctypes.c_int, (ctypes.c_void_p, ctypes.c_int, ctypes.c_int)),
        "delete_fluid_synth": (None, (ctypes.c_void_p,)),
        "new_fluid_audio_driver": (ctypes.c_void_p, (ctypes.c_void_p, ctypes.c_void_p)),
        "delete_fluid_audio_driver": (None, (ctypes.c_void_p,)), }

    def __init__(self, library="fluidsynth"):
        """ Load the library and "bind" the imported functions.

        Once loaded, the imported functions are available as members.

        Parameters
        ----------
        library : str, optional
            Name or path to the FluidSynth library.

        """
        # Load library
        lib = ctypes.CDLL(ctypes.util.find_library(library))
        # Bind imported functions
        for name, params in type(self)._imported.items():
            # Resolve parameters
            restype, argtypes = params
            # Resolve foreign function and bind name to it
            setattr(self, name, ctypes.CFUNCTYPE(restype, *argtypes)((name, lib)))
        # Finalization
        self._lib = lib

    def make(self, soundfont, settings={"audio.driver": "pulseaudio"}):
        """ Make a new instance manager with the given settings and SoundFont.

        Parameters
        ----------
        soundfont : str or pathlib.Path (or equivalent)
            Path to the SoundFont file to use.
        settings : dict, optional
            Dictionary of `str` -> {`str`, `float`, `int`} to use as settings.

        Returns
        -------
        FluidSynth._Instance
            An instance manager, ready to be used to play notes.

        """
        # Forward the call
        return type(self)._Instance(self, soundfont, settings)
