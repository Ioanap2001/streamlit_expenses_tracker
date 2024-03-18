import streamlit as st
import sqlite3
from main import FamilyExpenseTracker
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
from pathlib import Path

# Streamlit configuration
st.set_page_config(
    page_title="Transaktionen Tracker",
    page_icon="💰",
    layout="wide"
)
st.title("")  # Clear the default title

# Path Settings
current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
css_file = current_dir / "styles" / "main.css"  # Change this to your desired CSS file

with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

# Create SQLite3 database connection
conn = sqlite3.connect('expense_tracker.db')
cursor = conn.cursor()

# Create tables if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS family_members (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    earning_status BOOLEAN NOT NULL,
                    earnings REAL NOT NULL)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY,
                    category TEXT NOT NULL,
                    description TEXT,
                    value REAL NOT NULL,
                    date DATE NOT NULL)''')

conn.commit()

# Create a session state object
if "expense_tracker" not in st.session_state:
    # If not, create and initialize it
    st.session_state.expense_tracker = FamilyExpenseTracker()

# Center-align the heading using HTML
st.markdown(
    '<h1 style="text-align: center;">Meine Transaktionen- Übersicht</h1>',
    unsafe_allow_html=True,
)

# Navigation Menu
selected = option_menu(
    menu_title=None,
    options=["Data Entry", "Data Overview", "Data Visualization"],
    icons=[
        "pencil-fill",
        "clipboard2-data",
        "bar-chart-fill",
    ],  # https://icons.getbootstrap.com/
    orientation="horizontal",
)

# Access the 'expense_tracker' object from session state
expense_tracker = st.session_state.expense_tracker

if selected == "Data Entry":
    st.header("Einnahmen erfassen")
    with st.expander("Details"):
        # Sidebar for adding family members
        member_name = st.text_input("Name").title()
        earning_status = st.checkbox("Einkommen")
        if earning_status:
            earnings = st.number_input("Earnings", value=1, min_value=1)
        else:
            earnings = 0

        if st.button("Add Member"):
            try:
                # Add family member to the database
                cursor.execute('''INSERT INTO family_members (name, earning_status, earnings) 
                                  VALUES (?, ?, ?)''', (member_name, earning_status, earnings))
                conn.commit()
                st.success("Mitglied erfolgreich hinzugefügt!")
            except sqlite3.Error as e:
                st.error(str(e))

    # Sidebar for adding expenses
    st.header("Ausgaben erfassen")
    with st.expander("Ausgaben hinzufügen"):
        expense_category = st.selectbox(
            "Kategorie",
            (
                "Housing",
                "Food",
                "Transportation",
                "Entertainment",
                "Child-Related",
                "Medical",
                "Investment",
                "Miscellaneous",
            ),
        )
        expense_description = st.text_input("Beschriebung(optional)").title()
        expense_value = st.number_input("Betrag", min_value=0)
        expense_date = st.date_input("Datum", value="today")

        if st.button("Bestätigen"):
            try:
                # Add expense to the database
                cursor.execute('''INSERT INTO expenses (category, description, value, date) 
                                  VALUES (?, ?, ?, ?)''', (expense_category, expense_description, expense_value, expense_date))
                conn.commit()
                st.success("Ausgabe erfolgreich hinzugefügt!")
            except sqlite3.Error as e:
                st.error(str(e))
elif selected == "Data Overview":
    # Display family members
    cursor.execute('''SELECT * FROM family_members''')
    members = cursor.fetchall()
    if not members:
        st.info(
            "Start by adding family members to track your expenses together! Currently, no members have been added. Get started by clicking the 'Add Member' from the Data Entry Tab"
        )
    else:
        st.header("Family Members")
        (
            name_column,
            earning_status_column,
            earnings_column,
            family_delete_column,
        ) = st.columns(4)
        name_column.write("**Name**")
        earning_status_column.write("**Earning status**")
        earnings_column.write("**Earnings**")
        family_delete_column.write("**Action**")

        for member in members:
            name_column.write(member[1])
            earning_status_column.write(
                "Earning" if member[2] else "Not Earning"
            )
            earnings_column.write(member[3])

            if family_delete_column.button(f"Delete {member[1]}"):
                cursor.execute('''DELETE FROM family_members WHERE id = ?''', (member[0],))
                conn.commit()
                st.experimental_rerun()  # Rerun the app

        # Display expenses
        cursor.execute('''SELECT * FROM expenses''')
        expenses = cursor.fetchall()
        st.header("Expenses")
        if not expenses:
            st.info(
            "Currently, no expenses have been added. Get started by clicking the 'Add Expenses' from the Data Entry Tab"
        )
        else:
            (
                value_column,
                category_column,
                description_column,
                date_column,
                expense_delete_column,
            ) = st.columns(5)
            value_column.write("**Value**")
            category_column.write("**Category**")
            description_column.write("**Description**")
            date_column.write("**Date**")
            expense_delete_column.write("**Delete**")

            for expense in expenses:
                value_column.write(expense[3])
                category_column.write(expense[1])
                description_column.write(expense[2])
                date_column.write(expense[4])

                if expense_delete_column.button(f"Delete {expense[1]}"):
                    cursor.execute('''DELETE FROM expenses WHERE id = ?''', (expense[0],))
                    conn.commit()
                    st.experimental_rerun()  # Rerun the app

        # Calculate total earnings
        cursor.execute('''SELECT SUM(earnings) FROM family_members''')
        total_earnings = cursor.fetchone()[0] or 0
        # Calculate total expenditure
        cursor.execute('''SELECT SUM(value) FROM expenses''')
        total_expenditure = cursor.fetchone()[0] or 0
        remaining_balance = total_earnings - total_expenditure
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Earnings", f"{total_earnings}")          # Display total earnings
        col2.metric("Total Expenditure", f"{total_expenditure}")    # Display total expenditure 
        col3.metric("Remaining Balance", f"{remaining_balance}")    # Display remaining balance 

elif selected == "Data Visualization":
    # Create a list of expenses and their values
    cursor.execute('''SELECT category, value FROM expenses''')
    expense_data = cursor.fetchall()
    if expense_data:
        # Calculate the percentage of expenses for the pie chart
        expenses = [data[0] for data in expense_data]
        values = [data[1] for data in expense_data]
        total = sum(values)
        percentages = [(value / total) * 100 for value in values]

        # Create a smaller pie chart with a transparent background
        fig, ax = plt.subplots(figsize=(2, 2), dpi=200)
        ax.pie(
            percentages,
            labels=expenses,
            autopct="%1.1f%%",
            startangle=140,
            textprops={"fontsize": 6, "color": "white"},
        )
        ax.set_title("Expense Distribution", fontsize=10, color="white")

        # Set the background color to be transparent
        fig.patch.set_facecolor("none")

        # Display the pie chart in Streamlit
        st.pyplot(fig)
    else:
        st.info(
            "Start by adding family members to track your expenses together! Currently, no members have been added. Get started by clicking the 'Add Member' from the Data Entry Tab."
        )

# Close SQLite3 database connection
conn.close()
