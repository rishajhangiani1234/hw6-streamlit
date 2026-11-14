import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="UFO Sightings Report", layout="wide")

URL = ("https://github.com/UIUC-iSchool-DataViz/is445_data/raw/main/"
       "ufo-scrubbed-geocoded-time-standardized-00.csv")
COLS = ["datetime", "city", "state", "country", "shape", "duration_sec",
        "duration_text", "comments", "date_posted", "lat", "lon"]


@st.cache_data
def load_data():
    df = pd.read_csv(URL, header=None, names=COLS, low_memory=False)
    # a few timestamps use "24:00", which pandas can't parse
    df["datetime"] = df["datetime"].astype(str).str.replace(" 24:", " 00:", regex=False)
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"])
    df["year"] = df["datetime"].dt.year
    df["month"] = df["datetime"].dt.month
    df["hour"] = df["datetime"].dt.hour
    df["shape"] = df["shape"].fillna("unknown")
    df["country"] = df["country"].fillna("unknown")
    return df


df = load_data()

st.title("UFO Sightings: When and What People See")
st.caption("Dataset: scrubbed, geocoded UFO sightings (UIUC iSchool DataViz course data).")

# ---------------------------------------------------------------- sidebar
st.sidebar.header("Controls")
min_year, max_year = int(df["year"].min()), int(df["year"].max())
year_range = st.sidebar.slider("Year range", min_year, max_year, (1990, max_year))

top_shapes = df["shape"].value_counts().head(8).index.tolist()
shapes = st.sidebar.multiselect("Shapes (Visualization 1)", top_shapes,
                                default=top_shapes[:5])
countries = st.sidebar.multiselect("Country (Visualization 2)",
                                   sorted(df["country"].unique()),
                                   default=["us"])

filtered = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

# ---------------------------------------------------------------- viz 1
st.header("Visualization 1: Sightings per year by shape")

v1 = (filtered[filtered["shape"].isin(shapes)]
      .groupby(["year", "shape"]).size().reset_index(name="sightings"))

legend_select = alt.selection_point(fields=["shape"], bind="legend")

chart1 = (
    alt.Chart(v1)
    .mark_line(point=True)
    .encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("sightings:Q", title="Number of sightings"),
        color=alt.Color("shape:N", title="Shape (click legend)",
                        scale=alt.Scale(scheme="tableau10")),
        opacity=alt.condition(legend_select, alt.value(1.0), alt.value(0.1)),
        tooltip=["year", "shape", "sightings"],
    )
    .add_params(legend_select)
    .properties(height=400)
)
st.altair_chart(chart1, width="stretch")

# ---------------------------------------------------------------- viz 2
st.header("Visualization 2: When do sightings happen? (hour vs. month)")

v2 = (filtered[filtered["country"].isin(countries)]
      .groupby(["month", "hour"]).size().reset_index(name="sightings"))

month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
v2["month_name"] = v2["month"].apply(lambda m: month_names[m - 1])

chart2 = (
    alt.Chart(v2)
    .mark_rect()
    .encode(
        x=alt.X("month_name:O", sort=month_names, title="Month"),
        y=alt.Y("hour:O", title="Hour of day (24h)", sort="descending"),
        color=alt.Color("sightings:Q", title="Sightings",
                        scale=alt.Scale(scheme="inferno")),
        tooltip=["month_name", "hour", "sightings"],
    )
    .properties(height=450)
)
st.altair_chart(chart2, width="stretch")

# ---------------------------------------------------------------- write-up
st.header("Write-up")

st.subheader("1. How has UFO reporting changed over time, and by shape?")
st.write(
    "For this chart I wanted to see how reporting changed over the years and whether the "
    "kinds of things people described changed with it. I went with lines and points because "
    "years are ordered and I wanted the trends to be easy to follow, and the points give the "
    "tooltips something to hover on. Year is ordinal on the x-axis, the count is quantitative "
    "on the y-axis (starting at zero so the heights stay honest), and shape is nominal in the "
    "color encoding. Shapes have no natural order, so I used a categorical palette and kept "
    "it to the most common ones so the colors stay easy to tell apart. In Python, I parsed "
    "the timestamps (a few use 24:00, which needed fixing), dropped rows with unreadable "
    "dates, labeled missing shapes as unknown, and counted reports for each year and shape. "
    "The main story is steady growth through the late 1990s, a plateau in the 2000s, and a "
    "big jump around 2012 where fireball reports spike right alongside light and circle. "
    "Light is the top shape almost every year, and unknown leads in the mid 1990s. With more "
    "time, I would switch to each shape's share of the yearly total, since overall growth in "
    "reporting could be hiding changes in the mix, and I would add a log scale so the rarer "
    "shapes are easier to see."
)

st.subheader("2. When during the day and year do sightings happen?")
st.write(
    "Here I wanted to know when people tend to report sightings. A heatmap felt like the "
    "right fit since month and hour are both discrete, and it avoids the overplotting I "
    "would get from showing individual reports. Month is ordinal on the x-axis in calendar "
    "order, hour is ordinal on the y-axis, and the count is quantitative in the color "
    "encoding. I picked the inferno scheme because it is sequential and evenly spaced "
    "perceptually, so brighter always means more reports, and I flipped the y-axis so late "
    "evening hours sit together near the top of the chart. In Python, I pulled the month and "
    "hour out of the cleaned timestamps and counted reports in each cell. For US reports "
    "since 1990, the brightest cells land around 9 to 10 p.m. and in July, and about 62% of "
    "reports come between 6 p.m. and midnight. If I had more time, I would adjust for the "
    "number of days in each month, show countries side by side, and link this chart to the "
    "first one so brushing a year range or shape updates the heatmap."
)

st.subheader("Interactivity")
st.write(
    "In the first chart, clicking a shape in the legend highlights that line and fades the "
    "rest, which helps a lot when lines overlap. The sidebar year slider and shape "
    "multiselect control the line chart, and the year slider and country multiselect control "
    "the heatmap. Both charts also have hover tooltips with exact values."
)

st.subheader("Caveats")
st.write(
    "These are counts of reports from people, not verified events, so more reports does not "
    "necessarily mean more objects in the sky. Reporting also depends on things like "
    "internet access and publicity. The data end in 2014, and that year is incomplete, so "
    "the drop at the end is not a real decline. The default views only show the most common "
    "shapes and US reports."
)
