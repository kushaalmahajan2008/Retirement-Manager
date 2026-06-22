import streamlit as st
import pandas as pd
from mftool import Mftool
from datetime import datetime
import sqlite3


#----------------------------------------------------------Functions----------------------------------------------------------

def init_buy_session_state():
    if "Fund Name" not in st.session_state:
        st.session_state["Fund Name"]=""
    if "units" not in st.session_state:
        st.session_state["units"]=0
    if "amount" not in st.session_state:
        st.session_state["amount"]=0


def check_fields():
    if st.session_state["Fund Name"]=="" or st.session_state["Fund Name"]=="Select Mutual Fund Name":
        st.session_state["error_msg"]=("Please Select A mutual fund")
        return False
    elif st.session_state["units"]==0:
        st.session_state["error_msg"]=("Please Enter Units")
        return False
    elif st.session_state["amount"]==0:
        st.session_state["error_msg"]=("Please Enter Amount")
        return False
    else:
        return True
    
    
def clear_fields():
    st.session_state["Date"]=datetime.now().date()
    st.session_state["Fund Name"]=""
    st.session_state["units"]=0
    st.session_state["amount"]=0


def prev_transaction(choice):
    units=st.session_state["units"]
    amount=st.session_state["amount"]
    avg=amount/units
    prev_buy_transaction_data={
        "Choice":choice,
        "Date":st.session_state["Date"],
        "Fund Name":st.session_state["Fund Name"],
        "Scheme Code":scheme_code,
        "Units":units,
        "Amount":amount,
        "Average Buying Price":f'{avg:.3f}'
    }
    st.session_state["prev_transaction"]=prev_buy_transaction_data


def store_data():
    data=(st.session_state["Date"],st.session_state["choice"],st.session_state["Fund Name"],scheme_code,st.session_state["units"],st.session_state["amount"])
    record_transaction="""INSERT INTO MF_Transactions
    (Date,Transaction_Type,Fund_Name,Scheme_Code,Units,Amount)
    VALUES(?,?,?,?,?,?)"""
    with sqlite3.Connection("retirement_manager.db") as conn:
        conn.execute(record_transaction,data)
        conn.commit()


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


def get_data():
    with sqlite3.connect("retirement_manager.db") as conn:
        df=pd.read_sql_query("SELECT * FROM MF_Transactions",conn)
    df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce")
    return df


def selling_button():
    fields_check=check_fields()
    if fields_check:
        prev_transaction("Sell")
        store_data()
        clear_fields()
        st.session_state["success_msg"]="Transaction Saved Successfully!!!"




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
    mf=Mftool()
    choice=st.radio(label="",options=["Buy","Sell"],horizontal=True,label_visibility="collapsed",key="choice")
    
    #----–––-----------------------------------------------------------Transaction type is mf buy----–––-----------------------------------------------------------

    if choice=="Buy":
        transaction_date=st.date_input("Transaction Date:",format="DD/MM/YYYY",key="Date")
        
        #Getting Scheme Names And Codes Data
        mutual_code_fund=mf.get_scheme_codes()
        mutual_fund_code = {
            name: code
            for code, name in mutual_code_fund.items()
        }

        #Getting Scheme Name 
        options_list=list(mutual_fund_code.keys())
        options_list.pop(0)
        options_list.insert(0,"Select Mutual Fund Name")
        scheme_name=st.selectbox("Select Mutual Fund:",options=options_list,key="Fund Name")

        #Displaying Scheme Code After Name is selected
        if scheme_name != "Select Mutual Fund Name" and scheme_name!= "":
            scheme_code=mutual_fund_code[scheme_name]
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

        #Getting Funds List From Portfolio
        portfolio_data_df=get_data()
        options_list=portfolio_data_df["Fund_Name"].unique().tolist()
        options_list.insert(0,"Select Mutual Fund Name")
        scheme_name=st.selectbox("Select Mutual Fund:",options=options_list,key="Fund Name")

        if scheme_name!="" and scheme_name!="Select Mutual Fund Name":

        #Getting Fund code for selected fund
            scheme_code=portfolio_data_df.loc[portfolio_data_df["Fund_Name"]==scheme_name,"Scheme_Code"].iloc[0]
            st.caption("Scheme code is: "+scheme_code)

        #Getting Total number of Units held of selected fund
            today = pd.Timestamp.today()
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
            st.caption(f'Average Buying Price is {avg:.3f}')

        if "error_msg" in st.session_state:
            st.warning(st.session_state.error_msg)
            del st.session_state["error_msg"]
        if "success_msg" in st.session_state:
            st.success(st.session_state.success_msg)
            del st.session_state["success_msg"]

        submit=st.button("Submit",on_click=selling_button)
        if "prev_transaction" in st.session_state:
            show_prev_data()
        



        

