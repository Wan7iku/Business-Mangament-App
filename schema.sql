CREATE TABLE purchase_receipts (
    receipt_id INTEGER PRIMARY KEY AUTOINCREMENT, supplier TEXT NOT NULL, purchase_date DATE NOT NULL, total_amount REAL NOT NULL
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(id)
    );

CREATE TABLE purchase_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    item TEXT NOT NULL,
    quantity_purchased INTEGER NOT NULL,
    unit_cost REAL NOT NULL,
    total_cost REAL NOT NULL,

    FOREIGN KEY (receipt_id)
        REFERENCES purchase_receipts(receipt_id)
);
