import streamlit as st
from config import database_file
from portfolio_utils import portfolio_builder,portfolio_xirr
import pandas as pd

st.set_page_config(layout="wide")

st.markdown("## Equity Portfolio")
df_list=portfolio_builder()

def format_inr(number):
    number = round(number)
    sign = "-" if number < 0 else ""
    number = abs(number)

    s = str(number)
    if len(s) <= 3:
        return f"{sign}₹{s}"

    last3 = s[-3:]
    rest = s[:-3]

    parts = []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)

    return f"{sign}₹{','.join(parts)},{last3}"



def color_pl(value):
    if value > 0:
        return "color: #00C853; font-weight: bold;"
    elif value < 0:
        return "color: #FF5252; font-weight: bold;"
    return ""
df=pd.DataFrame(df_list)



total_row = {
    "Fund Name": "TOTAL",
    "Invested Value": df["Invested Value"].sum(),
    "Current Value": df["Current Value"].sum(),
    "P&L": df["P&L"].sum(),
    "XIRR":portfolio_xirr(df["Current Value"].sum()),
    "Absolute Returns":((df["Current Value"].sum()/df["Invested Value"].sum()-1)*100),

}
df = pd.concat(
    [df, pd.DataFrame([total_row])],
    ignore_index=True
)

def highlight_total(row):
    if row["Fund Name"] == "TOTAL":
        return ["background-color: #262730; font-weight: bold; border-top: 2 px solid #555;"] * len(row)
    return [""] * len(row)


#-----------------------------------------------------------------------------Body-----------------------------------------------------------------------------

row1=st.columns(6)

total_row = df.loc[
    df["Fund Name"] == "TOTAL"
].iloc[0]

invested = total_row["Invested Value"]
current = total_row["Current Value"]
profit = total_row["P&L"]
return_pct = total_row["Absolute Returns"]
xirr = total_row["XIRR"]
holdings=len(df)-1

row1[0].metric("Invested Value",format_inr(invested),border=True)
row1[1].metric("Absolute Returns",f"{return_pct:.2f}%",border=True)

row1[2].metric("Current Value",format_inr(current),border=True)
row1[3].metric("XIRR",f"{xirr:.2f}%",border=True)

row1[4].metric("P&L",format_inr(profit),border=True)
row1[5].metric("No. Of Holdings",holdings,border=True)










styled_df = (
    df.style
    .apply(highlight_total, axis=1)
    .map(color_pl, subset=["P&L"])
    .map(color_pl, subset=["Absolute Returns"])
    .map(color_pl, subset=["XIRR"])
)
formated_df=styled_df.format({
    "Invested Value": format_inr,
    "Current Value": format_inr,
    "P&L": format_inr,
    "Avg Buying NAV": "₹{:.2f}",
    "Current NAV": "₹{:.2f}",
    "Absolute Returns": "{:.2%}",
    "XIRR": "{:.2%}",
    "Units Holding":"{:.3f}"
},na_rep=""
)

















event=st.dataframe(
    formated_df,
    on_select="rerun",
    hide_index=True,
    selection_mode="single-cell",
    use_container_width=True,
    column_config={
        "Fund Name": st.column_config.TextColumn("Fund Name"),
        "Invested Value": st.column_config.NumberColumn("Invested Value"),
        "Units Holding":st.column_config.NumberColumn("Units Holding",format="%.3f"),
        "Avg Buying NAV": st.column_config.NumberColumn("Avg Buying NAV", format="₹%.2f"),
        "Current NAV": st.column_config.NumberColumn("Current NAV", format="₹%.2f"),
        "Current Value": st.column_config.NumberColumn("Current Value"),
        "P&L": st.column_config.NumberColumn("P&L"),
        "Absolute Returns": st.column_config.NumberColumn("Absolute Return", format="%.2f%%"),
        "XIRR": st.column_config.NumberColumn("XIRR", format="%.2f%%")
    }
)

selected_cells = event.selection.get("cells", [])
df=pd.DataFrame(df_list)
if selected_cells:
    row_idx, col_name = selected_cells[0]
    selected_fund = df.iloc[row_idx]["Fund Name"]
    st.session_state["selected_fund"] = selected_fund
    # st.switch_page("pages/fund_details.py")
    st.write(st.session_state.selected_fund)
