"""
Temperature data for Burning Man 2019
py3.8, using dataclasses

Eventually show the resulting plotly html file in a github.io page
https://mpesavento.github.io/phage_temperature_2019/

"""
import os
import sys
import datetime
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

LINE_OPACITY = 0.8

LINE_COLORS = [
    "#1f77b4",  # muted blue
    "#ff7f0e",  # safety orange
    "#2ca02c",  # cooked asparagus green
    "#d62728",  # brick red
    "#9467bd",  # muted purple
    "#8c564b",  # chestnut brown
    "#e377c2",  # raspberry yogurt pink
    "#7f7f7f",  # middle gray
    "#bcbd22",  # curry yellow-green
    "#17becf",  # blue-teal
]

# ------------------------------------------------
# utility methods

def is_interactive():
    # type: () -> bool
    """Returns True if in an interactive session"""
    # noinspection PyUnresolvedReferences
    import __main__ as main_
    if "pydevconsole" in sys.argv[0]:
        return True
    if not hasattr(main_, "__file__"):
        return True
    return False


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
    color: str = LINE_COLORS[0]
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

    @property
    def name(self):
        return "{} - {}".format(self.recording_location, self.owner)


# ------------------------------------------------
# data registry
# metadata store for data origin and additional information
REGISTERED_DATA = [
    TemperatureSource(
        filename="burningman_2019_mjp_shiftpod2.csv",
        recording_location="shiftpod2",
        owner="mjp",
        tags=["shade", "swampcooler"],
        color=LINE_COLORS[0],
    ),
    TemperatureSource(
        filename="burningman_2019_pnelson_shiftpod2_blastshield_swampcooler.csv",
        recording_location="shiftpod2",
        owner="pnelson",
        tags=["shade", "swampcooler", "blastshield"],
        color=LINE_COLORS[1],
    ),
    TemperatureSource(
        filename="BurningMan2019 - Altitude Lounge 845&C.csv",
        recording_location="outdoors",
        owner="Altitude Lounge",
        datetime_col="Time",
        temp_col="Outdoor Temperature (F)",
        temp_units="F",
        tags=[],
        color="#333333",

    ),
    TemperatureSource(
        filename="burningman_2019_myq_h12yurt.csv",
        recording_location="h12yurt",
        owner="myq",
        tags=["AC?"],
        data_tz=UTC_TZ,
        color=LINE_COLORS[2],
    ),
    TemperatureSource(
        filename="burningman_2019_bunnie_shiftpod-clipped.csv",
        recording_location="shiftpod1",
        owner="bunnie",
        tags=["AC"],
        data_tz=UTC_TZ,
        color=LINE_COLORS[3],
    ),
]


# ------------------------------------------------
# analysis methods

def get_sun_transitions(
    start_date="2019-08-22",
    end_date="2019-09-03"
):
    """Get BRC sunrise and sunset times between date range, date inclusive"""
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
        line=dict(color=source.color),
        name=source.name,
        opacity=LINE_OPACITY,

    )
    return trace


def plot_week_temperatures(data_sources: list, sun_df: pd.DataFrame, units="F"):
    if not hasattr(data_sources[0], "data"):
        load_data_files()

    temperature_traces = [get_source_data_trace(source) for source in data_sources]
    # # change the line color of the traces here
    # for i, trace in enumerate(temperature_traces):
    #     clr = LINE_COLORS[i] if "outdoors" not in trace.name else "black"
    #     # width = 2 if "outdoors" not in trace.name else 3
    #     width = 2
    #     trace['line'] = dict(width=width, color=clr)

    night_traces = get_night_rect_traces(sun_df)

    # order matters, we want the night traces below the temp traces
    traces = night_traces + temperature_traces

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
    out_filename = os.path.join(FIGURE_PATH, "phage_temperature_{}_2019.html".format(units))
    plot(fig, filename=out_filename)
    return fig


def plot_temperature_distributions():
    # TODO: create histograms of each dwelling. make outdoors gray, and plot it first
    pass


def ts_to_epoch_seconds(t) -> float:
    """
    Convert pandas Timestamp to epoch time in seconds
    Can be a single timestamp or a Series of Timestamps
    """
    return t.astype(int) / 1e9


def mean_time(ser: pd.Series, shift_timezone=True) -> datetime.time:
    """
    Find the average time over a series of Timestamps
    EG, what is the average sunrise time
    """
    mean_epoch_time = ts_to_epoch_seconds(ser).mean()
    mean_datetime = pd.to_datetime(mean_epoch_time, unit="s")
    if shift_timezone:
        # we only need to do this if the time series we get in is not TZ aware already
        mean_datetime = mean_datetime.tz_localize(UTC_TZ).tz_convert(PACIFIC_TZ)
    return mean_datetime.time()


def plot_period_averages(data_sources: list, sun_df: pd.DataFrame):
    """Create a plot of the average temperatures over a 24 hour period"""
    daily_mean_df = extract_daily_means(data_sources)

    traces = []

    # There is a bug in here with using datetime.time as the x axis. Things
    # don't line up as expected, so we need to have the first trace(s) have
    # a full sampling of all timestamps from the data sources
    # to be able to plot the night shading rects. Dunno why.
    # To solve this, we just plot an invisible line with our target x axis
    # before the night rects
    traces.append(
        go.Scatter(
            x=daily_mean_df.index,
            y=[60] * len(daily_mean_df.index),
            mode="lines",
            line=dict(width=0),
            name="placeholder",
            showlegend=False,
        )
    )

    # shade the night time
    # these traces need to be after the temperature traces, because indexing is weird for datetime.time
    sunset = mean_time(sun_df.sunset)
    sunrise = mean_time(sun_df.sunrise)
    y_range = (60, 100)  # temperature range, in F
    traces.extend([
        # NOTE: the sunset/sunrise datetime.time needs to perfectly align with the times in the temperature traces
        go.Scatter(
            x=[
                datetime.time(0, 0),
                datetime.time(0, 0),
                datetime.time(6, 15),
                datetime.time(6, 15),
                # sunrise,
                # sunrise,
            ],
            y=[y_range[0], y_range[1], y_range[1], y_range[0]],
            fill="toself",
            fillcolor="grey",
            mode="lines",
            line=dict(width=0),
            opacity=0.3,
            showlegend=True,
            name="night",
        ),
        go.Scatter(
            x=[
                # sunset,
                # sunset,
                datetime.time(19, 42),
                datetime.time(19, 42),
                datetime.time(23, 57),
                datetime.time(23, 57),
            ],
            y=[y_range[0], y_range[1], y_range[1], y_range[0]],
            fill="toself",
            fillcolor="grey",
            mode="lines",
            line=dict(width=0),
            opacity=0.3,
            showlegend=False,
            name="night",
        ),
    ])

    # create traces for each of the source day averages
    for i, source in enumerate(data_sources):
        traces.append(
            go.Scatter(
                x=daily_mean_df.index,
                y=daily_mean_df[source.name],
                mode="lines",
                line=dict(width=2, color=source.color),
                name=source.name,
                opacity=LINE_OPACITY,
            )
        )

    fig = go.Figure(
        data=traces,
        layout=dict(
            width=1200,
            height=800,
            title="Dwelling 24H average temperature - BRC 2019",
            xaxis=dict(title="date"),
            yaxis=dict(title=f"temperature (F)", range=y_range),
        ),
    )
    out_filename = os.path.join(FIGURE_PATH, "phage_average_temperature_2019.html")
    plot(fig, filename=out_filename)
    return fig


def extract_daily_means(data_sources: list) -> pd.DataFrame:
    daily_mean = {}
    for source in data_sources:
        daily_mean[source.name] = daily_mean_for_source(source)
    daily_mean_df = pd.concat(daily_mean, axis=1)
    daily_mean_df.columns = daily_mean_df.columns.get_level_values(0)
    return daily_mean_df


def daily_mean_for_source(source) -> pd.Series:
    # given the datasource, pull it as a series
    tempf = source.data.set_index('datetime')['temperature F'].dropna()
    # resample to make the timestamps consistent between data sources; fill with mean
    tempf_df = tempf.resample("3T").bfill().to_frame().reset_index()

    # add columns for date and time
    tempf_df['date'] = tempf_df['datetime'].dt.date
    tempf_df['time'] = tempf_df['datetime'].dt.time
    daily_temp = tempf_df.groupby('time').mean()
    return daily_temp


def main():
    load_data_files(REGISTERED_DATA)
    sun_df = get_sun_transitions()

    # create plot of temperatures over all Burning Man recordings
    plot_week_temperatures(REGISTERED_DATA, sun_df)

    # create plot of average dwelling temperature over 24 hours
    plot_period_averages(REGISTERED_DATA, sun_df)


if __name__ == "__main__" and not is_interactive():
    sys.exit(main())
