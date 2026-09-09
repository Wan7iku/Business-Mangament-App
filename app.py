import streamlit as st
from database import get_connection

st.title("Business Management App")

conn = get_connection()

st.success("Database connected successfully!")

conn.close()
