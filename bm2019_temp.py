"""
Temperature data for Burning Man 2019
py3.8, using dataclasses

Eventually show the resulting plotly html file in a github.io page
https://mpesavento.github.io/phage_temperature_2019/

"""
import os
import sys
from dataclasses import dataclass, field

import pandas as pd
import numpy as np
from astral import Astral

import matplotlib.pyplot as plt
from plotly import graph_objs as go
from plotly.offline import plot


# ------------------------------------------------
# globals

try:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError as e:
    # if we aren't running this as a file, default to a known location
    # clearly this will break on most other systems, so update as necessary
    ROOT_DIR = "/Users/mpesavento/src/phage_temperature_2019"

# repository location of the data
DATA_PATH = os.path.join(ROOT_DIR, "data")
# where we save the figures
FIGURE_PATH = os.path.join(ROOT_DIR, "figures")

# py_tz timezones
PACIFIC_TZ = "US/Pacific"
UTC_TZ = "UTC"

# black rock city: 40.7886° N, 119.2030° W
BLACK_ROCK_CITY_LATITUDE = 40.7886  # northern is positive
BLACK_ROCK_CITY_LONGITUDE = -119.2030  # eastern is positive
BLACK_ROCK_CITY_ELEVATION = 1100  # meters

# bounds on expected temperature range, for plotting
# smarter would be to check the data registry for max/min and fid the nearest order of 10
TEMPERATURE_RANGE = (50, 110)


# ------------------------------------------------
# data classes

@dataclass
class TemperatureSource:
    """
    Data class for metadata associated with a specific temperature recording
    """
    filename: str
    recording_location: str
    path: str = DATA_PATH
    owner: str = "someone"
    datetime_col: str = "datetime"
    temp_col: str = "temperature"
    temp_units: str = "C"
    data_tz: str = PACIFIC_TZ
    display_tz: str = PACIFIC_TZ
    tags: list = field(default_factory=list)
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
        self.data.rename(
            columns={
                self.datetime_col: "datetime",
                self.temp_col: f"temperature {self.temp_units}",
            },
            inplace=True,
        )

        # align timestamps
        self.data["datetime"] = pd.to_datetime(self.data["datetime"])
        # print("Tz: {}->{}".format(self.data_tz, self.display_tz))
        self.data["datetime"] = (
            self.data["datetime"]
            .dt.tz_localize(self.data_tz)
            .dt.tz_convert(self.display_tz)
        )

        # add both conversions
        if self.temp_units == "C":
            self.data["temperature F"] = self.data[f"temperature C"].apply(self._c2f)
        elif self.temp_units == "F":
            self.data["temperature C"] = self.data[f"temperature F"].apply(self._f2c)
        else:
            raise ValueError("invalid temperature unit selected, unable to convert")
        self.data["temperature K"] = self.data[f"temperature C"] - 273.15


# ------------------------------------------------
# data registry
# metadata store for data origin and additional information
REGISTERED_DATA = [
    TemperatureSource(
        filename="burningman_2019_mjp_shiftpod2.csv",
        recording_location="shiftpod2",
        owner="mjp",
        tags=["shade", "swampcooler"],
    ),
    TemperatureSource(
        filename="burningman_2019_pnelson_shiftpod2_blastshield_swampcooler.csv",
        recording_location="shiftpod2",
        owner="pnelson",
        tags=["shade", "swampcooler", "blastshield"],
    ),
    TemperatureSource(
        filename="BurningMan2019 - Altitude Lounge 845&C.csv",
        recording_location="outdoors",
        owner="Altitude Lounge",
        datetime_col="Time",
        temp_col="Outdoor Temperature (F)",
        temp_units="F",
        tags=[],
    ),
    TemperatureSource(
        filename="burningman_2019_myq_h12yurt.csv",
        recording_location="h12yurt",
        owner="myq",
        tags=["AC?"],
        data_tz=UTC_TZ,
    ),
    TemperatureSource(
        filename="burningman_2019_bunnie_shiftpod-clipped.csv",
        recording_location="shiftpod1",
        owner="bunnie",
        tags=["AC"],
        data_tz=UTC_TZ,
    ),
]


# ------------------------------------------------
# analysis methods

def get_sun_transitions(
    start_date="2019-08-22",
    end_date="2019-09-03"
):
    dates = pd.date_range(start_date, end_date, freq="D")

    a = Astral()
    sunrise = [
        a.sunrise_utc(
            date.to_pydatetime().date(),
            BLACK_ROCK_CITY_LATITUDE,
            BLACK_ROCK_CITY_LONGITUDE,
            BLACK_ROCK_CITY_ELEVATION,
        )
        for date in dates
    ]
    sunset = [
        a.sunset_utc(
            date.to_pydatetime().date(),
            BLACK_ROCK_CITY_LATITUDE,
            BLACK_ROCK_CITY_LONGITUDE,
            BLACK_ROCK_CITY_ELEVATION,
        )
        for date in dates
    ]
    sun_transitions_df = pd.DataFrame({"sunrise": sunrise, "sunset": sunset})
    # convert everything to PST because was given in UTC
    for col_name in sun_transitions_df.columns:
        sun_transitions_df[col_name] = sun_transitions_df[col_name]\
            .dt.tz_convert(PACIFIC_TZ)

    # because we want to look at night times, add the previous sunset into the row
    sun_transitions_df['prev_sunset'] = sun_transitions_df.sunset.shift(1)

    return sun_transitions_df


def get_night_rect_traces(
    daylight_df: pd.DataFrame,
    color="gray",
    name="night",
    y_range=TEMPERATURE_RANGE,
):
    traces = []
    for i, row in enumerate(daylight_df.itertuples(index=False)):
        traces.append(
            go.Scatter(
                x=[
                    row.prev_sunset,
                    row.prev_sunset,
                    row.sunrise,
                    row.sunrise,
                ],
                y=[y_range[0], y_range[1], y_range[1], y_range[0]],
                fill="toself",
                fillcolor=color,
                mode="lines",
                line=dict(width=0),
                opacity=0.3,
                showlegend=True if i == 0 else False,
                name=name,
            )
        )
    return traces


def load_data_files(data_sources: list = REGISTERED_DATA):
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
        name="{} - {}".format(source.recording_location, source.owner),
    )
    return trace


def plot_temperatures(data_sources, units="F"):
    if not hasattr(data_sources[0], "data"):
        load_data_files()

    temp_traces = [get_source_data_trace(source) for source in data_sources]
    night_traces = get_night_rect_traces(get_sun_transitions())

    # order matters, we want the night traces below the temp traces
    traces = night_traces + temp_traces

    fig = go.Figure(
        data=traces,
        layout=dict(
            width=1200,
            height=800,
            title="Dwelling temperature - BRC 2019",
            xaxis=dict(title="date"),
            yaxis=dict(title=f"temperature {units}", range=TEMPERATURE_RANGE),
        ),
    )
    out_filename = os.path.join(FIGURE_PATH, "phage_temperature_2019.html")
    plot(fig, filename=out_filename)


def plot_temperature_distributions():
    # TODO: create histograms of each dwelling. make outside gray, and plotted first
    pass


def plot_period_averages():
    pass
    # TODO: do the average sunset to sunrise for each trace
    # fix the sunrise-sunset times as the average over the week


def main():
    load_data_files(REGISTERED_DATA)
    plot_temperatures(REGISTERED_DATA)


if __name__ == "__main__":
    sys.exit(main())