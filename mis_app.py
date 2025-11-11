import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import os
from datetime import date

EXCEL_PATH = "Book1.xlsx"
INR_MULTIPLIER = 1000

# -------------------------
# Helper to append to Excel
# -------------------------
def append_df_to_excel(filename, df, sheet_name):
    if not os.path.exists(filename):
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        return

    book = load_workbook(filename)
    if sheet_name in book.sheetnames:
        start_row = book[sheet_name].max_row
        with pd.ExcelWriter(filename, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
            df.to_excel(writer, index=False, header=False, sheet_name=sheet_name, startrow=start_row)
    else:
        with pd.ExcelWriter(filename, engine="openpyxl", mode="a") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)

# -------------------------
# Summary calculator
# -------------------------
def calculate_summary(pur_df, sal_df):
    for df in [pur_df, sal_df]:
        for col in ["INR", "BHD", "Quantity", "Item Rate (BHD)"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    total_purchase = pur_df["INR"].sum() if "INR" in pur_df.columns else 0
    total_sales = sal_df["INR"].sum() if "INR" in sal_df.columns else 0
    return {"Total Purchase (INR)": total_purchase, "Total Sales (INR)": total_sales, "Gross Profit (INR)": total_sales - total_purchase}

# -------------------------
# App setup
# -------------------------
st.set_page_config(page_title="MIS System", layout="wide")
st.title("📊 MIS System - Smooth Editing Mode")

# initialize default data
if "purchase_df" not in st.session_state:
    st.session_state.purchase_df = pd.DataFrame([{
        "Date": date.today(),
        "Vendor": "",
        "Item Rate (BHD)": 0.0,
        "Quantity": 0.0
    }])

if "sales_df" not in st.session_state:
    st.session_state.sales_df = pd.DataFrame([{
        "Date": date.today(),
        "Customer": "",
        "Item Rate (BHD)": 0.0,
        "Quantity": 0.0
    }])

# -------------------------
# PURCHASE SECTION
# -------------------------
st.subheader("🧾 Purchase")

if st.button("➕ Add Purchase Row"):
    new_row = {"Date": date.today(), "Vendor": "", "Item Rate (BHD)": 0.0, "Quantity": 0.0}
    st.session_state.purchase_df = pd.concat([st.session_state.purchase_df, pd.DataFrame([new_row])], ignore_index=True)

purchase_temp = st.session_state.purchase_df.copy()
purchase_temp["Date"] = pd.to_datetime(purchase_temp["Date"]).dt.date

edited_purchase = st.data_editor(
    purchase_temp,
    num_rows="dynamic",
    use_container_width=True,
    key="purchase_editor",
    column_config={
        "Date": st.column_config.DateColumn("Date"),
        "Vendor": st.column_config.TextColumn("Vendor"),
        "Item Rate (BHD)": st.column_config.NumberColumn("Item Rate (BHD)", step=0.001),
        "Quantity": st.column_config.NumberColumn("Quantity", step=0.01),
    },
    hide_index=True,
)

# Apply button updates session state only once user finishes editing
if st.button("✔️ Apply Purchase Changes"):
    st.session_state.purchase_df = edited_purchase
    st.success("✅ Purchase table updated successfully!")

# -------------------------
# SALES SECTION
# -------------------------
st.subheader("💰 Sales")

if st.button("➕ Add Sales Row"):
    new_row = {"Date": date.today(), "Customer": "", "Item Rate (BHD)": 0.0, "Quantity": 0.0}
    st.session_state.sales_df = pd.concat([st.session_state.sales_df, pd.DataFrame([new_row])], ignore_index=True)

sales_temp = st.session_state.sales_df.copy()
sales_temp["Date"] = pd.to_datetime(sales_temp["Date"]).dt.date

edited_sales = st.data_editor(
    sales_temp,
    num_rows="dynamic",
    use_container_width=True,
    key="sales_editor",
    column_config={
        "Date": st.column_config.DateColumn("Date"),
        "Customer": st.column_config.TextColumn("Customer"),
        "Item Rate (BHD)": st.column_config.NumberColumn("Item Rate (BHD)", step=0.001),
        "Quantity": st.column_config.NumberColumn("Quantity", step=0.01),
    },
    hide_index=True,
)

if st.button("✔️ Apply Sales Changes"):
    st.session_state.sales_df = edited_sales
    st.success("✅ Sales table updated successfully!")

# -------------------------
# 💾 Save All
# -------------------------
st.markdown("---")
if st.button("💾 Save All to Excel"):
    pur = st.session_state.purchase_df.copy()
    sal = st.session_state.sales_df.copy()

    # calculate INR/BHD before saving
    pur["INR"] = pd.to_numeric(pur["Quantity"], errors="coerce").fillna(0) * INR_MULTIPLIER
    pur["BHD"] = pur["Quantity"] * pur["Item Rate (BHD)"]
    sal["INR"] = pd.to_numeric(sal["Quantity"], errors="coerce").fillna(0) * INR_MULTIPLIER
    sal["BHD"] = sal["Quantity"] * sal["Item Rate (BHD)"]

    pur = pur[~pur["Vendor"].astype(str).str.strip().eq("")]
    sal = sal[~sal["Customer"].astype(str).str.strip().eq("")]

    if not pur.empty:
        append_df_to_excel(EXCEL_PATH, pur, "Purchase")
    if not sal.empty:
        append_df_to_excel(EXCEL_PATH, sal, "Sales")

    st.success("✅ All data saved to Excel successfully!")

# -------------------------
# 📊 Summary
# -------------------------
if os.path.exists(EXCEL_PATH):
    xls = pd.ExcelFile(EXCEL_PATH)
    pur = pd.read_excel(xls, "Purchase") if "Purchase" in xls.sheet_names else pd.DataFrame()
    sal = pd.read_excel(xls, "Sales") if "Sales" in xls.sheet_names else pd.DataFrame()
    summary = calculate_summary(pur, sal)
    st.markdown("---")
    st.write("### Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Purchase (INR)", f"{summary['Total Purchase (INR)']:.2f}")
    c2.metric("Total Sales (INR)", f"{summary['Total Sales (INR)']:.2f}")
    c3.metric("Gross Profit (INR)", f"{summary['Gross Profit (INR)']:.2f}")
else:
    st.info("No Excel data yet.")
