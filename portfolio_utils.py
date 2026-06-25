import streamlit as st
import pandas as pd
from database import get_conn
from mftool import Mftool
from datetime import date
from pyxirr import xirr


#----------------------------------------------------------Functions----------------------------------------------------------
@st.cache_data
def get_data():
    with get_conn() as conn:
        df=pd.read_sql_query("SELECT * FROM MF_Transactions",conn)
    df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce")
    return df


@st.cache_resource
def get_mf_tool():
    return Mftool()

def portfolio_funds_list():
    #Getting Funds List From Portfolio
    portfolio_data_df=get_data()
    options_list=portfolio_data_df["Fund_Name"].unique().tolist()
    return portfolio_data_df,options_list


def buy_sell_txn(portfolio_data,fund_name):
    buy_transaction=portfolio_data[
        (portfolio_data["Fund_Name"]==fund_name)&
        (portfolio_data["Transaction_Type"]=="Buy")
    ]
    sell_transaction=portfolio_data[
        (portfolio_data["Fund_Name"]==fund_name)&
        (portfolio_data["Transaction_Type"]=="Sell")
    ]
    return buy_transaction,sell_transaction


def calculate_remaining_units(buy_transactions,sold_units_total):
    remaining = buy_transactions.copy()
    remaining["Units Left"] = remaining["Units"]

    for idx, row in remaining.iterrows():
        if sold_units_total <= 0:
            break

        if sold_units_total >= row["Units"]:
            remaining.at[idx, "Units Left"] = 0
            sold_units_total -= row["Units"]
        else:
            remaining.at[idx, "Units Left"] = row["Units"] - sold_units_total
            sold_units_total = 0
            break

    return remaining


def invested_value(portfolio_data,fund_name):
    buy_transactions,sell_transactions=buy_sell_txn(portfolio_data,fund_name)
    sold_units_total=round(sell_transactions["Units"].sum(),3)
    remaing_units_df=calculate_remaining_units(buy_transactions,sold_units_total)
    invested_value=0
    for idx, row in remaing_units_df.iterrows():
        if row["Units Left"]>0:
            cost_of_units_left=row["Amount"]/row["Units"]*row["Units Left"]
            invested_value+=cost_of_units_left
    
    return round(invested_value,2)


def net_units(portfolio_data,fund_name):
    buy_transactions,sell_transactions=buy_sell_txn(portfolio_data,fund_name)
    sold_units_total=round(sell_transactions["Units"].sum(),3)
    bought_units_total=round(buy_transactions["Units"].sum(),3)
    return bought_units_total-sold_units_total


def fund_nav(portfolio_data,fund):
    mf=get_mf_tool()
    code=portfolio_data.loc[(portfolio_data["Fund_Name"]==fund),"Scheme_Code"].iloc[0]
    details=mf.get_scheme_quote(code)
    return details['nav']


def get_xirr(portfolio_data,fund_name,current_value):
    today=date.today()
    buy_transactions,sell_transactions=buy_sell_txn(portfolio_data,fund_name)
    dates=[]
    amounts=[]
    for idx,row in buy_transactions.iterrows():
        dates.append(row["Date"].date())
        amt=row["Amount"]
        amounts.append(amt*-1)
    for idx,row in sell_transactions.iterrows():
        dates.append(row["Date"].date())
        amt=row["Amount"]
        amounts.append((amt))
    dates.append(today)
    amounts.append(current_value)
    return (xirr(dates,amounts))


def portfolio_xirr(current_portfolio_value):
    portfolio_data=get_data()
    buy_dates_df=portfolio_data.loc[(portfolio_data["Transaction_Type"]=="Buy"),"Date"]
    buy_dates=buy_dates_df.to_list()

    sell_dates_df=portfolio_data.loc[(portfolio_data["Transaction_Type"]=="Sell"),"Date"]
    sell_dates=sell_dates_df.to_list()
    
    dates=sell_dates+buy_dates

    buy_txn=portfolio_data.loc[(portfolio_data["Transaction_Type"]=="Buy"),"Amount"]
    sell_txn=portfolio_data.loc[(portfolio_data["Transaction_Type"]=="Sell"),"Amount"]
    amounts=sell_txn.to_list()
    buy_txn_list=buy_txn.to_list()
    for x in buy_txn_list:
        amounts.append(-x)
    today=date.today()
    dates.append(today)
    amounts.append(current_portfolio_value)
    return xirr(dates,amounts)*100


def portfolio_builder():
    portfolio=[]
    portfolio_data_df,funds_list=portfolio_funds_list()
    for fund in funds_list:
        invested_value_var=invested_value(portfolio_data_df,fund)
        net_units_var=net_units(portfolio_data_df,fund)
        nav=float(fund_nav(portfolio_data_df,fund))
        current_value_var=nav*net_units_var
        fund_split=fund.split("-")
        fund_name=fund_split[0]
        portfolio.append({
            "Fund Name":fund_name,
            "Invested Value":invested_value_var,
            "Units Holding":net_units_var,
            "Avg Buying NAV":invested_value_var/net_units_var,
            "Current NAV":nav,
            "Current Value": current_value_var,
            "P&L":current_value_var-invested_value_var,
            "Absolute Returns": (current_value_var/invested_value_var-1)*100,
            "XIRR":get_xirr(portfolio_data_df,fund,current_value_var)*100
        })
    
    return portfolio






