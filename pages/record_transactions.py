import streamlit as st
import pandas as pd
from mftool import Mftool
from datetime import datetime
import sqlite3
from config import EQUITY_LTCG_TAX_RATE,EQUITY_STCG_TAX_RATE,database_file
from database import get_conn

#----------------------------------------------------------Functions----------------------------------------------------------

def init_buy_session_state():
    if "Fund Name" not in st.session_state:
        st.session_state["Fund Name"]=""
    if "units" not in st.session_state:
        st.session_state["units"]=0
    if "amount" not in st.session_state:
        st.session_state["amount"]=0

@st.cache_resource
def get_mf_tool():
    return Mftool()

@st.cache_data
def get_mf_data():
    mutual_code_fund=mf.get_scheme_codes()
    mutual_fund_code = {
        name: code
        for code, name in mutual_code_fund.items()
    }
    return mutual_code_fund,mutual_fund_code


def check_fields():
    if choice=="Sell":
        scheme_name=st.session_state["Fund Name"]
        if scheme_name!="" or scheme_name!='Select Mutual Fund Name':
            number_of_units_bought=portfolio_data_df.loc[(portfolio_data_df["Fund_Name"]==scheme_name) & (portfolio_data_df["Date"].dt.date<=transaction_date) & (portfolio_data_df["Transaction_Type"]=="Buy"),"Units"]
            number_of_units_sold=portfolio_data_df.loc[(portfolio_data_df["Fund_Name"]==scheme_name) &(portfolio_data_df["Transaction_Type"]=="Sell"),"Units"]
            total_units=sum(number_of_units_bought)-sum(number_of_units_sold)
        if st.session_state["units"]>total_units:
            st.session_state["error_msg"]="Sale Units Cannot be more than Available Units"
    if st.session_state["Fund Name"]=="" or st.session_state["Fund Name"]=="Select Mutual Fund Name":
        st.session_state["error_msg"]=("Please Select A mutual fund")
        return False
    elif st.session_state["units"]<=0:
        st.session_state["error_msg"]=("Please Enter Units")
        return False
    elif st.session_state["amount"]==0:
        st.session_state["error_msg"]=("Please Enter Amount")
        return False
    else:
        return True
    
    
def clear_fields():
    # st.session_state["Date"]=datetime.now().date()
    st.session_state["Fund Name"]=""
    st.session_state["units"]=0
    st.session_state["amount"]=0


def prev_transaction(choice):
    units=st.session_state["units"]
    amount=st.session_state["amount"]
    avg=amount/units
    prev_transaction_data={
        "Choice":choice,
        "Date":st.session_state["Date"],
        "Fund Name":st.session_state["Fund Name"],
        "Scheme Code":st.session_state["scheme code"],
        "Units":units,
        "Amount":amount,
        "Average Buying Price":f'{avg:.3f}'
    }
    st.session_state["prev_transaction"]=prev_transaction_data


def store_data():
    data=(st.session_state["Date"],st.session_state["choice"],st.session_state["Fund Name"],st.session_state["scheme code"],st.session_state["units"],st.session_state["amount"])
    record_transaction="""INSERT INTO MF_Transactions
    (Date,Transaction_Type,Fund_Name,Scheme_Code,Units,Amount)
    VALUES(?,?,?,?,?,?)"""
    with get_conn() as conn:
        conn.execute(record_transaction,data)
        conn.commit()
    get_data.clear()


def show_prev_data():
    prev_transaction_dict=st.session_state["prev_transaction"]
    df=pd.DataFrame(prev_transaction_dict.items(),columns=["Field", "Recorded Value"])
    st.write("Previous Recorded Transaction")
    st.dataframe(df,hide_index=True)


def buying_button():
    fields_check=check_fields()
    if fields_check:
        prev_transaction("Buy")
        store_data()
        clear_fields()
        st.session_state["success_msg"]="Transaction Saved Successfully!!!"

@st.cache_data
def get_data():
    with get_conn() as conn:
        df=pd.read_sql_query("SELECT * FROM MF_Transactions",conn)
    df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce")
    return df


def matched_transaction(row,units):
    data={
        "Transaction Id":row["Id"],
        "Date":row["Date"],
        "Units Sold":units,
        "Units Bought":row["Units"],
        "Cost":row["Amount"]
    }
    return data

def get_sale_data(fund_name):
    scheme_name=st.session_state.prev_transaction["Fund Name"]
    portfolio_data_df=get_data()
    fund_data_df=portfolio_data_df[portfolio_data_df["Fund_Name"]==fund_name]
    req_fund_data_df=fund_data_df[fund_data_df["Transaction_Type"]=="Buy"].sort_values("Date")


    units_sold=portfolio_data_df.loc[(portfolio_data_df["Fund_Name"]==scheme_name) &(portfolio_data_df["Transaction_Type"]=="Sell"),"Units"]
    number_of_units_sold_now=st.session_state.prev_transaction["Units"]
    number_of_units_sold_previously=sum(units_sold)-number_of_units_sold_now

    matched_transactions=[]
    for index,row in req_fund_data_df.iterrows():
        if number_of_units_sold_previously>=row["Units"]:
            number_of_units_sold_previously-=row["Units"]
            continue
        elif number_of_units_sold_previously==0:
            if number_of_units_sold_now>=row["Units"]:
                number_of_units_sold_now-=row["Units"]
                matched_transactions.append(matched_transaction(row,row["Units"]))
                if number_of_units_sold_now==0:
                    break
            elif number_of_units_sold_now<row["Units"]:
                matched_transactions.append(matched_transaction(row,number_of_units_sold_now))
                number_of_units_sold_now=0
                break
        elif number_of_units_sold_previously<row["Units"]:
            current_row_units=row["Units"]
            current_row_units-=number_of_units_sold_previously
            number_of_units_sold_previously=0
            matched_transactions.append(matched_transaction(row,current_row_units))
            number_of_units_sold_now-=current_row_units
    return matched_transactions







@st.dialog("Units Sale Analysis")
def show_sell_dialog():

    #Transaction Summary

    st.markdown("<h3>Transaction Summary:</h3>",unsafe_allow_html=True)
    st.write(f'Fund Name: {st.session_state.prev_transaction["Fund Name"]}')
    st.write(f'Units Being Sold: {st.session_state.prev_transaction["Units"]}')
    st.divider()

    #Sale Summary

    st.markdown("<h3>Sale Summary:</h3>",unsafe_allow_html=True)
    st.write(f'Sale Value: ₹{st.session_state.prev_transaction["Amount"]}')
    sale_data=get_sale_data(st.session_state.prev_transaction["Fund Name"])
    purchased_value=0
    for transaction in sale_data:
        units_bought=transaction["Units Bought"]
        cost=transaction["Cost"]
        units_sold=transaction["Units Sold"]
        cost_of_sold_units=units_sold*(cost/units_bought)
        transaction["Cost of Sold Units"]=cost_of_sold_units
        purchased_value+=cost_of_sold_units
    st.write(f'Purchase Cost: ₹{purchased_value:.0f}')
    delta=st.session_state.prev_transaction["Amount"]-purchased_value
    if delta>=0:
        st.write(f'Realized Gain: ₹{delta}')
    elif delta<0:
        neg_delta=-delta
        st.write(f'Realized Loss: ₹{neg_delta}')
    returns=delta/purchased_value*100
    st.write(f'Absolute Return: {returns:.2f}%')
    st.divider()

    #Tax Breakdown

    ltcg=0
    stcg=0
    st.markdown("<h3>Tax Breakdown</h3>",unsafe_allow_html=True)
    #Categorizing Transactions Into long term and short term
    today=datetime.today().date()
    for transaction in sale_data:
        cost_of_sold_units=transaction["Cost of Sold Units"]
        amt=st.session_state.prev_transaction["Amount"]
        total_units_sold=st.session_state.prev_transaction["Units"]
        sale_value_of_units=transaction["Units Sold"]*amt/total_units_sold
        gain=sale_value_of_units-cost_of_sold_units
        
        purchase_date=transaction["Date"]
        purchase_date=purchase_date.date()
        holding_days=(today-purchase_date).days
        if holding_days>365:
            ltcg+=gain
        else:
            stcg+=gain

    ltcg_tax=ltcg*EQUITY_LTCG_TAX_RATE
    stcg_tax=stcg*EQUITY_STCG_TAX_RATE 
    #Printing LTCG Data
    st.write(f'Long Term Capital Gain: ₹{ltcg:.1f}')
    if ltcg>=0:
        st.write(f'LTCG Tax Payable: ₹{ltcg_tax:.1f}')
        st.markdown("<br>",unsafe_allow_html=True)
    else:
        ltcg_tax=0
        st.write(f'LTCG Tax Payable: ₹{ltcg_tax:.1f}')
        st.caption("Your Loss May be eligible for set-off")
        st.markdown("<br>",unsafe_allow_html=True)
    #Printing STCG Data
    st.write(f'Short Term Capital Gain: ₹{stcg:.1f}')
    if stcg>=0:
        st.write(f'STCG Tax Payable: ₹{stcg_tax:.1f}')
    else:
        stcg_tax=0
        st.write(f'STCG Tax Payable: ₹{stcg_tax:.1f}')
        st.caption("Your Loss May be eligible for set-off")
    st.markdown("<br>",unsafe_allow_html=True)
    st.write(f'Total Tax: ₹{ltcg_tax+stcg_tax}')
    st.divider()

    #Lot Breakdown

    st.markdown("<h3>Lot Breakdown:</h3>",unsafe_allow_html=True)
    sale_data["Date"]=sale_data["Date"].dt.date
    st.dataframe(sale_data)
    st.divider()
    
    #Note
    st.caption("Note: This analysis is provided for informational purposes only and should not be considered tax advice.")


def selling_button():
    fields_check=check_fields()
    if fields_check:
        prev_transaction("Sell")
        store_data()
        show_sell_dialog()
        clear_fields()
        st.session_state["success_msg"]="Transaction Saved Successfully!!!"


def all_funds_list(mutual_fund_code):


    #Getting Scheme Name 
    options_list=list(mutual_fund_code.keys())
    options_list.pop(0)
    options_list.insert(0,"Select Mutual Fund Name")
    return options_list


def portfolio_funds_list():
    #Getting Funds List From Portfolio
    portfolio_data_df=get_data()
    options_list=portfolio_data_df["Fund_Name"].unique().tolist()
    options_list.insert(0,"Select Mutual Fund Name")
    return portfolio_data_df,options_list




#---------------------------------------------------------------------------------BODY---------------------------------------------------------------------------------


#Header

st.title("Record Transactions")


#Select Asset 

col1,col2,col3=st.columns([8,10,9])
col1.markdown("<h5>Select Asset Type:</h5>",unsafe_allow_html=True)
asset_type=col2.selectbox("Select Asset Type",options=["Mutual Fund", "Stock","Debt Investments"],label_visibility="collapsed")
st.markdown("---")



if asset_type=="Mutual Fund":

    #Initializing Buying Form

    init_buy_session_state()
    mf=get_mf_tool()
    choice=st.radio(label="",options=["Buy","Sell"],horizontal=True,label_visibility="collapsed",key="choice")
    
    #----–––-----------------------------------------------------------Transaction type is mf buy----–––-----------------------------------------------------------

    if choice=="Buy":
        transaction_date=st.date_input("Transaction Date:",format="DD/MM/YYYY",key="Date")
        
        #Getting Scheme Names And Codes Data
        mutual_code_fund,mutual_fund_code=get_mf_data()

        check=st.checkbox("Portfolio Funds Only",value=True)
        if check:
            portfolio_data_df,options_list=portfolio_funds_list()
        else:
            options_list=all_funds_list(mutual_fund_code)

        scheme_name=st.selectbox("Select Mutual Fund:",options=options_list,key="Fund Name")

        #Displaying Scheme Code After Name is selected
        if scheme_name != "Select Mutual Fund Name" and scheme_name!= "":
            scheme_code=mutual_fund_code[scheme_name]
            st.session_state["scheme code"]=scheme_code
            code_txt="Scheme Code is "+scheme_code
            st.caption(code_txt)

        #Getting Number Units Bought
        units=st.number_input("Number of Units Alloted:",format="%.3f",key="units") #Setting format to allow upto 3 decimals as mf units also operate at 3 decimals
        #Checking if units aren't below 0
        if units<0:
            st.error("Units Must be More than 0")

        #Getting Amount Paid for units
        amount=st.number_input("Amount Debited:",key="amount")
        #Checking if amount isn't below 0
        if amount<0:
            st.error("Amount Must be greater than 0")

        #Showing avg Buying Price 
        if units>0 and amount>0:
            avg=amount/units
            st.caption(f'Average Buying Price is {avg:.3f}')
        
        if "error_msg" in st.session_state:
            st.warning(st.session_state.error_msg)
            del st.session_state["error_msg"]
        if "success_msg" in st.session_state:
            st.success(st.session_state.success_msg)
            del st.session_state["success_msg"]
        submit=st.button("Submit",on_click=buying_button)
        if "prev_transaction" in st.session_state:
            show_prev_data()



    #------------------------------------------------------------------Transaction type is sell------------------------------------------------------------------
    elif choice=="Sell":
        transaction_date=st.date_input("Transaction Date:",format="DD/MM/YYYY",key="Date")

        portfolio_data_df,options_list=portfolio_funds_list()

        scheme_name=st.selectbox("Select Mutual Fund:",options=options_list,key="Fund Name")

        if scheme_name!="" and scheme_name!="Select Mutual Fund Name":

        #Getting Fund code for selected fund
            scheme_code=portfolio_data_df.loc[portfolio_data_df["Fund_Name"]==scheme_name,"Scheme_Code"].iloc[0]
            st.session_state["scheme code"]=scheme_code
            st.caption("Scheme code is: "+scheme_code)

        #Getting Total number of Units held of selected fund
            number_of_units_bought=portfolio_data_df.loc[(portfolio_data_df["Fund_Name"]==scheme_name) & (portfolio_data_df["Date"].dt.date<=transaction_date) & (portfolio_data_df["Transaction_Type"]=="Buy"),"Units"]
            number_of_units_sold=portfolio_data_df.loc[(portfolio_data_df["Fund_Name"]==scheme_name) &(portfolio_data_df["Transaction_Type"]=="Sell"),"Units"]
            total_units=sum(number_of_units_bought)-sum(number_of_units_sold)
            st.caption(f'Total Units Available: {total_units:.3f}')

        #Getting Number of Units Sold
        units=st.number_input("Number of Units Sold:",format="%.3f",key="units") #Setting format to allow upto 3 decimals as mf units also operate at 3 decimals
        
        #Checking if units aren't below 0 or Above Available Units
        if units<0:
            st.error("Units Must be More than 0")
        if scheme_name!="" and scheme_name!="Select Mutual Fund Name":
            if units>total_units:
                st.error("Units Must be Less than Total Units Available")

        #Getting Amount Received for units
        amount=st.number_input("Amount Credited:",key="amount")
        #Checking if amount isn't below 0
        if amount<0:
            st.error("Amount Must be greater than 0")

        #Showing avg Selling Price 
        if units>0 and amount>0:
            avg=amount/units
            st.caption(f'Average Selling Price is {avg:.3f}')

        if "error_msg" in st.session_state:
            st.warning(st.session_state.error_msg)
            del st.session_state["error_msg"]
        if "success_msg" in st.session_state:
            st.success(st.session_state.success_msg)
            del st.session_state["success_msg"]

        submit=st.button("Submit",on_click=selling_button)
        if "prev_transaction" in st.session_state:
            show_prev_data()
        



        

