import streamlit as st
from config import database_file
from portfolio_utils import portfolio_builder,portfolio_xirr,category_allocation
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.markdown("## Equity Portfolio")

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



df_list=portfolio_builder()
df=pd.DataFrame(df_list)






#-----------------------------------------------------------------------------Body-----------------------------------------------------------------------------


#----------------Summary Cards----------------#
row1=st.columns(5)



invested = df["Invested Value"].sum()
current = df["Current Value"].sum()
profit = df["P&L"].sum()
return_pct = ((df["Current Value"].sum()/df["Invested Value"].sum()-1)*100)
xirr = portfolio_xirr(df["Current Value"].sum())
holdings=len(df)

row1[0].metric("Invested Value",format_inr(invested),border=True)
row1[1].metric("Current Value",format_inr(current),border=True)
row1[2].metric("P&L",format_inr(profit),border=True)
row1[3].metric("Absolute Returns",f"{return_pct:.2f}%",border=True)
row1[4].metric("XIRR",f"{xirr:.2f}%",border=True)

# row1[5].metric("No. Of Holdings",holdings,border=True)




#--------------Portfolio Data/Table--------------#



df=df.sort_values(by="Invested Value",ascending=False)


styled_df = (
    df.style
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
}
)



event=st.dataframe(
    formated_df,
    on_select="rerun",
    hide_index=True,
    selection_mode="single-cell",
    width="stretch",
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
# df=pd.DataFrame(df_list)
if selected_cells:
    row_idx, col_name = selected_cells[0]
    selected_fund = df.iloc[row_idx]["Fund Name"]
    st.session_state["selected_fund"] = selected_fund
    # st.switch_page("pages/fund_details.py")
    st.write(st.session_state.selected_fund)

#---------------------------------Pie Chart---------------------------------

col1,col2=st.columns(2)
#Fund Allocation

allocation_dict={}
for idx,row in df.iterrows():
     allocation_dict[row["Fund Name"]]=f'{row["Current Value"]:.0f}'

allocation=pd.DataFrame(allocation_dict.items(),columns=["Fund Name","Current Value"]).sort_values(by="Current Value",ascending=False)
fig=px.pie(allocation,values="Current Value",names="Fund Name")
fig.update_traces(direction="clockwise")
col1.plotly_chart(fig)


#Category Allocation

category_allocation=pd.DataFrame(category_allocation().items(),columns=["Category","Current Value"]).sort_values(by="Current Value",ascending=False)
category_allocation["Category"] = (
    category_allocation["Category"]
    .str.split(" - ")
    .str[-1]
)
fig=px.pie(category_allocation,values="Current Value",names="Category")
fig.update_traces(direction="clockwise")

col2.plotly_chart(fig)

