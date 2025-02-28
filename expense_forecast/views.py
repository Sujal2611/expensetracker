from django.shortcuts import render
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from django.utils.timezone import now
from expenses.models import Expense
from django.contrib import messages
import matplotlib.pyplot as plt
from django.contrib.auth.decorators import login_required

@login_required(login_url='/authentication/login')
def forecast(request):
    expenses = Expense.objects.filter(owner=request.user).order_by('-date')[:30]

    # Check if there are enough expenses
    if len(expenses) < 10:
        messages.error(request, "Not enough expenses to make a forecast.")
        return render(request, 'expense_forecast/index.html')

    # Create DataFrame
    data = pd.DataFrame({
        'Date': [expense.date for expense in expenses], 
        'Expenses': [expense.amount for expense in expenses], 
        'Category': [expense.category for expense in expenses]
    })
    data.set_index('Date', inplace=True)

    # Debugging: Print DataFrame info
    print("\n==== DataFrame Info ====")
    print(data.info())
    print("\n==== Data Preview ====")
    print(data.head())

    # Ensure Expenses column is numeric
    if 'Expenses' in data.columns:
        data['Expenses'] = pd.to_numeric(data['Expenses'], errors='coerce')

    # **FIX: Handle Empty DataFrame Before Grouping**
    if data.empty:
        print("⚠️ Warning: DataFrame is empty, skipping forecast.")
        messages.error(request, "No valid expense data available for forecasting.")
        return render(request, 'expense_forecast/index.html')

    # **FIX: Ensure Category Column Exists**
    if 'Category' not in data.columns:
        print("⚠️ Warning: 'Category' column missing.")
        messages.error(request, "Expense categories are missing in your data.")
        return render(request, 'expense_forecast/index.html')

    # **FIX: Use .groupby() Correctly**
    category_forecasts = {}
    if not data['Category'].isnull().all():
        category_forecasts = data.groupby('Category')['Expenses'].sum().to_dict()
    else:
        print("⚠️ Warning: All 'Category' values are NaN.")

    print("\n==== Category Forecasts ====")
    print(category_forecasts)

    # Fit ARIMA model
    try:
        model = ARIMA(data['Expenses'], order=(5, 1, 0))
        model_fit = model.fit()
    except Exception as e:
        print(f"❌ ARIMA Model Error: {e}")
        messages.error(request, "Error in forecasting model.")
        return render(request, 'expense_forecast/index.html')

    # Forecast next 30 days
    forecast_steps = 30
    forecast = model_fit.forecast(steps=forecast_steps)
    forecast_index = pd.date_range(start=now().date() + pd.DateOffset(days=1), periods=forecast_steps, freq='D')

    forecast_data = pd.DataFrame({'Date': forecast_index, 'Forecasted_Expenses': forecast})
    total_forecasted_expenses = np.sum(forecast)

    # Save forecast plot
    plt.figure(figsize=(10, 6))
    plt.plot(data.index, data['Expenses'], label='Previous Expenses')
    plt.plot(forecast_index, forecast, label='Forecasted Expenses', color='red')
    plt.xlabel('Date')
    plt.ylabel('Expenses')
    plt.title('Expense Forecast for Next 30 Days')
    plt.legend()
    plot_file = 'static/img/forecast_plot.png'
    plt.savefig(plot_file)
    plt.close()

    context = {
        'forecast_data': forecast_data.to_dict(orient='records'),
        'total_forecasted_expenses': total_forecasted_expenses,
        'category_forecasts': category_forecasts,
        'plot_file': plot_file
    }

    return render(request, 'expense_forecast/index.html', context)
