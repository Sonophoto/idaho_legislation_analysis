import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from config import get_datarun


@st.cache_data
def load_data():
    try:
        run = get_datarun()
    except SystemExit:
        st.error(
            "Could not determine DATARUN. "
            "Run scrape.py first or set the DATARUN environment variable."
        )
        st.stop()
    path = Path("Data") / f"idaho_bills_enriched_{run}.jsonl"
    df = pd.read_json(path, orient="records", lines=True)
    return df
