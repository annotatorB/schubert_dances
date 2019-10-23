""" Coding rules: Feel free to add!

###############################################################################
#                                  DOCSTRINGS
###############################################################################

NumPy style for use with Sphinx with Napoleon extension (Google style also possible). Rules:

Parameters
----------
parameter1 : :obj:`str`
parameter2 : :obj:`int`
parameter3 : :obj:`pd.DataFrame`, optional

Example
-------
    >>> indented(function, call)
    'Indented result.'

    >>> other_example()
    'Result.'

###############################################################################
#                               ORDER OF THINGS
###############################################################################

Helper functions on top, then the classes. Functions that need the original
score file need to be methods of the class `Score` or of a class that gets
a `Score` object as an argument, e.g. the class `Section`. Things are separated
by 3 blank lines.

###############################################################################
#                               STRING CREATION
###############################################################################

f-Strings avoid type conversion and make the code more readable:
    >>> print(f"The value of this integer is {some_integer_variable}, which is quite {'small' if some_integer_variable < 100 else 'big'}!")
    The value of this integer is 10, which is quite small!

###############################################################################
#                                   LOGGING
###############################################################################

Use logging.debug('Message') abundantly to easily follow the programs workflow.
Use logging.info('Message') for messages that users would want to see in everyday use.

"""
