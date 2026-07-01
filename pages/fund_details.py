import streamlit as st
import pandas as pd
from portfolio_utils import get_mf_tool,format_inr,buy_sell_txn,get_data,invested_value,portfolio_funds_list,get_historical_nav,get_conn
from pyxirr import xirr
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime,timedelta
import requests
from yahooquery import Ticker


if "selected_fund" not in st.session_state:
    st.switch_page("pages/equity_investments.py")
st.set_page_config(layout="wide")


#00C853"


if st.button("<- Back To Equity Portfolio",type="tertiary"):
    st.switch_page("pages/equity_investments.py")

def allocation_data():
    portfolio_data,funds_list=portfolio_funds_list()
    allocation_data_dict={}
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
        margin=dict(t=10, b=10, r=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=500,
    )

    return fig



def nav_chart_data(nav_data,option):
    option_matrix={
        "7 Days":7,
        "1 Month":30,
        "1 Year":365,
        "3 Years":3*365,
        "5 Years":5*365,
        "All":0
    }
    period=option_matrix[option]
    if period==0:
        chart_data=nav_data[['date','nav']]
        return chart_data
    else:
        today=datetime.today()
        last_date=today-timedelta(period)
        chart_data=nav_data[(nav_data['date']>=last_date)]
        return chart_data[['date','nav']]

 

@st.cache_data(ttl=86400 * 30)  # ISIN never changes for a scheme, cache aggressively
def get_or_fetch_isin(scheme_code):
    """Returns ISIN from DB cache if available, otherwise fetches once and stores it."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT ISIN FROM MF_Fund_Meta WHERE Scheme_Code=?", (str(scheme_code),)
        ).fetchone()
        if row and row[0]:
            return row[0]

    # Not in DB yet — fetch once from mfapi.in
    try:
        resp = requests.get(f"https://api.mfapi.in/mf/{scheme_code}", timeout=15)
        if resp.status_code == 200:
            meta = resp.json().get("meta", {})
            isin = meta.get("isin_growth")
            fund_house = meta.get("fund_house")
            category = meta.get("scheme_category")
            with get_conn() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO MF_Fund_Meta
                       (Scheme_Code, ISIN, Fund_House, Category)
                       VALUES (?, ?, ?, ?)""",
                    (str(scheme_code), isin, fund_house, category)
                )
                conn.commit()
            return isin
    except Exception:
        return None

    
@st.cache_data(ttl=86400)
def get_fund_details(isin):
    resp = requests.get(f"https://mf.captnemo.in/kuvera/{isin}")
    if resp.status_code == 200:
        data = resp.json()
        fund = data[0] if isinstance(data, list) and len(data) > 0 else data
        return fund
    return {}


 
def get_yahoo_ticker(isin):
    """Search Yahoo Finance by fund name to get the .BO ticker automatically."""
    try:
        resp = requests.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": isin, "lang": "en-US", "type": "mutualfund"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        if resp.status_code == 200:
            results = resp.json().get("quotes", [])
            for r in results:
                if r.get("quoteType") == "MUTUALFUND":
                    return r.get("symbol")
    except Exception:
        return None
    
def get_or_fetch_yahoo_ticker(scheme_code,isin):
    # Check DB first
    with get_conn() as conn:
        row = conn.execute(
            "SELECT Yahoo_Ticker FROM MF_Fund_Meta WHERE Scheme_Code=?",
            (str(scheme_code),)
        ).fetchone()
        if row and row[0]:
            return row[0]

    # Not cached — search Yahoo
    ticker = get_yahoo_ticker(isin)
    if ticker:
        with get_conn() as conn:
            conn.execute(
                "UPDATE MF_Fund_Meta SET Yahoo_Ticker=? WHERE Scheme_Code=?",
                (ticker, str(scheme_code))
            )
            conn.commit()
    return ticker



@st.cache_data(ttl=86400)  # holdings update monthly, cache for a day
def get_fund_holdings(scheme_code,ticker_symbol):
    # ticker_symbol = YAHOO_TICKERS.get(scheme_code)
    if not ticker_symbol:
        return None, None
    ticker = Ticker(ticker_symbol)
    holdings = ticker.fund_top_holdings        # DataFrame: holdingName, holdingPercent
    sectors = ticker.fund_sector_weightings    # DataFrame: sector, percentage
    return holdings, sectors



def color_pl(value):
    if value > 0:
        return "color: #00C853; font-weight: bold;"
    elif value < 0:
        return "color: #FF5252; font-weight: bold;"
    return ""


#-------------------------------------------------------------------------------Body-------------------------------------------------------------------------------

mf=get_mf_tool()
data=st.session_state.selected_fund
data=data.iloc[0]
# st.write(data)

details = mf.get_scheme_details(data["Code"])
fund_category=details.get("scheme_category", "Uncategorized")
fund_category=fund_category.split("-")
fund_details=data["Full Fund Name"].split("-")
isin=(get_or_fetch_isin(data["Code"]))
full_fund_details=get_fund_details(isin)

#--Header--
if full_fund_details.get("small_screen_name") != None:
    st.markdown(f'# {full_fund_details.get("small_screen_name")}')
else:
    st.markdown(f'# {fund_details[0]}')

if full_fund_details:
    rating=full_fund_details.get("fund_rating")
    stars="★" * rating + "☆"* (5-rating)
    st.write(f'{fund_category[0]} | {fund_category[1]} | {fund_details[1]} | {fund_details[2]} | {stars}')


#------Displaying Matrics-----

row=st.columns(4)
invested_val=data["Invested Value"]
current_value=data["Current Value"]
absolute_return=(current_value/invested_val-1)*100
fund_xirr=data["XIRR"]



row[0].metric("Invested Value",value=format_inr(invested_val),border=True)
row[1].metric("Current Value",value=format_inr(current_value),border=True)
row[2].metric("P&L",value=format_inr(current_value-invested_val),border=True)
row[3].metric("Absolute Portfolio Returns",value=f'{absolute_return:.2f}%',border=True)
row[0].metric("XIRR", value=f'{fund_xirr:.2f}%',border=True)
row[1].metric("Units Holding",round(data["Units Holding"],3),border=True)
row[2].metric("Average Buying Price",value=f'₹{data["Avg Buying NAV"]:.2f}',border=True)
row[3].metric("Current NAV",value=f'₹{data["Current NAV"]:.2f}',border=True)


#-----Plotting Nav Chart And Displaying Nav Data-----
st.markdown("#### Fund Performance")
col1,buff,col2,col3=st.columns([12,0.25,2,2])
nav_data=get_historical_nav(data["Code"])
time_period=col1.radio("Select Time Period",options=["7 Days", "1 Month", "1 Year","3 Years", "5 Years", "All"],horizontal=True,index=2,label_visibility="collapsed")
chart_data=nav_chart_data(nav_data,time_period)
fig=go.Figure()
fig.add_trace(go.Scatter(
    x=chart_data['date'],
    y=chart_data['nav'],
    mode='lines',line=dict( width=3, dash="solid"),
    hovertemplate="₹%{y:,.2f}<extra></extra>"
))
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="NAV (₹)",
    template="plotly_white",
    margin=dict(t=5)
)
col1.plotly_chart(fig,width="stretch")

#Column 2 Data 
col2.space(25)
col3.space(25)


#------------------------------Showing returns Data in metrics------------------------------
# Styling for delta of metric
st.markdown("""
<style>
div[data-testid="stMetricDelta"] {
    font-size: 1.2rem !important;
    font-weight: 400;
}
</style>
""", unsafe_allow_html=True)
if full_fund_details:
    last_nav=full_fund_details.get("nav").get("nav")
    second_last_nav=full_fund_details.get("last_nav").get("nav")
    one_day_delta=f'{round((last_nav-second_last_nav)/second_last_nav*100,2)}%'
    returns=full_fund_details.get("returns")
    col2.metric("1 Day Change",value="",delta=one_day_delta,border=True)
    col2.metric("1 Year Return",value="",delta=f'{round(float(returns["year_1"]),2)}%',border=True)
    col2.metric("5 Year CAGR",value="",delta=f'{round(float(returns["year_5"]),2)}%',border=True)
    col3.metric("1 Week Return",value="",delta=f'{round(float(returns["week_1"]),2)}%',border=True)
    col3.metric("3 Year CAGR",value="",delta=f'{round(float(returns["year_3"]),2)}%',border=True)
    col3.metric("Life Time CAGR",value="",delta=f'{round(float(returns["inception"]),2)}%',border=True)



col2.space(1)
col3.space(6)
nav_history=mf.get_scheme_historical_nav(data["Code"])
high_52_week=nav_history['52_week_high']
col2.markdown(f'* 52 week high:')
col3.markdown(f'**₹ {float(high_52_week):.2f}**')
low_52_week=nav_history['52_week_low']
col2.markdown(f'* 52 week low:')
col3.markdown(f'**₹ {float(low_52_week):.2f}**')









st.markdown("#### Fund Details")
col4,col5=st.columns([1,1.5])
allocation_df=allocation_data()
# st.dataframe(allocation_df)
fig=fund_share_pie(allocation_df,data["Fund Name"],invested_val)
col4.plotly_chart(fig,width="stretch")
if full_fund_details:
    expense_ratio=full_fund_details.get("expense_ratio")
    aum=full_fund_details.get("aum")/10
    col5.markdown(f'* **Expense Ratio:** {expense_ratio}%')
    col5.markdown(f'* **Fund AUM:** {format_inr(aum)} Cr')
    col5.markdown(f'* **Volatility:** {float(full_fund_details.get("volatility")):.2f}%')
    rating=full_fund_details.get("fund_rating")
    stars="★" * rating + "☆"* (5-rating)
    col5.markdown(f"* **Ratings**\n  * **Fund Rating:** {stars}\n  * **SEBI's Risk Category:** {full_fund_details.get("crisil_rating")}")
    fund_managers=full_fund_details.get("fund_manager")
    if ";" in fund_managers:
        fund_managers_list=fund_managers.split(";")
        if len(fund_managers_list)<=3:
            txt=("* **Fund Managers**")
            for fund_manager in fund_managers_list:
                txt=txt+"\n  * "+fund_manager
            col5.markdown(txt)
        else:
            txt=("* **Fund Managers**")
            for i in range(2):
                txt=txt+"\n  * "+fund_managers_list[i]
            col5.markdown(txt)
            with col5.expander(f"View all {len(fund_managers_list)} fund managers"):
                for manager in fund_managers_list[2:]:
                    st.markdown(f"* {manager}")
    col5.markdown(f'* **Fund Objective:** {full_fund_details.get("investment_objective")}')



col6,space,col7=st.columns([1,0.05,1])
col6.markdown("#### Top Holdings")
col7.markdown('#### Sectoral Allocation')


ticker=get_or_fetch_yahoo_ticker(data["Code"],isin)
mf_holdings,sectors=get_fund_holdings(ticker_symbol=ticker,scheme_code=data["Code"])

#------------Top Holdings---------------#
holdings_df=mf_holdings[['holdingName','holdingPercent']]
holdings_df=holdings_df.rename(columns={"holdingName":'Holding Name','holdingPercent':"Portfolio Weightage"})
holdings_df["Portfolio Weightage"] = holdings_df["Portfolio Weightage"] * 100  



col6.dataframe(
    holdings_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Holding Name": st.column_config.TextColumn("Holding Name", width="large"),
        "Portfolio Weightage": st.column_config.ProgressColumn(
            "Portfolio Weightage",
            min_value=0,
            max_value=holdings_df["Portfolio Weightage"].max(),
            format="%.2f%%",
        ),
    }
)

#------------Sectoral Allocation--------------#
sectors = sectors.reset_index()
sectors.columns = ["Sector", "Weightage"]
sectors["Weightage"]=sectors["Weightage"]*100
sectors=sectors.sort_values(by="Weightage",ascending=False)
sectors["Sector"] = (
    sectors["Sector"]
    .str.replace("_", " ")
    .str.title()
)
hovertemplate = (
    "<b>%{label}</b><br>"
    "Portfolio Allocation: <b>%{value:.2f}%</b>"
    "<extra></extra>"
)
fig=px.pie(sectors,values="Weightage",names="Sector")
fig.update_traces(direction="clockwise",hovertemplate=hovertemplate)
col7.plotly_chart(fig,width="stretch")



#--------------------------------Similar Funds--------------------------------
st.markdown("#### Similar Funds")
comparison_data=full_fund_details.get("comparison")
comparison_df=pd.DataFrame(comparison_data)



row_comparison=st.columns(len(comparison_df))
for idx,row in comparison_df.iterrows():
    with row_comparison[idx].container(border=True):
        if row["short_name"]==full_fund_details.get("small_screen_name"):
            st.markdown(f'###### ✓ {row["short_name"]}')
        else:
            st.markdown(f'###### {row["short_name"]}')
        st.markdown("---")
        returns=[row["1y"],row["3y"],row["5y"],row["inception"]]
        modified_returns = ['--' if cagr == 0.0 else cagr for cagr in returns]

        st.markdown(f"* Returns\n  * 1Y CAGR: {modified_returns[0]}%\n  * 3Y CAGR: {modified_returns[1]}%\n  * 5Y CAGR: {modified_returns[2]}%\n  * Lifetime CAGR: {modified_returns[3]}%")
        
        st.markdown(f'* AUM: {format_inr(row["aum"]/10)} Cr')
        st.markdown(f'* Volatility: {row["volatility"]:.2f}%')
        st.markdown(f'* Expense Ratio: {row["expense_ratio"]}')
        st.markdown(f'* Information Ratio: {row["info_ratio"]}')
st.caption("ℹ Information Ratio measures how consistently a fund beats its benchmark after adjusting for risk.")








#----------Holdings Data----------
st.space()
st.markdown("#### Transaction Details")
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
    return_pct=profit/amount_paid
    today=pd.Timestamp.today()
    cagr=xirr([row['Date'],today],[-amount_paid,current_val])
    holdings.append({
        "Date Of Purchase":row['Date'],
        'Units Holding':units_holding,
        'Invested Amount':amount_paid,
        'Current Amount':current_val,
        'Average Buying Nav':float(amount_paid/units_holding),
        'P&L':float(profit),
        'Absolute Returns':float(return_pct),
        'XIRR':float(cagr)

    })


holdings_df=pd.DataFrame(holdings)
holdings_df["Date Of Purchase"]=holdings_df['Date Of Purchase'].dt.date


styled_df = (
    holdings_df.style
    .map(color_pl, subset=["P&L"])
    .map(color_pl, subset=["Absolute Returns"])
    .map(color_pl, subset=["XIRR"])
)

formated_df=styled_df.format({
    "Invested Amount": format_inr,
    "Current Amount": format_inr,
    "P&L": format_inr,
    "Average Buying NAV": "₹{:.2f}",
    "Absolute Returns": "{:.2%}",
    "XIRR": "{:.2%}",
    "Units Holding":"{:.3f}"
}
)
st.dataframe(formated_df,hide_index=True)




#---------------------Tax Details---------------------

# st.markdown("#### Tax Details")