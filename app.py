import streamlit as st
from database import get_connection

st.title("Business Management App")

conn = get_connection()

if "purchase_items" not in st.session_state:
    st.session_state.purchase_items = []

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
quantity_purchased = st.number_input(
    "Quantity purchased",
    min_value=1,
    step=1
)

unit_cost = st.number_input(
    "Unit buying price",
    min_value=0.0,
    step=0.01
)

total_cost = quantity_purchased * unit_cost

st.write(f"Total cost: KSh {total_cost:,.2f}")
if st.button("Add Item"):
    st.session_state.purchase_items.append({
        "inventory_id": inventory_id,
        "item": selected_item,
        "quantity": quantity_purchased,
        "unit_cost": unit_cost,
        "total_cost": total_cost
    })    
if st.session_state.purchase_items:
    st.subheader("Items on this receipt")

    for item in st.session_state.purchase_items:
        st.write(
            f"{item['item']} | "
            f"Qty: {item['quantity']} | "
            f"Unit cost: KSh {item['unit_cost']:,.2f} | "
            f"Total: KSh {item['total_cost']:,.2f}"
        )

    receipt_total = sum(
        item["total_cost"]
        for item in st.session_state.purchase_items
    )

    st.subheader(
        f"Receipt Total: KSh {receipt_total:,.2f}"
    )  
conn.close()
