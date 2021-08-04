#includes several functions useful for processing data from the EDF file format. Additions will be made as new file formats are used.
import numpy as np
import pandas as pd
import datetime
import pytz
import math
import csv
# Getting Variable Names and Data
def locate_reformat(FileLocation):
    with open(FileLocation, mode='r') as csv_file:
        DataFile_all = csv.reader(csv_file)
        # Convert to list
        DataFile_all = list(DataFile_all)
    # get variable names
    VariableNames = []
    counter = 0
    for row in DataFile_all:
        if "COLUMN" in row[0]:
            VariableNames.append(row[1])
            counter += 1
    VariableNames = VariableNames[:-1]
    if counter == 0:
        temp = []
        for row in DataFile_all:
            if "NAME" in row:
                counter += 1
                temp.append(item.replace("NAME(" + str(counter) + ")=", ""))
            else:
                continue
        for item in temp:
            VariableNames.append(item.replace("\n", ""))

    # locate Data
    data_start = 0
    for row in DataFile_all:
        data_start += 1
        if "&" in row[0]:
            break
    if data_start == len(DataFile_all):
        row_counter = 0
        break_counter = 0
        for item in DataFile_all:
            row_counter += 1
            if item == "\n":
                break_counter += 1
            if break_counter == counter:
                break
        data_start = row_counter
    # reformat data
    Data_extracolumns = []
    Data_unsplit = []
    # checking the number of rows
    # print(1129-data_start)
    Data_extracolumns = DataFile_all[data_start:]
    # Split variables into tuples with the time as VARIABLE_raw
    # print(Data_ISOPOOH)
    counter = 0
    # take everything from first column
    for item in Data_extracolumns:
        counter += 1
        Data_unsplit.append(item[0])
    # Now each TIme piont is its own item
    Data = []
    for item in Data_unsplit:
        Data.append(item.split())
    # Now all the data is in one 2d list
    # turn it into an array
    Data_array = np.array(Data)
    # turn it into a dataframe
    DataFrame = pd.DataFrame(columns=VariableNames, data=Data_array)
    return Data, DataFrame, VariableNames

# Function for creating time stamp from a reference and based on seconds for epoch time
def time_stamp_maker(reference, epochtime):
    time_change = datetime.timedelta(seconds=float(epochtime))
    time_stamp = time_change + reference
    return time_stamp

#Bin
def Bin_15minutes(Data, Variable_Names):
    Full_Data_array = np.empty([1, len(Variable_Names)])
    # Loop for one hour period at a time. So every 4 rows
    for hour in range(Data["Hour"].min(), Data["Hour"].max() + 1):
        # creates leftmost columns of these 4 rows that represnt one hour
        temp_array = np.array([[hour, 0],
                                   [hour, 1],
                                   [hour, 2],
                                   [hour, 3]])
        # loops through the variables to add columns to the 4x2 array above.
        for Variable in Variable_Names[2:]:
            # creates column that is reset then added to the array
            column = np.empty([4, 1])
            for q in range(4):
                # creates a set of values for the variable at each quart and hour
                Quart = [Data[Variable][x] for x in range(len(Data[Variable])) if Data["Quart"][x] == q \
                             and Data["Hour"][x] == hour and math.isnan(float(Data[Variable][x])) != True \
                         and float(Data[Variable][x]) >= 0]
                if len(Quart) == 0:
                    column[q] = float("NaN")
                else:
                    Quart_avg = np.nanmean(np.array(Quart).astype(float))
                    column[q] = Quart_avg
                # data for each of the 4 bins for an hour are stored in one list
                # here the columns are added to the array
            temp_array = np.append(temp_array, column, axis=1)
            # once each variable has been gone through for that hour, the set of 4 rows is added to the larger array \
            # then it goes to the next 4 rows that overall represent an hour
        Full_Data_array = np.append(Full_Data_array, temp_array, axis=0)

    Headings = ["Hour", "Quart"]
    Headings.extend(Variable_Names[2:])

    qstart = int(Data["Quart"][0])
    Bin_Frame = pd.DataFrame(columns=Headings, data=Full_Data_array[1+qstart:, ])
    Bin_Frame["TM"] = Bin_Frame["Hour"] + Bin_Frame["Quart"] / 4
    return Bin_Frame

#Total Function
def EDF_DataProcessor(FileLocation):
    Data, DataFrame, VariableNames = locate_reformat(FileLocation)

    # Create variable for the time
    reference_time = datetime.datetime(2000, 1, 1, 0, 0, 0)
    timezone = pytz.timezone("UTC")
    reference_time = timezone.localize(reference_time)

    time_unfiltered = []

    for rows in Data:
        temp_time = time_stamp_maker(reference_time, rows[0])
        time_unfiltered.append(temp_time)
    # adding datetime for all
    DataFrame["DateTime"] = time_unfiltered
    ExperimentStart = time_unfiltered[0]
    # add quart and hour marks to dataframe
    Hour = [DataFrame["DateTime"][x].hour for x in range(len(DataFrame["DateTime"]))]
    Quart = [np.floor(DataFrame["DateTime"][x].minute / 15) for x in range(len(DataFrame["DateTime"]))]
    DataFrame["Hour"] = Hour
    DataFrame["Quart"] = Quart

    # Bin Function but with filteration
    Name_of_final_data = Bin_15minutes(DataFrame, VariableNames)
    return Name_of_final_data, ExperimentStart
