import streamlit as st
import pandas as pd
from mftool import Mftool

st.title("Record Equity Transactions")

# st.markdown("<br>",unsafe_allow_html=True)
col1,col2,col3=st.columns([8,10,9])
col1.markdown("<h5>Select Asset Type:</h5>",unsafe_allow_html=True)
asset_type=col2.selectbox("Select Asset Type",options=["Mutual Fund", "Stock"],label_visibility="collapsed")
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
                data={
                    "Type":choice,
                    "Date of Transaction":transaction_date,
                    "Scheme Name":scheme_name,
                    "Scheme Code":mutual_fund_code[scheme_name],
                    "Units":units,
                    "Amount":amount,
                    "Average Buying Cost":amount/units

                }
                st.dataframe(data)

