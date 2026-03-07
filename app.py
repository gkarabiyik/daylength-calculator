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
logging.basicConfig(level=logging.DEBUG)

BASE_URL = "https://www.timeanddate.com/sun/"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot', methods=['POST'])
def plot_day_length():
    data = request.json
    locations = data.get('locations', [])
    year = datetime.datetime.now().year - 1 # Use previous complete year
    
    plt.figure(figsize=(10, 6))
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    data_found = False

    try:
        for loc in locations:
            country = loc['country']
            city = loc['city']
            all_hours = []
            
            for month in range(1, 13):
                url = f'{BASE_URL}{country}/{city}?month={month}&year={year}'
                response = requests.get(url, headers=headers)
                if response.status_code != 200: continue

                soup = BeautifulSoup(response.content, 'html.parser')
                table = soup.find('table', {'id': 'as-monthsun'}) or soup.find('table')

                if table:
                    df = pd.read_html(io.StringIO(str(table)))[0]
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(-1)
                    
                    col_name = next((c for c in df.columns if 'Length' in str(c) or 'Daylength' in str(c)), None)
                    
                    if col_name:
                        # Convert HH:MM:SS to decimal hours
                        df['TempDate'] = pd.to_datetime(df[col_name], format='%H:%M:%S', errors='coerce')
                        df = df.dropna(subset=['TempDate'])
                        hours = (df['TempDate'].dt.hour * 60 + df['TempDate'].dt.minute) / 60
                        all_hours.extend(hours.tolist())

            if all_hours:
                start_date = datetime.datetime(year, 1, 1)
                date_list = [start_date + datetime.timedelta(days=i) for i in range(len(all_hours))]
                plt.plot(date_list, all_hours, label=city.title(), linewidth=2)
                data_found = True

        if not data_found:
            return jsonify({'error': 'No data found.'}), 404

        # Format X-axis to show Months
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        
        plt.ylabel('Hours of Daylight')
        plt.title(f'Daylight Patterns for {year}')
        plt.legend()
        plt.grid(True, linestyle=':', alpha=0.6)
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        plt.close()
        img.seek(0)
        return send_file(img, mimetype='image/png')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
