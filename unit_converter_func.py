def unit_converter(Dataset, units_to_convert, formula):
    R=82.05746
    N_A=6.02214076*10**23
    mbar_atm=1013.25
    import numpy as np
    import pandas as pd
    import datetime
    import math
    Dataset_altered = Dataset.copy()
    for measurement in Dataset_altered.columns:
        if measurement in units_to_convert:
            if formula == "cm3 to ppb":
                Dataset_altered[measurement] = [(Dataset[measurement][x] * R * Dataset["T"][x] * mbar_atm * 10**9) / \
                                (N_A * Dataset["P"][x]) for x in range(len(Dataset[measurement]))]
            if formula == "ppm to ppb":
                Dataset_altered[measurement] = [float(Dataset[measurement][x]*1000) for x in range(len(Dataset[measurement]))]
            #Can add other conversions here if necessary
        else:
            continue
    return Dataset_altered