import pandas as pd
from fractions import Fraction as frac



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
