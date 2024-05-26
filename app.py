import matplotlib
matplotlib.use('Agg')  # Use the Anti-Grain Geometry backend

import requests
from flask import Flask, render_template, request, jsonify, send_file
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import io
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder='templates')

BASE_URL = "https://www.timeanddate.com/sun/"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot', methods=['POST'])
def plot_day_length():
    data = request.json
    countries_cities = data['locations']
    year = data['year']
    
    plt.figure(figsize=(10, 6))
    
    try:
        for location in countries_cities:
            country = location['country']
            city = location['city']
            combined_data = pd.DataFrame()
            
            for month in range(1, 13):
                url = f'{BASE_URL}{country}/{city}?month={month}&year={year}'
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                tables = soup.find_all('table')
                
                # Identify the correct table
                table = None
                for tbl in tables:
                    if 'Daylength' in tbl.get_text():
                        table = tbl
                        break

                if table is None:
                    raise ValueError(f"Day length table not found for {city} in {year}")

                df = pd.read_html(str(table))[0]  # Read the table into a DataFrame
                df['Daylength'] = pd.to_datetime(df['Daylength'], format='%H:%M:%S', errors='coerce')
                df = df.dropna(subset=['Daylength'])
                df['Length'] = (df['Daylength'].dt.hour * 60 + df['Daylength'].dt.minute) / 60
                combined_data = pd.concat([combined_data, df[['Date', 'Length']]], ignore_index=True)
            
            combined_data['Day'] = pd.to_datetime(combined_data['Date']).dt.dayofyear
            plt.plot(combined_data['Day'], combined_data['Length'], label=f'{city}')
        
        plt.xlabel('Day')
        plt.ylabel('Day Length (Total Hours)')
        plt.title('Day Length Comparison')
        plt.legend()
        
        # Save the plot to a BytesIO object
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        
        return send_file(img, mimetype='image/png')
    
    except Exception as e:
        logging.exception("Error generating plot")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
