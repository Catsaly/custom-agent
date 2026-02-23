"""
Streamlit Community Cloud entry point.
API URL'si env/secrets'tan okunur.
"""
import os
import streamlit as st

# Streamlit Cloud secrets'ı env'e yükle
if hasattr(st, "secrets"):
    for key, val in st.secrets.items():
        if isinstance(val, str):
            os.environ.setdefault(key, val)

# Ana uygulamayı başlat
from app.streamlit_app import *  # noqa: F401, F403
