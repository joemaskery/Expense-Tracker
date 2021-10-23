import PySimpleGUI as sg
import sqlite3
import numpy as np

con = sqlite3.connect('expenses.db')
cur = con.cursor()

headings = ['Date', 'Type', 'Category', 'Amount']
data = []
categories = []
month_number = {}
net_balance = 0

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
months_n = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
for m, n in zip(months, months_n):
    month_number[m] = n

for row in cur.execute("SELECT * from expenses ORDER BY date(Date) DESC"):
    row = list(row)
    data.append(row)
    if row[1] == 'Income':
        net_balance += row[3]
        print('+' + str(row[3]))
    if row[1] == 'Outgoing':
        net_balance -= row[3]
        print('-' + str(row[3]))

net_balance = np.round(net_balance, 2)
net_balance = f'{net_balance:.2f}'
print(net_balance)

for cat in cur.execute("SELECT DISTINCT Category from expenses"):
    cat = ''.join(cat)
    categories.append(cat)


col = [[sg.Text('Enter your expense here:')],
       [sg.Text('Date (YYY-MM-DD):'), sg.Input(key='-DATEIN-'), sg.Text('Expense Type:'),
        sg.InputCombo(('Income', 'Outgoing'), key='-TYPEIN-')],
       [sg.Text('Category (Enter new or select from existing):'), sg.InputCombo(([*categories]), key='-CATIN-'),
        sg.Text('Amount:'), sg.Input(key='-AMOUNTIN-')]
       ]

layout = [[sg.Column(col)],
          [sg.Button('Submit')],
          [sg.Text('Your Expense:'), sg.Text(size=(15, 1), key='-DATEOUTPUT-'), sg.Text(size=(15, 1), key='-TYPEOUTPUT-'),
           sg.Text(size=(15, 1), key='-CATOUTPUT-'), sg.Text(size=(15, 1), key='-AMOUNTOUTPUT-')],
          [sg.InputCombo(('Sort by Date (Most Recent)', 'Sort by Date (Oldest)', 'Sort by Amount (High to Low)',
                         'Sort by Amount (Low to High)', 'Sort by Type', 'Sort by Category'), key='-SORTKEY-',
                         enable_events=True, default_value='Sort by Date (Most Recent)')],
          [sg.Table(values=data, headings=headings, max_col_width=25,
                    auto_size_columns=True,
                    display_row_numbers=True,
                    justification='right',
                    alternating_row_color='black',
                    key='-TABLE-',
                    row_height=35,
                    tooltip='This is a table'),
           sg.Listbox(values=('All', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                              'October', 'November', 'December'), enable_events=True, size=(30, 13), key='-MONTHFILTER-'),
           sg.InputCombo(('Select', 'Past Month', 'Past 2 Months', 'Past 3 Months', 'Past 6 Months', 'All'),
                         key='-PERIODFILTER-', default_value='Select'),
           sg.InputCombo(('Months')), sg.InputCombo(('Years'))],
          [sg.Text('Net Balance:'), sg.Text(net_balance, size=(15, 1), key='-NETBALANCE-')],


          [sg.Button('Exit')]
          ]

window = sg.Window('Expenses', layout)

while True:  # Event Loop
    event, values = window.read()
    print(event, values)
    date_selected = False
    new_net_balance = 0

    if event == sg.WIN_CLOSED or event == 'Exit':
        break

    if event == 'Submit':
        # Update the "output" text element to be the value of "input" element
        window['-DATEOUTPUT-'].update(values['-DATEIN-'])
        date = values['-DATEIN-']
        window['-TYPEOUTPUT-'].update(values['-TYPEIN-'])
        exp_type = values['-TYPEIN-']
        window['-CATOUTPUT-'].update(values['-CATIN-'])
        cat = values['-CATIN-']
        window['-AMOUNTOUTPUT-'].update(values['-AMOUNTIN-'])
        amount = float(values['-AMOUNTIN-'])

        new_expense = [date, exp_type, cat, amount]
        data.append(new_expense)
        window['-TABLE-'].update(values=data)

        cur.execute("insert into expenses values (?, ?, ?, ?)", new_expense)
        con.commit()

        if cat not in categories:
            categories.insert(0, cat)
            window['-CATIN-'].update(values=categories)

    if values['-MONTHFILTER-']:
        selected_month = ''.join(values['-MONTHFILTER-'])
        print(selected_month)
        if selected_month == 'All':
            date_selected = False
        else:
            date_selected = True
            month_filter = month_number[selected_month]

    if values['-SORTKEY-']:
        ordered_data = []
        window['-PERIODFILTER-'].update('Select')
        if values['-SORTKEY-'] == 'Sort by Date (Most Recent)':
            sort_filter = 'date(DATE)'
            direction = 'DESC'

        if values['-SORTKEY-'] == 'Sort by Date (Oldest)':
            sort_filter = 'date(Date)'
            direction = 'ASC'

        if values['-SORTKEY-'] == 'Sort by Amount (High to Low)':
            sort_filter = 'Amount'
            direction = 'DESC'

        if values['-SORTKEY-'] == 'Sort by Amount (Low to High)':
            sort_filter = 'Amount'
            direction = 'ASC'

        if values['-SORTKEY-'] == 'Sort by Type':
            sort_filter = 'Type'
            direction = 'ASC'

        if values['-SORTKEY-'] == 'Sort by Category':
            sort_filter = 'Category'
            direction = 'ASC'

        if date_selected is True:
            for row in cur.execute("SELECT * from expenses WHERE strftime('%m', Date) = '" + month_filter + "' ORDER BY "
                                   + sort_filter + " " + direction):
                row = list(row)
                ordered_data.append(row)
        if date_selected is False:
            for row in cur.execute("SELECT * from expenses ORDER BY " + sort_filter + " " + direction):
                row = list(row)
                ordered_data.append(row)

        for row in ordered_data:
            if row[1] == 'Income':
                new_net_balance += row[3]
                print('+' + str(row[3]))
            if row[1] == 'Outgoing':
                new_net_balance -= row[3]
                print('-' + str(row[3]))

        new_net_balance = np.round(new_net_balance, 2)
        new_net_balance = f'{new_net_balance:.2f}'

        window['-TABLE-'].update(values=ordered_data)
        window['-NETBALANCE-'].update(value=new_net_balance)


window.close()
