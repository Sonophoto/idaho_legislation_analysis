import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from config import get_datarun


@st.cache_data
def load_data():
    run = get_datarun()
    path = Path("Data") / f"idaho_bills_enriched_{run}.jsonl"
    df = pd.read_json(path, orient="records", lines=True)
    return df
