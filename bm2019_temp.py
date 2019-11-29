"""
Temperature data for Burning Man 2019
py3.8, using dataclasses

Eventually show the resulting plotly html file in a github.io page
https://mpesavento.github.io/phage_temperature_2019/

"""
import os
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotly import graph_objs as go
from plotly.offline import plot
from plotly.tools import make_subplots


try:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError as e:
    # if we aren't running this as a file, default to a known location
    # clearly this will break on most other systems, so update as necessary
    ROOT_DIR = "/Users/mpesavento/src/phage_temperature_2019"

# repository location of the data
DATA_PATH = os.path.join(ROOT_DIR, "data")
# where we save the figure
FIGURE_PATH = os.path.join(ROOT_DIR, "figures")

PACIFIC_TZ = "US/Pacific"
UTC_TZ = "UTC"

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
    data_tz: str=PACIFIC_TZ
    display_tz: str=PACIFIC_TZ
    tags: list=field(default_factory=list)
    # data: pd.DataFrame=field(default_factory=_read_csv)

    @staticmethod
    def _f2c(f):
        """Fahrenheit to Celsius"""
        return (f - 32) * (5.0 / 9.0)

    @staticmethod
    def _c2f(c):
        """Celsius to Fahrenheit"""
        return c * (9.0 / 5.0) + 32


    def load_data(self, header=0):
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

        # align timestamps
        self.data["datetime"] = pd.to_datetime(self.data["datetime"])
        print("Tz: {}->{}".format(self.data_tz, self.display_tz))
        self.data["datetime"] = self.data["datetime"].dt.tz_localize(self.data_tz)\
            .dt.tz_convert(self.display_tz)

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
        tags = ["AC?"],
        data_tz = UTC_TZ
    ),
    TemperatureSource(
        filename = 'burningman_2019_bunnie_shiftpod.csv',
        recording_location = "shiftpod1",
        owner = "bunnie",
        tags = ["AC"],
        data_tz = UTC_TZ
    ),
]



def load_data_files(data_sources: list=REGISTERED_DATA):
    for source in data_sources:
        print(source.filename)
        source.load_data()


def get_source_data_trace(source, units="F"):
    if not hasattr(source, "data"):
        source.load_data()

    field = f"temperature {units}"
    trace = go.Scatter(
        x=source.data["datetime"],
        y=source.data[field],
        mode="lines",
        name="{} - {}".format(source.owner, source.recording_location)
    )
    return trace


def plot_temperatures(data_sources, units="F"):
    traces = [get_source_data_trace(source) for source in data_sources]
    fig = go.Figure(
        data=traces,
        layout=dict(
            width=1200,
            height=800,
            title="Dwelling temperature - BRC 2019",
            xaxis=dict(title="date"),
            yaxis=dict(title=f"temperature {units}")
        )
    )
    out_filename = os.path.join(FIGURE_PATH, "phage_temperature_2019.html")
    plot(fig, filename=out_filename)


if __name__ == "__main__":
    load_data_files(REGISTERED_DATA)
    plot_temperatures(REGISTERED_DATA)

