import os
import io
import matplotlib
matplotlib.use('Agg') 

import requests
from flask import Flask, render_template, request, jsonify, send_file
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

BASE_URL = "https://www.timeanddate.com/sun/"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot', methods=['POST'])
def plot_day_length():
    data = request.json
    locations = data.get('locations', [])
    year = data.get('year', 2024)
    
    plt.figure(figsize=(10, 6))
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        for loc in locations:
            # Fix: Lowercase and replace spaces for URL
            country = loc['country'].strip().lower().replace(" ", "-")
            city = loc['city'].strip().lower().replace(" ", "-")
            combined_data = pd.DataFrame()
            
            for month in range(1, 13):
                url = f'{BASE_URL}{country}/{city}?month={month}&year={year}'
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.content, 'html.parser')
                table = soup.find('table', {'id': 'as-monthsun'})

                if table:
                    # Fix: Use StringIO to prevent OSError
                    html_str = io.StringIO(str(table))
                    df = pd.read_html(html_str)[0]
                    
                    # Target the 'Length' column for daylight hours
                    df.columns = df.columns.get_level_values(-1)
                    if 'Length' in df.columns:
                        df['Daylength'] = pd.to_datetime(df['Length'], format='%H:%M:%S', errors='coerce')
                        df = df.dropna(subset=['Daylength'])
                        df['Hours'] = (df['Daylength'].dt.hour * 60 + df['Daylength'].dt.minute) / 60
                        combined_data = pd.concat([combined_data, df[['Hours']]], ignore_index=True)
            
            if not combined_data.empty:
                plt.plot(combined_data.index, combined_data['Hours'], label=f'{city}')
        
        plt.xlabel('Day of Year')
        plt.ylabel('Hours of Daylight')
        plt.title(f'Day Length Comparison ({year})')
        plt.legend()
        
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        return send_file(img, mimetype='image/png')
    
    except Exception as e:
        logging.exception("Error generating plot")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
