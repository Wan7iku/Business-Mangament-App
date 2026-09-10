import streamlit as st
from database import get_connection

st.title("Business Management App")

conn = get_connection()

# Get suppliers from database
suppliers = conn.execute(
    """
    SELECT supplier_id, name
    FROM suppliers
    ORDER BY name
    """
).fetchall()

st.subheader("New Purchase")

supplier_options = {
    supplier["name"]: supplier["supplier_id"]
    for supplier in suppliers
}

selected_supplier = st.selectbox(
    "Supplier",
    options=list(supplier_options.keys())
)

if selected_supplier:
    supplier_id = supplier_options[selected_supplier]
    st.write("Selected supplier ID:", supplier_id)

conn.close()