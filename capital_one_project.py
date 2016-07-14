import requests
import json
import pandas as pd
import numpy as np

# Suppresses any false-positive warnings from pandas
pd.options.mode.chained_assignment = None

# Setting the url for the GetAllTransactions endpoint, where we obtain the data.
# We also need to pass headers on how to display data, as well as give the url
# relevant information through data such as the user ID and the session token
url = 'https://prod-api.level-labs.com/api/v2/core/get-all-transactions'
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
data = {'args': {"uid":  1110590645, "token":  "79DA94985E2D213B7114BC4FE3001C34",
                 "api-token":  "AppTokenForInterview", "json-strict-mode": False, "json-verbose-response": False
                }
       }

# Function below ignores donut related transactions if the user tells us they
# want to remove them. We determine if a transaction is donut related by simply
# looking at the transaction's merchant: 'Krispy Kreme Donuts' or 'DUNKIN #336784'
def ignore_donuts(df, remove):
    if remove.lower() == 'yes':
        df = df[[('Krispy Kreme Donuts' or 'DUNKIN #336784') not in merchant for merchant in df.merchant]]
    else:
        pass
    return df

# If called, our Crystal Ball below will return a dataframe consisting of the
# predicted transactions for the current month
def crystal_ball():
    url = 'https://prod-api.level-labs.com/api/v2/core/projected-transactions-for-month'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    data = {'args': {"uid":  1110590645, "token":  "79DA94985E2D213B7114BC4FE3001C34",
                     "api-token":  "AppTokenForInterview", "json-strict-mode": False, "json-verbose-response": False
                    }
           }
    r = requests.post(url, json = data, headers = headers)
    projected_month = r.json()['transactions']

    projected_month_df = pd.DataFrame.from_dict(projected_month)
    return projected_month_df

# If the user wants to remove credit card payments, the function below gets rid
# of them by looking if the merchant is either 'Credit Card Payment' or 'CC Payment'
def ignore_cc_payments(df, remove):
    if remove.lower() == 'yes':
        print "Credit card payments:"
        print df['amount'][[('Credit Card Payment' or 'CC Payment') in merchant for merchant in df.merchant]] / 10000
        df = df[[('Credit Card Payment' or 'CC Payment') not in merchant for merchant in df.merchant]]
    else:
        pass
    return df

# Here we finally get to the meat of our program. Essentially, it grabs data from the
# api we specified above and stores it in a pandas dataframe. Then we transform it
# based on the user's needs and return the transactions grouped by month and whether
# it was an income or expense.
def monthly_expenses(url, data, headers):
    r = requests.post(url, json = data, headers = headers)
    transactions = r.json()['transactions']

    transactions_df = pd.DataFrame.from_dict(transactions)

    # If we want to remove all donut-related transactions, we can enter 'yes', which
    # will call our no_donuts function above
    remove_donuts = raw_input('Remove donut related transactions? Yes or No: ')
    transactions_df = ignore_donuts(transactions_df, remove_donuts).reset_index(drop = True)

    remove_cc = raw_input('Remove credit card payments? Yes or No: ')
    transactions_df = ignore_cc_payments(transactions_df, remove_cc).reset_index(drop = True)

    # If the user says 'yes', we call the crystal_ball function above to predict the
    # transactions for the current month
    look = raw_input('Look into the Crystal Ball (predict income and outcome for this month)? Yes or No: ')
    if look.lower() == 'yes':
        projected_month_df = crystal_ball()
        transactions_df = pd.concat([transactions_df, projected_month_df], axis = 0).reset_index(drop = True)

    # Removing all columns except the relevant ones; the amount of the transaction
    # and the time that transaction took place.
    cols_to_keep = ['amount', 'transaction-time']
    transactions_df = transactions_df[cols_to_keep]

    # We only want the year and month from the transaction-time column, so we're going
    # to reassign each time with the first 7 characters, which just so happen to be the
    # year and month of the transaction
    for i in range(len(transactions_df['transaction-time'])):
        transactions_df['transaction-time'][i] = transactions_df['transaction-time'][i][:7]

    # Since we want to break up the 'amount' column into expenses and income, we
    # need to create two columns (spent and income) based on whether the transaction
    # amount is negative or positive. We also divide by 10000 to convert from centocents 
    # to dollars
    spent = []
    for i in range(len(transactions_df.amount)):
        if transactions_df.amount[i] < 0:
            spent.append(transactions_df.amount[i] / 10000)
        else:
            spent.append(0)
    transactions_df['spent'] = spent

    income = []
    for i in range(len(transactions_df.amount)):
        if transactions_df.amount[i] > 0:
            income.append(transactions_df.amount[i] / 10000)
        else:
            income.append(0)
    transactions_df['income'] = income

    # Simply turning negative values to positive here
    transactions_df.spent = transactions_df.spent.apply(lambda x: x*-1)

    # We need to group the dataframe above by month, so we'll sum both spent transactions
    # and earned transactions and join those two dataframes into one final dataframe
    join1_df = transactions_df.groupby(['transaction-time'])['spent'].sum().reset_index()
    join2_df = transactions_df.groupby(['transaction-time'])['income'].sum().reset_index()
    final_df = pd.merge(join1_df, join2_df, on = 'transaction-time')

    # We calculate the average expense and income across all months below, giving us an
    # idea of what an "average" month looks like for this particular user. 
    average_spent = np.mean(final_df['spent'])
    average_income = np.mean(final_df['income'])

    print "Average money spent per month: ", round(average_spent, 2)
    print "Average money earned per month: ", round(average_income, 2)

    print final_df

monthly_expenses(url, data, headers)
