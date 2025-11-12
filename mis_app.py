import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ===================================
# ⚙️ Page Config - MUST BE FIRST!
# ===================================
st.set_page_config(page_title="MIS System", layout="wide", page_icon="📊")

# ===================================
# ⚙️ Configuration
# ===================================
APP_USERNAME = "admin"
APP_PASSWORD = "admin123"

# ===================================
# 🔒 Authentication
# ===================================
def password_gate():
    """Simple and safe login system."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None

    # Already logged in
    if st.session_state.authenticated:
        with st.sidebar:
            st.success(f"👋 Logged in as **{st.session_state.username}**")
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.rerun()
        return True

    # --- Login UI ---
    st.title("🔐 Secure MIS System Login")
    st.markdown("Please enter your credentials to access the MIS system.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("👤 Username", placeholder="Enter username")
        password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
        
        if st.button("🔓 Login", use_container_width=True):
            if username == APP_USERNAME and password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")

    st.stop()


# Run authentication
if not password_gate():
    st.stop()

# ===================================
# 💹 Helper Functions
# ===================================
def calculate_summary(purchase_df, sales_df):
    """Calculate financial summary."""
    for df in [purchase_df, sales_df]:
        for col in ["INR", "BHD", "Quantity", "Item Rate (BHD)"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    total_purchase = purchase_df["BHD"].sum() if len(purchase_df) > 0 and "BHD" in purchase_df.columns else 0
    total_sales = sales_df["BHD"].sum() if len(sales_df) > 0 and "BHD" in sales_df.columns else 0
    gross_profit = total_sales - total_purchase
    
    return {
        "Total Purchase (BHD)": total_purchase,
        "Total Sales (BHD)": total_sales,
        "Gross Profit (BHD)": gross_profit,
    }

def load_data_from_excel(uploaded_file):
    """Load data from uploaded Excel file."""
    try:
        xls = pd.ExcelFile(uploaded_file)
        purchase_df = pd.read_excel(xls, "Purchase") if "Purchase" in xls.sheet_names else pd.DataFrame()
        sales_df = pd.read_excel(xls, "Sales") if "Sales" in xls.sheet_names else pd.DataFrame()
        
        # Convert Date columns to datetime
        for df in [purchase_df, sales_df]:
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"]).dt.date
        
        return purchase_df, sales_df
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        return pd.DataFrame(), pd.DataFrame()

def create_excel_download(purchase_df, sales_df):
    """Create Excel file for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        purchase_df.to_excel(writer, sheet_name='Purchase', index=False)
        sales_df.to_excel(writer, sheet_name='Sales', index=False)
    output.seek(0)
    return output

# ===================================
# 🧱 Initialize Session State
# ===================================
if "purchase_data" not in st.session_state:
    st.session_state.purchase_data = pd.DataFrame(columns=["Date", "Vendor", "Item Rate (BHD)", "Quantity", "INR", "BHD"])
if "sales_data" not in st.session_state:
    st.session_state.sales_data = pd.DataFrame(columns=["Date", "Customer", "Item Rate (BHD)", "Quantity", "INR", "BHD"])
if "purchase_entries" not in st.session_state:
    st.session_state.purchase_entries = []
if "sales_entries" not in st.session_state:
    st.session_state.sales_entries = []

# ===================================
# 📤 Upload Existing Data Section
# ===================================
st.title("📊 MIS System - Purchase & Sales Entry")

with st.expander("📤 Upload Existing Excel File (Optional)", expanded=False):
    st.info("💡 If you have existing data, upload your Excel file here to continue from where you left off.")
    uploaded_file = st.file_uploader("Choose your MIS Excel file", type=['xlsx'], key="file_uploader")
    
    if uploaded_file is not None:
        if st.button("📥 Load Data from Excel"):
            purchase_df, sales_df = load_data_from_excel(uploaded_file)
            st.session_state.purchase_data = purchase_df
            st.session_state.sales_data = sales_df
            st.success(f"✅ Data loaded successfully! Found {len(purchase_df)} purchase records and {len(sales_df)} sales records.")
            st.rerun()

# ===================================
# 📊 Current Data Overview
# ===================================
st.markdown("---")
col_info1, col_info2 = st.columns(2)
with col_info1:
    st.metric("📦 Total Purchase Records", len(st.session_state.purchase_data) + len(st.session_state.purchase_entries))
with col_info2:
    st.metric("💰 Total Sales Records", len(st.session_state.sales_data) + len(st.session_state.sales_entries))

# ==============================
# 🛒 PURCHASE SECTION
# ==============================
st.markdown("---")
st.subheader("🧾 Purchase Entry")

with st.form("purchase_form"):
    c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.5, 1, 1, 1, 1])
    with c1:
        p_date = st.date_input("Date", key="p_date")
    with c2:
        p_vendor = st.text_input("Vendor Name", key="p_vendor", placeholder="Enter vendor name")
    with c3:
        p_item_rate = st.number_input("Item Rate (BHD)", min_value=0.0, format="%.3f", key="p_rate")
    with c4:
        p_quantity = st.number_input("Quantity", min_value=0.0, format="%.2f", key="p_qty")
    with c5:
        p_inr = p_quantity * 1000
        st.number_input("INR Value (auto)", value=p_inr, disabled=True, format="%.2f")
    with c6:
        p_bhd = p_item_rate * p_quantity
        st.number_input("BHD (auto)", value=p_bhd, disabled=True, format="%.3f")

    submitted_purchase = st.form_submit_button("➕ Add Purchase Entry", use_container_width=True)

if submitted_purchase:
    if p_vendor and p_item_rate > 0 and p_quantity > 0:
        st.session_state.purchase_entries.append({
            "Date": p_date,
            "Vendor": p_vendor,
            "Item Rate (BHD)": p_item_rate,
            "Quantity": p_quantity,
            "INR": p_inr,
            "BHD": p_bhd
        })
        st.success("✅ Purchase entry added successfully!")
        st.rerun()
    else:
        st.warning("⚠️ Please fill all purchase fields correctly.")

# Show pending entries
if st.session_state.purchase_entries:
    st.info(f"📝 **Pending Entries:** {len(st.session_state.purchase_entries)} (Click 'Save All Data' to finalize)")
    df_pur = pd.DataFrame(st.session_state.purchase_entries)
    st.dataframe(df_pur, use_container_width=True)
    st.write(f"**Pending Total - INR:** ₹{df_pur['INR'].sum():,.2f} | **BHD:** {df_pur['BHD'].sum():,.3f}")

# ==============================
# 💰 SALES SECTION
# ==============================
st.markdown("---")
st.subheader("💰 Sales Entry")

with st.form("sales_form"):
    s1, s2, s3, s4, s5, s6 = st.columns([1.2, 1.5, 1, 1, 1, 1])
    with s1:
        s_date = st.date_input("Date", key="s_date")
    with s2:
        s_customer = st.text_input("Customer Name", key="s_customer", placeholder="Enter customer name")
    with s3:
        s_item_rate = st.number_input("Item Rate (BHD)", min_value=0.0, format="%.3f", key="s_rate")
    with s4:
        s_quantity = st.number_input("Quantity", min_value=0.0, format="%.2f", key="s_qty")
    with s5:
        s_inr = s_quantity * 1000
        st.number_input("INR Value (auto)", value=s_inr, disabled=True, format="%.2f")
    with s6:
        s_bhd = s_item_rate * s_quantity
        st.number_input("BHD (auto)", value=s_bhd, disabled=True, format="%.3f")

    submitted_sales = st.form_submit_button("➕ Add Sales Entry", use_container_width=True)

if submitted_sales:
    if s_customer and s_item_rate > 0 and s_quantity > 0:
        st.session_state.sales_entries.append({
            "Date": s_date,
            "Customer": s_customer,
            "Item Rate (BHD)": s_item_rate,
            "Quantity": s_quantity,
            "INR": s_inr,
            "BHD": s_bhd
        })
        st.success("✅ Sales entry added successfully!")
        st.rerun()
    else:
        st.warning("⚠️ Please fill all sales fields correctly.")

# Show pending entries
if st.session_state.sales_entries:
    st.info(f"📝 **Pending Entries:** {len(st.session_state.sales_entries)} (Click 'Save All Data' to finalize)")
    df_sales = pd.DataFrame(st.session_state.sales_entries)
    st.dataframe(df_sales, use_container_width=True)
    st.write(f"**Pending Total - INR:** ₹{df_sales['INR'].sum():,.2f} | **BHD:** {df_sales['BHD'].sum():,.3f}")

# ==============================
# 💾 SAVE ALL DATA
# ==============================
st.markdown("---")
st.subheader("💾 Save & Finalize Data")

col_save1, col_save2 = st.columns(2)

with col_save1:
    if st.button("💾 Save All Data", use_container_width=True, type="primary"):
        # Merge pending entries with existing data
        if st.session_state.purchase_entries:
            new_purchase = pd.DataFrame(st.session_state.purchase_entries)
            st.session_state.purchase_data = pd.concat([st.session_state.purchase_data, new_purchase], ignore_index=True)
            st.session_state.purchase_entries = []
        
        if st.session_state.sales_entries:
            new_sales = pd.DataFrame(st.session_state.sales_entries)
            st.session_state.sales_data = pd.concat([st.session_state.sales_data, new_sales], ignore_index=True)
            st.session_state.sales_entries = []
        
        st.success("✅ All data saved successfully! You can now download the Excel file.")
        st.rerun()

with col_save2:
    # Download button
    if len(st.session_state.purchase_data) > 0 or len(st.session_state.sales_data) > 0:
        excel_file = create_excel_download(st.session_state.purchase_data, st.session_state.sales_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 Download Excel File",
            data=excel_file,
            file_name=f"MIS_Data_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("ℹ️ No data to download yet. Add some entries first!")

# ==============================
# 📊 SUMMARY & DATA DISPLAY
# ==============================
st.markdown("---")
st.subheader("📈 Summary Overview")

# Calculate summary
summary = calculate_summary(st.session_state.purchase_data, st.session_state.sales_data)

colA, colB, colC = st.columns(3)
with colA:
    st.metric("💸 Total Purchase", f"BHD {summary['Total Purchase (BHD)']:,.2f}")
with colB:
    st.metric("💰 Total Sales", f"BHD {summary['Total Sales (BHD)']:,.2f}")
with colC:
    profit_color = "normal" if summary['Gross Profit (BHD)'] >= 0 else "inverse"
    st.metric("📊 Gross Profit", f"BHD {summary['Gross Profit (BHD)']:,.2f}")

# ==============================
# 📋 ALL DATA TABLES
# ==============================
st.markdown("---")

tab1, tab2 = st.tabs(["🛒 Purchase Data", "💰 Sales Data"])

with tab1:
    if len(st.session_state.purchase_data) > 0:
        st.dataframe(st.session_state.purchase_data, use_container_width=True)
        st.write(f"**Total Records:** {len(st.session_state.purchase_data)}")
    else:
        st.info("📭 No purchase data yet. Add some entries above!")

with tab2:
    if len(st.session_state.sales_data) > 0:
        st.dataframe(st.session_state.sales_data, use_container_width=True)
        st.write(f"**Total Records:** {len(st.session_state.sales_data)}")
    else:
        st.info("📭 No sales data yet. Add some entries above!")

# ==============================
# 🗑️ CLEAR DATA (with confirmation)
# ==============================
st.markdown("---")
with st.expander("⚠️ Clear All Data (Danger Zone)", expanded=False):
    st.warning("⚠️ **WARNING:** This will permanently delete all data from the current session. Make sure you've downloaded the Excel file first!")
    
    confirm_text = st.text_input("Type 'DELETE' to confirm:", key="confirm_delete")
    
    if st.button("🗑️ Clear All Data", type="secondary"):
        if confirm_text == "DELETE":
            st.session_state.purchase_data = pd.DataFrame(columns=["Date", "Vendor", "Item Rate (BHD)", "Quantity", "INR", "BHD"])
            st.session_state.sales_data = pd.DataFrame(columns=["Date", "Customer", "Item Rate (BHD)", "Quantity", "INR", "BHD"])
            st.session_state.purchase_entries = []
            st.session_state.sales_entries = []
            st.success("✅ All data cleared! Starting fresh.")
            st.rerun()
        else:
            st.error("❌ Please type 'DELETE' to confirm.")

# ==============================
# 📌 FOOTER
# ==============================
st.markdown("---")
st.caption("💡 **How to use:** Upload existing Excel → Add new entries → Save → Download → Next time upload the same file to continue!")



