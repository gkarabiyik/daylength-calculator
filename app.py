import os
import io
import datetime
import matplotlib
matplotlib.use('Agg') 

import requests
from flask import Flask, render_template, request, jsonify, send_file
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import logging

app = Flask(__name__)

BASE_URL = "https://www.timeanddate.com/sun/"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot', methods=['POST'])
def plot_day_length():
    data = request.json
    locations = data.get('locations', [])
    
    # Always use the current year
    year = datetime.datetime.now().year
    
    plt.figure(figsize=(12, 6))
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        for loc in locations:
            country = loc['country']
            city = loc['city']
            combined_data = []
            
            # Scrape 12 months
            for month in range(1, 13):
                url = f'{BASE_URL}{country}/{city}?month={month}&year={year}'
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.content, 'html.parser')
                table = soup.find('table', {'id': 'as-monthsun'})

                if table:
                    html_str = io.StringIO(str(table))
                    df = pd.read_html(html_str)[0]
                    df.columns = df.columns.get_level_values(-1)
                    
                    if 'Length' in df.columns:
                        # Convert to timedeltas then to float hours
                        df['Daylength'] = pd.to_timedelta(df['Length'] + ':00', errors='coerce')
                        df = df.dropna(subset=['Daylength'])
                        df['Hours'] = df['Daylength'].dt.total_seconds() / 3600
                        combined_data.extend(df['Hours'].tolist())
            
            if combined_data:
                # Create a date range for the X-axis to show Months
                dates = pd.date_range(start=f"{year}-01-01", periods=len(combined_data))
                plt.plot(dates, combined_data, label=f'{city.replace("-", " ").title()}')

        # Formatting the X-Axis to show Month Names
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        
        plt.xlabel('Month')
        plt.ylabel('Hours of Daylight')
        plt.title(f'Daylight Patterns for {year}')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        return send_file(img, mimetype='image/png')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
