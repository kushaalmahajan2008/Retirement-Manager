import streamlit as st
from config import database_file
from portfolio_utils import portfolio_builder,portfolio_xirr,category_allocation,build_portfolio_value_history,investment_history,monthly_flow,format_inr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta



st.set_page_config(layout="wide")

st.markdown("## Equity Portfolio")





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
        "XIRR": st.column_config.NumberColumn("XIRR", format="%.2f%%"),
        "Full Fund Name":None,
        "Code":None
    }
)

# Redirecting To details page


selected_cells = event.selection.get("cells", [])
if selected_cells:
    row_idx, col_name = selected_cells[0]
    selected_fund = df.iloc[row_idx]["Fund Name"]
    # st.session_state["selected_fund"] = selected_fund
    st.session_state["selected_fund"]=df.loc[df["Fund Name"]==selected_fund]
    st.session_state["data"]=df
    st.switch_page("pages/fund_details.py")

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


tab1, tab2, tab3, tab4, tab5= st.tabs([
    "📊 Growth",
    "📈 Portfolio History",
    "📅 Cashflow Timeline",
    "🏆 Returns",
    "⚠️ Risk Parameters"
])


#History And Future Projections Chart
history_df=(build_portfolio_value_history('MS'))

current_value=current
current_xirr=xirr/100

today = history_df["Date"].iloc[-1]
projection_dates = [today + relativedelta(years=y) for y in range(0, 21)]
projection_values = [round(current_value * (1 + current_xirr) ** y,0) for y in range(0, 21)]
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=history_df["Date"], y=history_df["Portfolio Value"],
    mode="lines",name="Portfolio Value (Actual)",
    line=dict( width=3, dash="solid"),
    hovertemplate="₹%{y:,.0f}<extra></extra>"
))

fig.add_trace(go.Scatter(
    x=projection_dates, y=projection_values,
    mode="lines", name="Projected (at current XIRR)",
    line=dict(color="#00C853", width=2, dash="dot"),
    hovertemplate="₹%{y:,.0f}<extra></extra>"
))
fig.add_vline(x=today, line_dash="dash", line_color="gray", annotation_text="Today")

fig.add_trace(
    go.Scatter(
        x=projection_dates,
        y=projection_values,
        mode="lines",
        line=dict(width=0),
        fill="tozeroy",
        fillcolor="rgba(0,200,83,0.08)",
        showlegend=False,
        hoverinfo="skip"
    )
)

fig.update_layout(
    template="plotly_dark",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    yaxis_title="Portfolio Value (₹)"
)

with tab1:
    st.write("Portfolio History & Future Projection")
    st.plotly_chart(fig, width="stretch")
    st.caption("Note: Projections are based on Current Portfolio XIRR. Actual Return May Vary")



#Portfolio Value V/s Invested Value
history_df=build_portfolio_value_history('W')
investment_history_df=investment_history()

fig=go.Figure()
fig.add_trace(go.Scatter(
    x=history_df["Date"], y=history_df["Portfolio Value"],
    mode="lines",name="Portfolio Value",
    line=dict(color="#00C853", width=2, dash="solid"),
    hovertemplate="₹%{y:,.0f}<extra></extra>"
))

fig.add_trace(go.Scatter(
    x=investment_history_df["Date"],y=investment_history_df["Invested Amount"],
    mode="lines",name="Invested Value",
    line=dict(width=2, dash="solid"),
    hovertemplate="₹%{y:,.0f}<extra></extra>"
))
fig.update_layout(
    template="plotly_dark",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    yaxis_title="Portfolio Value (₹)"
)

with tab2:
    st.write("Portfolio Value V/s Invested Value")
    st.plotly_chart(fig,width="stretch")


#Investment Timeline
monthly_flows=monthly_flow()
fig_flows = go.Figure()

fig_flows.add_trace(go.Bar(
    x=monthly_flows["Month"], y=monthly_flows["Buy"],
    name="Inflow (Buy)", marker_color="#00C853",
    hovertemplate="₹%{y:,.0f}<extra></extra>"
))

fig_flows.add_trace(go.Bar(
    x=monthly_flows["Month"], y=monthly_flows["Sell"],
    name="Outflow (Sell)", marker_color="#FF5252",
    hovertemplate="₹%{customdata:,.0f}<extra></extra>",
    customdata=-monthly_flows["Sell"]  # show as a positive number on hover, even though the bar is negative
))

fig_flows.add_hline(y=0, line_color="gray", line_width=1)

fig_flows.update_layout(
    template="plotly_dark",
    barmode="relative",
    xaxis_title="Month",
    yaxis_title="Amount (₹)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(l=10, r=10, t=60, b=10),
)
with tab3:
    st.write("Monthly Inflows v/s Outflows")
    st.plotly_chart(fig_flows,width="stretch")




#Returns Comparison 

returns_df = df.sort_values("XIRR", ascending=True)

colors = ["#FF5252" if v < 0 else "#00C853" for v in returns_df["XIRR"]]
fig_returns = go.Figure(go.Bar(
    x=returns_df["XIRR"],
    y=returns_df["Fund Name"],
    orientation="h",
    marker_color=colors,
    text=[f"{v:.2f}%" for v in returns_df["XIRR"]],
    textposition="outside",
    hovertemplate="%{y}: %{x:.2f}%<extra></extra>"
))

fig_returns.update_layout(
    template="plotly_dark",
    title="Returns by Fund (XIRR)",
    xaxis_title="XIRR (%)",
    margin=dict(l=10, r=10, t=40, b=10),
)

with tab4:
    st.write("Returns Comparison")
    st.plotly_chart(fig_returns, use_container_width=True)

with tab5:
    st.title("Coming Soon...")
    st.write("risk parameters in metrics")
