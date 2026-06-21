import streamlit as st
import pandas as pd
from mftool import Mftool
import sqlite3

def record_mf_transaction(transaction_date,choice,scheme_name,scheme_code,units,amount):
    data=(transaction_date,choice,scheme_name,scheme_code,units,amount)
    record_transaction="""INSERT INTO MF_Transactions
    (Date,Transaction_Type,Fund_Name,Scheme_Code,Units,Amount)
    VALUES(?,?,?,?,?,?)"""
    with sqlite3.Connection("retirement_manager.db") as conn:
        conn.execute(record_transaction,data)
        conn.commit()

st.title("Record Equity Transactions")

# st.markdown("<br>",unsafe_allow_html=True)
col1,col2,col3=st.columns([8,10,9])
col1.markdown("<h5>Select Asset Type:</h5>",unsafe_allow_html=True)
asset_type=col2.selectbox("Select Asset Type",options=["Mutual Fund", "Stock","Debt Investments"],label_visibility="collapsed")
st.markdown("---")


#------------------------------------------------------------------Form for Mutual fund Transaction------------------------------------------------------------------
if asset_type=="Mutual Fund":
    with st.form("Mutual_fund",clear_on_submit=True):
        mf=Mftool()
        choice=st.radio(label="",options=["Buy","Sell"],horizontal=True,label_visibility="collapsed")
        transaction_date=st.date_input("Transaction Date:",format="DD/MM/YYYY")

        #Getting Scheme And Codes Data
        mutual_code_fund=mf.get_scheme_codes()
        mutual_fund_code = {
            name: code
            for code, name in mutual_code_fund.items()
        }

        #Getting User Inputs
        scheme_name=st.selectbox("Select Mutual Fund:",options=list(mutual_fund_code.keys()))
        units=st.number_input("Number of Units Alloted:",format="%.3f") #Setting format to allow upto 3 decimals as mf units also operate at 3 decimals
        amount=st.number_input("Amount Credited/Debited:")
        

        #Submit Button Logic
        submit=st.form_submit_button("Submit")
        if submit:
            if scheme_name=="Scheme Name":
                st.warning("Please Select A Mutual Fund")
            elif units<=0:
                st.warning("Please Enter Number of Units Credited/Debited")
            elif amount<=0:
                st.warning("Please Enter Money Credited/Debited")
            else:
                scheme_code=mutual_fund_code[scheme_name]
                record_mf_transaction(transaction_date,choice,scheme_name,scheme_code,units,amount)
                st.success("Your Transaction Has Been Recorded")
                data={
                    "Type":choice,
                    "Date of Transaction":transaction_date,
                    "Scheme Name":scheme_name,
                    "Scheme Code":scheme_code,
                    "Units":units,
                    "Amount":amount,
                    "Average Buying Cost":amount/units

                }
                st.dataframe(data)


#------------------------------------------------------------------Form for Debt Investment Transaction------------------------------------------------------------------

elif asset_type=="Debt Ivestments":
    pass