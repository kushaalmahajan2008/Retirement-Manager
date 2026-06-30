import streamlit as st

# st.title("Finally retirement app is here")

#Setting Up Pages
dashboard_page=st.Page(
    page="pages/dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
    default=True
)

retirement_page=st.Page(
    title="Retirement Planning",
    page="pages/retirement_planning.py",
    icon="💰"
)

equity_investment_page=st.Page(
    title="Equity Portfolio",
    page="pages/equity_investments.py",
    icon=":material/finance_mode:"
)

debt_investment_page=st.Page(
    title="Debt Portfolio",
    page="pages/debt_investments.py",
    icon="💸"
)

transactions_record=st.Page(
    title="Record Transaction",
    page="pages/record_transactions.py",
    icon=":material/add:"
)



transactions_data_page=st.Page(
    title="View All Transaction",
    page="pages/transactions_view.py",
    icon=":material/swap_horiz:"
)

tax_page=st.Page(
    title="Tax Harvesting",
    page="pages/tax.py",
    icon="🏛️"
)

fund_details=st.Page(
    page="pages/fund_details.py",
    title="Details"
)

#Grouping Pages
all_pages=dashboard_page,retirement_page,equity_investment_page,debt_investment_page,transactions_record,transactions_data_page,tax_page,fund_details
pg = st.navigation(all_pages, position="hidden")

with st.sidebar:
    st.subheader("Main")
    st.page_link(dashboard_page, label="Dashboard", icon=":material/dashboard:")
    st.page_link(retirement_page, label="Retirement Planning", icon="💰")

    st.subheader("Investments")
    st.page_link(equity_investment_page, label="Equity Portfolio", icon=":material/finance_mode:")
    st.page_link(debt_investment_page, label="Debt Portfolio", icon="💸")

    st.subheader("Transactions")
    st.page_link(transactions_record, label="Record Transaction", icon=":material/add:")
    st.page_link(transactions_data_page, label="View All Transaction", icon=":material/swap_horiz:")

    st.subheader("Tax")
    st.page_link(tax_page, label="Tax Harvesting", icon="🏛️")

    st.space(50)
    st.write("Made with ❤️ By Kushaal Mahajan")

pg.run()