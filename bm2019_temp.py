"""
Temperature data for Burning Man 2019
py3.8, using dataclasses

"""
import os
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

try:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError as e:
    # if we aren't running this as a file, default to a known location
    # clearly this will break on most other systems, so update as necessary
    ROOT_DIR = "/Users/mpesavento/src/phage_temperature_2019"

# repository location of the data
DATA_PATH = os.path.join(ROOT_DIR, "data")

@dataclass
class TemperatureSource():
    """
    Data class for metadata associated with a specific temperature recording
    """
    filename: str
    recording_location: str
    path: str=DATA_PATH
    owner: str="someone"
    datetime_col: str='datetime'
    temp_col: str='temperature'
    temp_units: str="C"
    tags: list=field(default_factory=list)
    # data: pd.DataFrame=field(default_factory=_read_csv)

    def _f2c(f):
        return (f - 32) * (5.0 / 9.0)

    def _c2f(c):
        return c * (9.0 / 5.0) + 32


    def read_csv(self, header=0):
        use_cols = [self.datetime_col, self.temp_col]
        self.data = pd.read_csv(
            os.path.join(self.path, self.filename),
            header=header,
            encoding="utf8",
            usecols=use_cols,
        )[use_cols]
        # make the column naming consistent
        self.data.rename(columns={
            self.datetime_col: 'datetime',
            self.temp_col: f'temperature {self.temp_units}'}, inplace=True)
        self.data[self.datetime_col] = pd.to_datetime(self.data[self.datetime_col])
        # add both conversions
        if self.temp_units == "C":
            self.data['temperature F'] = self.data[
            f'temperature C'].apply(self._c2f)
        elif self.temp_units == "F":
            self.data['temperature C'] = self.data[
            f'temperature F'].apply(self._f2c)
        # TODO(mjp) add kelvin -- i'm lazy
        else:
            print("invalid unit selected, unable to convert")

# metadata store for data origin and additional information
REGISTERED_DATA = [
    TemperatureSource(
        filename = 'burningman_2019_mjp_shiftpod2.csv',
        recording_location = "shiftpod2",
        owner = "mjp",
        tags = ["shade", "swampcooler"]
    ),
    TemperatureSource(
        filename = 'burningman_2019_pnelson_shiftpod2_blastshield_swampcooler.csv',
        recording_location = "shiftpod2",
        owner = "pnelson",
        tags = ["shade", "swampcooler", "blastshield"]
    ),
    TemperatureSource(
        filename = 'BurningMan2019 - Altitude Lounge 845&C.csv',
        recording_location = "outdoors",
        owner = "Altitude Lounge",
        datetime_col = "Time",
        temp_col = "Outdoor Temperature (F)",
        temp_units = "F",
        tags = []
    ),
    TemperatureSource(
        filename = 'burningman_2019_myq_h12yurt.csv',
        recording_location = "h12yurt",
        owner = "myq",
        tags = ["AC?"]
    ),
    TemperatureSource(
        filename = 'burningman_2019_bunnie_shiftpod.csv',
        recording_location = "shiftpod1",
        owner = "bunnie",
        tags = ["AC"]
    ),
]



def load_data_files(data_sources: list=REGISTERED_DATA):
    for source in data_sources:
        print(source.filename)
        source.read_csv()



if __name__ == "__main__":
    load_data_files()
    REGISTERED_DATA[2].data.head()

