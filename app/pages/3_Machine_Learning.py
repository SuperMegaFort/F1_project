# pages/3_Machine_Learning.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
# Import shared functions and constants from utils.py
from utils import (
    load_data,
    SESSION_FILES,
    YEAR_COLUMN,
    GP_NAME_COLUMN,
    VIS_DRIVER_COL,
    VIS_POSITION_COL,
    POINTS_COL,
    CONSTRUCTOR_COL
)

st.set_page_config(
    layout="wide",
    page_title="Machine Learning",
    page_icon="🏎️"
)