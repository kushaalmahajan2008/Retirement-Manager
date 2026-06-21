import streamlit as st

# st.title("Finally retirement app is here")

#Setting Up Pages
dashboard_page=st.Page(
    page="dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
    default=True
)

retirement_page=st.Page(
    title="Retirement Planning",
    page="retirement_planning.py",
    icon="💰"
)

equity_investment_page=st.Page(
    title="Equity Investments",
    page="equity_investments.py",
    icon=":material/finance_mode:"
)

debt_investment_page=st.Page(
    title="Debt Investments",
    page="debt_investments.py",
    icon="💸"
)

transactions_record=st.Page(
    title="Record Transaction",
    page="record_transactions.py",
    icon=":material/add:"
)



transactions_data_page=st.Page(
    title="View All Transaction",
    page="transactions_view.py",
    icon=":material/swap_horiz:"
)

tax_page=st.Page(
    title="Tax Harvesting",
    page="tax.py",
    icon="🏛️"
)

#Grouping Pages
pages={
    "Main":[dashboard_page,retirement_page],
    "Investments":[equity_investment_page,debt_investment_page],
    "Transactions":[transactions_record,transactions_data_page],
    "Tax":[tax_page]
}

#Setting Navigation Sidebar
pg=st.navigation(pages)
pg.run()