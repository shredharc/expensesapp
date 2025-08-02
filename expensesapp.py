from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from datetime import date, datetime, timedelta
import mysql.connector
from colorama import Fore, Style, init

init(autoreset=True)

# Connect to MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="P@55w0rd",
    database="expenses"
)
cursor = db.cursor()

def get_suggestions(table, column):
    cursor.execute(f"SELECT DISTINCT {column} FROM {table}")
    return [row[0] for row in cursor.fetchall() if row[0]]

def insert_expense():
    category_suggestions = get_suggestions("category", "name")
    item_suggestions = get_suggestions("item_name", "name")
    store_suggestions = get_suggestions("store_name", "name")
    belongs_to_suggestions = get_suggestions("expense_belongs_to", "name")

    category_completer = WordCompleter(category_suggestions, ignore_case=True)
    item_completer = WordCompleter(item_suggestions, ignore_case=True)
    store_completer = WordCompleter(store_suggestions, ignore_case=True)
    belongs_to_completer = WordCompleter(belongs_to_suggestions, ignore_case=True)

    default_date = str(date.today())
    expense_date = prompt(f"📅 Expense Date (default {default_date}): ") or default_date
    category = prompt("📂 Category: ", completer=category_completer)
    item_name = prompt("🛒 Item Name: ", completer=item_completer)
    store_name = prompt("🏬 Store Name: ", completer=store_completer)
    expense_belongs_to = prompt("👤 Expense Belongs To: ", completer=belongs_to_completer)
    amount = prompt("💰 Amount (₹): ")

    try:
        cursor.execute("""
            INSERT INTO daily_expenses (expense_date, category, item_name, store_name, expense_belongs_to, amount)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (expense_date, category, item_name, store_name, expense_belongs_to, amount))
        db.commit()
        print("\n✅ Expense logged successfully!")
    except Exception as e:
        print(f"\n❌ Error while inserting expense: {e}")

    # Show menu again after insertion
    input("\nPress Enter to return to the main menu...")


def color_row(amount, row_text):
    try:
        amt = float(amount)
        if amt > 1000:
            return Fore.RED + row_text + Style.RESET_ALL
        elif 500 <= amt <= 999:
            return Fore.BLUE + row_text + Style.RESET_ALL
        elif 200 <= amt <= 499:
            return Fore.YELLOW + row_text + Style.RESET_ALL
        else:
            return Fore.GREEN + row_text + Style.RESET_ALL
    except:
        return row_text

def show_weekly_report():
    today = date.today()
    default_year = str(today.year)
    default_month = str(today.month)
    year = prompt(f"Enter year (YYYY) (default {default_year}): ") or default_year
    month = prompt(f"Enter month (1-12) (default {default_month}): ") or default_month

    # Calculate current week of the month for default
    if int(year) == today.year and int(month) == today.month:
        current_day = today.day
    else:
        current_day = 1
    week_of_month = ((current_day - 1) // 7) + 1
    default_week = str(week_of_month)
    week_options = ["1", "2", "3", "4", "5"]
    week_completer = WordCompleter(week_options, ignore_case=True)
    week_num = prompt(f"Enter week of month (1/2/3/4/5) (default {default_week}): ", completer=week_completer) or default_week

    # Default sort by price desc
    sort_choice = prompt("Sort by price? (asc/desc/none, default desc): ") or "desc"
    order_clause = ""
    if sort_choice.lower() == "asc":
        order_clause = "ORDER BY amount ASC"
    elif sort_choice.lower() == "desc" or sort_choice.strip() == "":
        order_clause = "ORDER BY amount DESC"
    else:
        order_clause = "ORDER BY expense_date, store_name, item_name"

    try:
        year = int(year)
        month = int(month)
        week_num = int(week_num)
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()
        start_date = first_day + timedelta(days=(week_num - 1) * 7 - first_weekday if first_weekday < 7 else 0)
        if start_date < first_day:
            start_date = first_day
        end_date = start_date + timedelta(days=6)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        if end_date > last_day:
            end_date = last_day

        query = f"""
            SELECT expense_date, store_name, item_name, amount
            FROM daily_expenses
            WHERE expense_date BETWEEN %s AND %s
            {order_clause}
        """
        cursor.execute(query, (str(start_date), str(end_date)))
        rows = cursor.fetchall()
        print(f"\n📊 Weekly Report ({start_date} to {end_date}):")
        print(f"{'Date':<12} {'Store Name':<20} {'Amount':>10}  {'Item Name':<35} ")
        print("-" * 79)
        for row in rows:
            row_text = f"{str(row[0]):<12} {str(row[1]):<20} {str(row[3]):>10}   {str(row[2]):<35} "
            print(color_row(row[3], row_text))
        print("-" * 79)
        total = sum(float(row[3]) for row in rows)
        print(f"{'Total':<67} {total:>10.2f}")
    except Exception as e:
        print(f"\n❌ Error generating weekly report: {e}")

def show_monthly_report():
    today = date.today()
    default_year = str(today.year)
    default_month = str(today.month)
    year = prompt(f"Enter year (YYYY) (default {default_year}): ") or default_year
    month = prompt(f"Enter month (1-12) (default {default_month}): ") or default_month

    # Default sort by price desc
    sort_choice = prompt("Sort by price? (asc/desc/none, default desc): ") or "desc"
    order_clause = ""
    if sort_choice.lower() == "asc":
        order_clause = "ORDER BY amount ASC"
    elif sort_choice.lower() == "desc" or sort_choice.strip() == "":
        order_clause = "ORDER BY amount DESC"
    else:
        order_clause = "ORDER BY expense_date, store_name, item_name"

    try:
        year = int(year)
        month = int(month)
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        query = f"""
            SELECT expense_date, store_name, item_name, amount
            FROM daily_expenses
            WHERE expense_date BETWEEN %s AND %s
            {order_clause}
        """
        cursor.execute(query, (str(start_date), str(end_date)))
        rows = cursor.fetchall()
        print(f"\n📊 Monthly Report ({start_date} to {end_date}):")
        print(f"{'Date':<12} {'Store Name':<20} {'Amount':>10}  {'Item Name':<35} ")
        print("-" * 79)
        for row in rows:
            row_text = f"{str(row[0]):<12} {str(row[1]):<20} {str(row[3]):>10}   {str(row[2]):<35} "
            print(color_row(row[3], row_text))
        print("-" * 79)
        total = sum(float(row[3]) for row in rows)
        print(f"{'Total':<67} {total:>10.2f}")
    except Exception as e:
        print(f"\n❌ Error generating monthly report: {e}")
        
def main_menu():
    while True:
        print("\nChoose an option:")
        print("1. Insert New Expense")
        print("2. View Reports")
        print("3. Exit")
        choice = prompt("Enter choice (1/2/3): ")
        if choice == "1":
            insert_expense()
        elif choice == "2":
            print("\nReport Options:")
            print("1. Weekly Report")
            print("2. Monthly Report")
            report_choice = prompt("Enter choice (1/2): ")
            if report_choice == "1":
                show_weekly_report()
            elif report_choice == "2":
                show_monthly_report()
            else:
                print("Invalid report option.")
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
    db.close()