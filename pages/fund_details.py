import streamlit as st
import pandas as pd
from portfolio_utils import get_mf_tool,format_inr,buy_sell_txn,get_data,invested_value,portfolio_funds_list
from pyxirr import xirr
import plotly.graph_objects as go

if "selected_fund" not in st.session_state:
    st.switch_page("pages/equity_investments.py")
st.set_page_config(layout="wide")


#00C853"


if st.button("<- Back To Equity Portfolio",type="tertiary"):
    st.switch_page("pages/equity_investments.py")

def allocation_data():
    allocation_data_dict={}
    portfolio_data,funds_list=portfolio_funds_list()
    for fund in funds_list:
        allocation_data_dict[fund]=invested_value(portfolio_data,fund)
    allocation_df=pd.DataFrame(allocation_data_dict.items(),columns=["Fund Name","Current Value"]).sort_values(by="Current Value",ascending=False)
    return allocation_df


def fund_share_pie(df,selected_fund,fund_val,color="#3B82F6"):
    total_val=df["Current Value"].sum()
    other_val=total_val-fund_val
    share_pct=fund_val/total_val*100

    fig=go.Figure(go.Pie(
        labels=[selected_fund,'Others'],
        values=[fund_val,other_val],
        rotation=0,
        direction="clockwise",
        sort=False,
        marker=dict(
            colors=[color, "rgba(0,0,0,0)"],   # second slice = fully transparent
            line=dict(color="rgba(0,0,0,0)", width=0),  # no border on either slice
        ),
        textinfo="none",
        hoverinfo="skip",                # disable hover entirely (see note below)
        showlegend=False,texttemplate=["%{percent}", ""]
    ))
    fig.update_traces(
        textfont=dict(
            size=22,
            color="white",
            family="Inter, Arial"
        )
    )

    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=280
    )

    return fig

    

mf=get_mf_tool()
data=st.session_state.selected_fund
data=data.iloc[0]
# st.write(data)

details = mf.get_scheme_details(data["Code"])
fund_category=details.get("scheme_category", "Uncategorized")
fund_category=fund_category.split("-")
fund_details=data["Full Fund Name"].split("-")


st.markdown(f'# {data["Fund Name"]}')


st.caption(f'{fund_category[0]} | {fund_category[1]} | {fund_details[1]} | {fund_details[2]}')

row=st.columns(4)
invested_val=data["Invested Value"]
current_value=data["Current Value"]
absolute_return=(current_value/invested_val-1)*100
fund_xirr=data["XIRR"]
row[0].metric("Invested Value",value=format_inr(invested_val),border=True)
row[1].metric("Current Value",value=format_inr(current_value),border=True)
row[2].metric("P&L",value=format_inr(current_value-invested_val),border=True)
row[3].metric("Absolute Return",value=f'{absolute_return:.2f}%',border=True)
row[0].metric("XIRR", value=f'{fund_xirr:.2f}%',border=True)
row[1].metric("Units Holding",round(data["Units Holding"],3),border=True)
row[2].metric("Average Buying Price",value=f'₹{data["Avg Buying NAV"]:.2f}',border=True)
row[3].metric("Current NAV",value=f'₹{data["Current NAV"]:.2f}',border=True)

st.markdown("#### Holding Details")
buy_txn,sell_txn=buy_sell_txn(get_data(),data["Full Fund Name"])


holdings=[]
buy_txn=buy_txn.sort_values(by='Date',ascending=True)
units_sold=sum(sell_txn["Units"])
nav=data["Current NAV"]

for idx,row in buy_txn.iterrows():
    if units_sold ==0:
        units_holding=row["Units"]
        amount_paid=row["Amount"]
    elif units_sold>=row["Units"]:
        units_sold-=row["Units"]
        units_holding=0
        continue
    elif units_sold>0:
        units_holding=row["Units"]-units_sold
        units_sold=0
        amount_paid=row["Amount"]/row["Units"]*units_holding

    current_val=units_holding*nav
    profit=current_val-amount_paid
    return_pct=profit/amount_paid*100
    today=pd.Timestamp.today()
    cagr=xirr([row['Date'],today],[-amount_paid,current_val])*100
    holdings.append({
        "Date Of Purchase":row['Date'],
        'Units Holding':f'{units_holding:.3f}',
        'Invested Amount':format_inr(amount_paid),
        'Current Amount':format_inr(current_val),
        'Average Buying Nav':(f'{amount_paid/units_holding:.2f}'),
        'P&L':format_inr(profit),
        'Absolute Return':(f'{return_pct:.2f}%'),
        'XIRR':f'{cagr:.2f}%'

    })


holdings_df=pd.DataFrame(holdings)
holdings_df["Date Of Purchase"]=holdings_df['Date Of Purchase'].dt.date
st.dataframe(holdings_df,hide_index=True)

st.markdown("#### Portfolio Share")
col1,col2=st.columns(2)
allocation_df=allocation_data()
# st.dataframe(allocation_df)
fig=fund_share_pie(allocation_df,data["Fund Name"],invested_val)
col1.plotly_chart(fig,width="stretch")

