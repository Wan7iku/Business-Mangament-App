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

    for item in items:

     st.write(f"**{item['item']}**")

     new_quantity = st.number_input(
        "Quantity",
        min_value=1,
        value=item["quantity_purchased"],
        step=1,
        key=f"qty_{purchase['receipt_id']}_{item['item']}"
     )

     new_unit_cost = st.number_input(
       "Unit buying price",
        min_value=0.0,
        value=float(item["unit_cost"]),
        step=0.01,
        key=f"cost_{purchase['receipt_id']}_{item['purchase_item_id']}"
     )

     new_total = new_quantity * new_unit_cost

     st.write(
        f"New total: KSh {new_total:,.2f}"
     )
    receipt_total = sum(
        item["total_cost"]
        for item in st.session_state.purchase_items
    )

    st.subheader(
        f"Receipt Total: KSh {receipt_total:,.2f}"
    )  
if st.session_state.purchase_items:

    receipt_total = sum(
        item["total_cost"]
        for item in st.session_state.purchase_items
    )

    st.subheader(
        f"Receipt Total: KSh {receipt_total:,.2f}"
    )

    if st.button("Save Receipt"):

        try:
            # Start database transaction
            conn.execute("BEGIN")

            # 1. Create the purchase receipt
            cursor = conn.execute(
                """
                INSERT INTO purchase_receipts
                (supplier_id, purchase_date, total_amount)
                VALUES (?, ?, ?)
                """,
                (
                    supplier_options[selected_supplier],
                    purchase_date,
                    receipt_total
                )
            )

            # Get the newly created receipt ID
            receipt_id = cursor.lastrowid

            # 2. Save each purchased item
            for item in st.session_state.purchase_items:

                conn.execute(
                    """
                    INSERT INTO purchase_items
                    (
                        receipt_id,
                        inventory_id,
                        quantity_purchased,
                        unit_cost,
                        total_cost
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        receipt_id,
                        item["inventory_id"],
                        item["quantity"],
                        item["unit_cost"],
                        item["total_cost"]
                    )
                )

                # 3. Increase inventory quantity
                conn.execute(
                    """
                    UPDATE inventory
                    SET quantity = COALESCE(quantity, 0) + ?
                    WHERE id = ?
                    """,
                    (
                        item["quantity"],
                        item["inventory_id"]
                    )
                )

            # Save everything
            conn.commit()

            st.success(
                f"Receipt #{receipt_id} saved successfully!"
            )

            # Clear the temporary purchase
            st.session_state.purchase_items = []

        except Exception as e:
            # Undo everything if something goes wrong
            conn.rollback()

            st.error(
                f"Could not save receipt: {e}"
            )


st.header("Purchase History")

purchases = conn.execute(
    """
    SELECT
        pr.receipt_id,
        s.name AS supplier,
        pr.purchase_date,
        pr.total_amount
    FROM purchase_receipts pr
    JOIN suppliers s
        ON pr.supplier_id = s.supplier_id
    ORDER BY pr.purchase_date DESC, pr.receipt_id DESC
    """
).fetchall()

if purchases:

    for purchase in purchases:

        receipt_id = purchase["receipt_id"]

        with st.expander(
            f"Receipt #{receipt_id} | "
            f"{purchase['supplier']} | "
            f"{purchase['purchase_date']} | "
            f"KSh {purchase['total_amount']:,.2f}"
        ):

            items = conn.execute(
                """
                SELECT
                    pi.purchase_item_id,
                    i.id AS inventory_id,
                    i.item,
                    pi.quantity_purchased,
                    pi.unit_cost,
                    pi.total_cost
                FROM purchase_items pi
                JOIN inventory i
                    ON pi.inventory_id = i.id
                WHERE pi.receipt_id = ?
                """,
                (receipt_id,)
            ).fetchall()

            # Edit or remove existing receipt items
            if items:

                for item in items:

                    item_id = item["purchase_item_id"]

                    st.divider()
                    st.write(f"**{item['item']}**")

                    new_quantity = st.number_input(
                        "Quantity",
                        min_value=1,
                        value=int(item["quantity_purchased"]),
                        step=1,
                        key=f"qty_{receipt_id}_{item_id}"
                    )

                    new_unit_cost = st.number_input(
                        "Unit buying price (KSh)",
                        min_value=0.0,
                        value=float(item["unit_cost"]),
                        step=0.01,
                        key=f"cost_{receipt_id}_{item_id}"
                    )

                    new_total = new_quantity * new_unit_cost

                    st.write(
                        f"Updated line total: KSh {new_total:,.2f}"
                    )

                    if st.button(
                        "Save Changes",
                        key=f"save_{receipt_id}_{item_id}"
                    ):

                        old_quantity = item["quantity_purchased"]
                        quantity_difference = (
                            new_quantity - old_quantity
                        )

                        try:
                            conn.execute("BEGIN")

                            # Update the receipt line
                            conn.execute(
                                """
                                UPDATE purchase_items
                                SET quantity_purchased = ?,
                                    unit_cost = ?,
                                    total_cost = ?
                                WHERE purchase_item_id = ?
                                """,
                                (
                                    new_quantity,
                                    new_unit_cost,
                                    new_total,
                                    item_id
                                )
                            )

                            # Adjust stock by the quantity difference
                            conn.execute(
                                """
                                UPDATE inventory
                                SET quantity =
                                    COALESCE(quantity, 0) + ?
                                WHERE id = ?
                                """,
                                (
                                    quantity_difference,
                                    item["inventory_id"]
                                )
                            )

                            # Recalculate the receipt total
                            new_receipt_total = conn.execute(
                                """
                                SELECT SUM(total_cost)
                                FROM purchase_items
                                WHERE receipt_id = ?
                                """,
                                (receipt_id,)
                            ).fetchone()[0]

                            conn.execute(
                                """
                                UPDATE purchase_receipts
                                SET total_amount = ?
                                WHERE receipt_id = ?
                                """,
                                (
                                    new_receipt_total or 0,
                                    receipt_id
                                )
                            )

                            conn.commit()

                            st.success("Receipt item updated!")
                            st.rerun()

                        except Exception as e:
                            conn.rollback()
                            st.error(
                                f"Could not update item: {e}"
                            )

                    # Remove item with confirmation
                    confirm_key = f"confirm_remove_{receipt_id}_{item_id}"

                    if st.button(
                        "Remove Item",
                        key=f"remove_{receipt_id}_{item_id}"
                    ):
                        st.session_state[confirm_key] = True

                    if st.session_state.get(confirm_key, False):

                        st.warning(
                            f"Remove {item['quantity_purchased']} × "
                            f"{item['item']} from this receipt?"
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button(
                                "Yes, remove",
                                key=f"yes_remove_{receipt_id}_{item_id}"
                            ):

                                try:
                                    current_stock = conn.execute(
                                        """
                                        SELECT quantity
                                        FROM inventory
                                        WHERE id = ?
                                        """,
                                        (item["inventory_id"],)
                                    ).fetchone()

                                    if current_stock is None:
                                        st.error(
                                            "Inventory item not found."
                                        )
                                        st.stop()

                                    current_quantity = (
                                        current_stock["quantity"] or 0
                                    )

                                    if (
                                        current_quantity
                                        < item["quantity_purchased"]
                                    ):
                                        st.error(
                                            "Cannot remove this line "
                                            "because current stock is "
                                            "lower than the quantity "
                                            "recorded on this receipt."
                                        )
                                        st.stop()

                                    conn.execute("BEGIN")

                                    # Reverse the stock added by this line
                                    conn.execute(
                                        """
                                        UPDATE inventory
                                        SET quantity = quantity - ?
                                        WHERE id = ?
                                        """,
                                        (
                                            item["quantity_purchased"],
                                            item["inventory_id"]
                                        )
                                    )

                                    # Delete the receipt line
                                    conn.execute(
                                        """
                                        DELETE FROM purchase_items
                                        WHERE purchase_item_id = ?
                                        """,
                                        (item_id,)
                                    )

                                    # Recalculate receipt total
                                    new_receipt_total = conn.execute(
                                        """
                                        SELECT SUM(total_cost)
                                        FROM purchase_items
                                        WHERE receipt_id = ?
                                        """,
                                        (receipt_id,)
                                    ).fetchone()[0]

                                    conn.execute(
                                        """
                                        UPDATE purchase_receipts
                                        SET total_amount = ?
                                        WHERE receipt_id = ?
                                        """,
                                        (
                                            new_receipt_total or 0,
                                            receipt_id
                                        )
                                    )

                                    conn.commit()

                                    st.session_state[confirm_key] = False
                                    st.success("Receipt item removed!")
                                    st.rerun()

                                except Exception as e:
                                    conn.rollback()
                                    st.error(
                                        f"Could not remove item: {e}"
                                    )

                        with col2:
                            if st.button(
                                "Cancel",
                                key=f"cancel_remove_{receipt_id}_{item_id}"
                            ):
                                st.session_state[confirm_key] = False
                                st.rerun()

            else:
                st.info(
                    "This receipt currently has no items."
                )

            # Add another item to this receipt
            st.divider()
            st.subheader("Add Item to Receipt")

            search_term = st.text_input(
                "Search inventory",
                placeholder="Type a product name...",
                key=f"add_search_{receipt_id}"
            )

            if search_term:

                matching_items = conn.execute(
                    """
                    SELECT id, item
                    FROM inventory
                    WHERE item LIKE ?
                    ORDER BY item
                    """,
                    (f"%{search_term}%",)
                ).fetchall()

                if matching_items:

                    item_options = {
                        row["item"]: row["id"]
                        for row in matching_items
                    }

                    selected_item_name = st.selectbox(
                        "Select product",
                        options=list(item_options.keys()),
                        key=f"add_item_{receipt_id}"
                    )

                    selected_inventory_id = item_options[
                        selected_item_name
                    ]

                    add_quantity = st.number_input(
                        "Quantity to add",
                        min_value=1,
                        step=1,
                        key=f"add_qty_{receipt_id}"
                    )

                    add_unit_cost = st.number_input(
                        "Unit buying price (KSh)",
                        min_value=0.0,
                        step=0.01,
                        key=f"add_cost_{receipt_id}"
                    )

                    add_total = add_quantity * add_unit_cost

                    st.write(
                        f"Item total: KSh {add_total:,.2f}"
                    )

                    if st.button(
                        "Add Item to Receipt",
                        key=f"add_button_{receipt_id}"
                    ):

                        try:
                            conn.execute("BEGIN")

                            conn.execute(
                                """
                                INSERT INTO purchase_items
                                (
                                    receipt_id,
                                    inventory_id,
                                    quantity_purchased,
                                    unit_cost,
                                    total_cost
                                )
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    receipt_id,
                                    selected_inventory_id,
                                    add_quantity,
                                    add_unit_cost,
                                    add_total
                                )
                            )

                            conn.execute(
                                """
                                UPDATE inventory
                                SET quantity =
                                    COALESCE(quantity, 0) + ?
                                WHERE id = ?
                                """,
                                (
                                    add_quantity,
                                    selected_inventory_id
                                )
                            )

                            new_receipt_total = conn.execute(
                                """
                                SELECT SUM(total_cost)
                                FROM purchase_items
                                WHERE receipt_id = ?
                                """,
                                (receipt_id,)
                            ).fetchone()[0]

                            conn.execute(
                                """
                                UPDATE purchase_receipts
                                SET total_amount = ?
                                WHERE receipt_id = ?
                                """,
                                (
                                    new_receipt_total or 0,
                                    receipt_id
                                )
                            )

                            conn.commit()

                            st.success(
                                f"{selected_item_name} added to "
                                f"Receipt #{receipt_id}."
                            )
                            st.rerun()

                        except Exception as e:
                            conn.rollback()
                            st.error(
                                f"Could not add item: {e}"
                            )

                else:
                    st.warning("No matching inventory items found.")

else:
    st.info("No purchases have been recorded yet.")



st.header("Inventory")

inventory_items = conn.execute(
    """
    SELECT
        id,
        item,
        category,
        buying_price,
        selling_price,
        quantity
    FROM inventory
    ORDER BY item
    """
).fetchall()
search_inventory = st.text_input(
    "Search inventory",
    placeholder="Type a product name..."
)

if search_inventory:

    inventory_items = conn.execute(
        """
        SELECT
            id,
            item,
            category,
            buying_price,
            selling_price,
            quantity
        FROM inventory
        WHERE item LIKE ?
        ORDER BY item
        """,
        (f"%{search_inventory}%",)
    ).fetchall()

if inventory_items:

    for item in inventory_items:

        st.write(
            f"**{item['item']}** | "
            f"Category: {item['category'] or 'N/A'} | "
            f"Stock: {item['quantity'] or 0} | "
            f"Buying: KSh {item['buying_price']:,.2f} | "
            f"Selling: KSh {item['selling_price']:,.2f}"
        )

else:
    st.info("No inventory items found.")

st.subheader("Edit Product")

# Load products from the inventory table
products = conn.execute(
    """
    SELECT id, item, category, buying_price, selling_price
    FROM inventory
    ORDER BY item
    """
).fetchall()

if products:

    # Show product names to the user, but retain their IDs internally
    product_options = {
        product["item"]: product["id"]
        for product in products
    }

    selected_product_name = st.selectbox(
        "Select product to edit",
        options=list(product_options.keys()),
        key="edit_product_select"
    )

    selected_product_id = product_options[selected_product_name]

    # Fetch the selected product's current details
    selected_product = conn.execute(
        """
        SELECT id, item, category, buying_price, selling_price
        FROM inventory
        WHERE id = ?
        """,
        (selected_product_id,)
    ).fetchone()

    with st.form("edit_product_form"):

        edited_name = st.text_input(
            "Product name",
            value=selected_product["item"]
        )

        edited_category = st.text_input(
            "Category",
            value=selected_product["category"] or ""
        )

        edited_buying_price = st.number_input(
            "Buying price (KSh)",
            min_value=0.0,
            value=float(selected_product["buying_price"]),
            step=0.01
        )

        edited_selling_price = st.number_input(
            "Selling price (KSh)",
            min_value=0.0,
            value=float(selected_product["selling_price"]),
            step=0.01
        )

        save_product = st.form_submit_button("Save Product Changes")

        if save_product:

            if not edited_name.strip():
                st.error("Product name cannot be empty.")

            else:
                try:
                    conn.execute(
                        """
                        UPDATE inventory
                        SET item = ?,
                            category = ?,
                            buying_price = ?,
                            selling_price = ?
                        WHERE id = ?
                        """,
                        (
                            edited_name.strip(),
                            edited_category.strip(),
                            edited_buying_price,
                            edited_selling_price,
                            selected_product_id
                        )
                    )

                    conn.commit()

                    st.success(
                        f"{edited_name.strip()} updated successfully!"
                    )

                    st.rerun()

                except Exception as e:
                    conn.rollback()

                    if "UNIQUE constraint failed" in str(e):
                        st.error(
                            "Another product already uses that name. "
                            "Please enter a unique product name."
                        )
                    else:
                        st.error(f"Could not update product: {e}")

else:
    st.info("There are no products available to edit.")

st.subheader("Add New Product")

with st.form("add_product_form"):

    new_item = st.text_input("Product name")

    new_category = st.text_input("Category")

    new_buying_price = st.number_input(
        "Buying price (KSh)",
        min_value=0.0,
        step=0.01
    )

    new_selling_price = st.number_input(
        "Selling price (KSh)",
        min_value=0.0,
        step=0.01
    )

    new_quantity = st.number_input(
        "Opening stock quantity",
        min_value=0,
        step=1
    )

    submitted = st.form_submit_button("Add Product")

    if submitted:

        if not new_item.strip():
            st.error("Please enter a product name.")

        else:
            try:
                conn.execute(
                    """
                    INSERT INTO inventory
                    (item, category, buying_price, selling_price, quantity)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        new_item.strip(),
                        new_category.strip(),
                        new_buying_price,
                        new_selling_price,
                        new_quantity
                    )
                )

                conn.commit()

                st.success(
                    f"{new_item.strip()} added to inventory!"
                )

                st.rerun()

            except Exception as e:
                conn.rollback()

                if "UNIQUE constraint failed" in str(e):
                    st.error(
                        "This product name already exists. "
                        "Use a unique name, including package size if needed."
                    )
                else:
                    st.error(f"Could not add product: {e}")
st.header("New Sale")

# Store sale items temporarily while building the sale
if "sale_items" not in st.session_state:
    st.session_state.sale_items = []

sale_date = st.date_input(
    "Sale date",
    key="sale_date"
)

st.subheader("Add Sale Item")

search_term = st.text_input(
    "Search inventory item",
    placeholder="Type an item name...",
    key="sale_search"
)

if search_term:

    items = conn.execute(
        """
        SELECT
            id,
            item,
            category,
            selling_price,
            quantity
        FROM inventory
        WHERE item LIKE ?
        ORDER BY item
        """,
        (f"%{search_term}%",)
    ).fetchall()

    if items:

        item_options = {
            item["item"]: item["id"]
            for item in items
        }

        selected_item_name = st.selectbox(
            "Select item",
            options=list(item_options.keys()),
            key="sale_item"
        )

        selected_inventory_id = item_options[selected_item_name]

        # Get the selected product's details
        selected_item = next(
            item for item in items
            if item["id"] == selected_inventory_id
        )

        current_stock = selected_item["quantity"] or 0
        default_price = selected_item["selling_price"]

        st.write(
            f"Current stock: **{current_stock}**"
        )

        quantity_sold = st.number_input(
            "Quantity sold",
            min_value=1,
            step=1,
            key="sale_quantity"
        )

        unit_price = st.number_input(
            "Actual selling price (KSh)",
            min_value=0.0,
            value=float(default_price),
            step=0.01,
            key="sale_unit_price"
        )

        item_total = quantity_sold * unit_price

        st.write(
            f"Item total: **KSh {item_total:,.2f}**"
        )

        if quantity_sold > current_stock:
            st.error(
                f"Not enough stock. Available stock: "
                f"{current_stock}"
            )

        elif st.button(
            "Add Item to Sale",
            key="add_sale_item"
        ):

            st.session_state.sale_items.append({
                "inventory_id": selected_inventory_id,
                "item": selected_item_name,
                "quantity": quantity_sold,
                "unit_price": unit_price,
                "total_price": item_total
            })

            st.success(
                f"{selected_item_name} added to sale."
            )

    else:
        st.warning(
            "No matching inventory items found."
        )
# --------------------------------------------------
# CURRENT SALE
# --------------------------------------------------

if st.session_state.sale_items:

    st.divider()

    st.subheader("Current Sale")

    for index, item in enumerate(
        st.session_state.sale_items
    ):

        st.write(
            f"**{item['item']}** | "
            f"Qty: {item['quantity']} | "
            f"Unit price: KSh {item['unit_price']:,.2f} | "
            f"Total: KSh {item['total_price']:,.2f}"
        )

        if st.button(
            "Remove",
            key=f"remove_sale_item_{index}"
        ):

            st.session_state.sale_items.pop(index)

            st.rerun()

    # Calculate total sale value
    sale_total = sum(
        item["total_price"]
        for item in st.session_state.sale_items
    )

    st.subheader(
        f"Sale Total: KSh {sale_total:,.2f}"
    )
# --------------------------------------------------
# SAVE SALE
# --------------------------------------------------

if st.session_state.sale_items:

    sale_total = sum(
        item["total_price"]
        for item in st.session_state.sale_items
    )

    if st.button(
        "Save Sale",
        key="save_sale"
    ):

        try:
            conn.execute("BEGIN")

            # Check stock again before saving
            for item in st.session_state.sale_items:

                current_stock = conn.execute(
                    """
                    SELECT quantity
                    FROM inventory
                    WHERE id = ?
                    """,
                    (item["inventory_id"],)
                ).fetchone()

                if current_stock is None:
                    raise Exception(
                        f"Inventory item '{item['item']}' "
                        f"no longer exists."
                    )

                available_stock = (
                    current_stock["quantity"] or 0
                )

                if item["quantity"] > available_stock:
                    raise Exception(
                        f"Not enough stock for "
                        f"{item['item']}. "
                        f"Available: {available_stock}, "
                        f"requested: {item['quantity']}."
                    )

            # Create the sale record
            cursor = conn.execute(
                """
                INSERT INTO sales
                (sale_date, total_amount)
                VALUES (?, ?)
                """,
                (
                    sale_date,
                    sale_total
                )
            )

            sale_id = cursor.lastrowid

            # Save each sale item and deduct stock
            for item in st.session_state.sale_items:

                conn.execute(
                    """
                    INSERT INTO sale_items
                    (
                        sale_id,
                        inventory_id,
                        quantity_sold,
                        unit_price,
                        total_price
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        sale_id,
                        item["inventory_id"],
                        item["quantity"],
                        item["unit_price"],
                        item["total_price"]
                    )
                )

                conn.execute(
                    """
                    UPDATE inventory
                    SET quantity =
                        COALESCE(quantity, 0) - ?
                    WHERE id = ?
                    """,
                    (
                        item["quantity"],
                        item["inventory_id"]
                    )
                )

            conn.commit()

            st.success(
                f"Sale #{sale_id} saved successfully!"
            )

            # Clear the temporary sale
            st.session_state.sale_items = []

            st.rerun()

        except Exception as e:

            conn.rollback()

            st.error(
                f"Could not save sale: {e}"
            )
conn.close()
