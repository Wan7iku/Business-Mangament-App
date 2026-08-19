import pandas as pd
import sqlite3

# Read CSV file
df = pd.read_csv("binventory.csv")

# Ensure numeric types and handle missing values
df["quantity"] = pd.to_numeric(df["quantity"], 
                            errors="coerce").fillna(0).astype(int)
df["id"] = pd.to_numeric(df["id"], errors="coerce")
# Drop rows without a valid id
df = df.dropna(subset=["id"]).copy()
df["id"] = df["id"].astype(int)

# Connect to database
conn = sqlite3.connect("business.db")
cursor = conn.cursor()

# Update quantity for each item
for _, row in df.iterrows():
    cursor.execute(
        """
        UPDATE inventory
        SET quantity = ?
        WHERE id = ?
        """,
        (int(row["quantity"]), int(row["id"]))
    )

# Save changes
conn.commit()

# Close connection
conn.close()

print("Inventory quantities updated successfully!")


