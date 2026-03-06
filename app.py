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
    
    # CALCULATE LAST YEAR HERE
    current_year = datetime.datetime.now().year
    year = current_year - 1 
    
    plt.figure(figsize=(10, 6))
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    data_found = False

    try:
        for loc in locations:
            country = loc['country'].strip().lower().replace(" ", "-")
            city = loc['city'].strip().lower().replace(" ", "-")
            all_hours = []
            
            for month in range(1, 13):
                # The 'year' variable here is now (current_year - 1)
                url = f'{BASE_URL}{country}/{city}?month={month}&year={year}'
                response = requests.get(url, headers=headers)
                
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')
                tables = soup.find_all('table')
                
                target_table = None
                for tbl in tables:
                    if 'Daylength' in tbl.get_text() or 'Length' in tbl.get_text():
                        target_table = tbl
                        break

                if target_table:
                    # Fix for Railway OSError
                    df = pd.read_html(io.StringIO(str(target_table)))[0]
                    
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(-1)
                    
                    col_name = None
                    for c in df.columns:
                        if 'Length' in str(c) or 'Daylength' in str(c):
                            col_name = c
                            break
                    
                    if col_name:
                        # Convert HH:MM:SS to decimal hours
                        df['TempDate'] = pd.to_datetime(df[col_name], format='%H:%M:%S', errors='coerce')
                        df = df.dropna(subset=['TempDate'])
                        # Calculation: (Hours * 60 + Minutes) / 60
                        hours = (df['TempDate'].dt.hour * 60 + df['TempDate'].dt.minute) / 60
                        all_hours.extend(hours.tolist())

            if all_hours:
                plt.plot(range(len(all_hours)), all_hours, label=city.title())
                data_found = True

        if not data_found:
            return jsonify({'error': 'No data found. Check city names!'}), 404

        plt.xlabel('Day of Year')
        plt.ylabel('Hours of Daylight')
        plt.title(f'Daylight Comparison (Data from {year})')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        img = io.BytesIO()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        return send_file(img, mimetype='image/png')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
