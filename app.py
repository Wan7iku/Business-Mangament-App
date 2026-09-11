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
purchase_date = st.date_input(
    "Purchase date"
)
if selected_supplier:
    supplier_id = supplier_options[selected_supplier]
    st.write("Selected supplier ID:", supplier_id)
st.subheader("Add Purchase Item")

search_term = st.text_input(
    "Search inventory item",
    placeholder="Type an item name..."
)

if search_term:
    conn = get_connection()

    items = conn.execute(
        """
        SELECT id, item, category
        FROM inventory
        WHERE item LIKE ?
        ORDER BY item
        """,
        (f"%{search_term}%",)
    ).fetchall()

    conn.close()

    if items:
        item_options = {
            item["item"]: item["id"]
            for item in items
        }

        selected_item = st.selectbox(
            "Select item",
            options=list(item_options.keys())
        )

        inventory_id = item_options[selected_item]

        st.write("Selected:", selected_item)
    else:
        st.warning("No matching inventory items found.")
conn.close()
