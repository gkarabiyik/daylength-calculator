import pandas as pd
import json
import re

with open("country-states.js", "r") as f:
    content = f.read()
    # This regex finds the first '[' or '{' and takes everything until the last ']' or '}'
    json_data = re.search(r'([\[\{].*[\]\}])', content, re.DOTALL).group(0)
    
df = pd.read_json(json_data)
df_cities= pd.read_json("cities.json")



# 1. Create a simple mapping of Code -> Country Name from the first DataFrame
# (Assuming index or a column named 'AF', 'AL', etc. is available)
# If your first DF has the index as 'AF', 'AL', we use:
country_map = df['country'].to_dict()

# 2. Add a 'country_name' column to your cities DataFrame using the map
df_cities['country_full_name'] = df_cities['country'].map(country_map)

# 3. Clean up the city names (Optional: remove "Province" or "Governorate" if they appear)
# This addresses your concern about "Adana Province"
df_cities['name'] = df_cities['name'].str.replace(' Province', '', case=False)
df_cities['name'] = df_cities['name'].str.replace(' Governorate', '', case=False)

# 4. Group by Country and create a list of cities
# We filter out any NaN values just in case a code didn't match
result = df_cities.groupby('country_full_name')['name'].apply(list).to_dict()

# # 5. Save as a clean JSON for your web app
# with open('app_cities.json', 'w', encoding='utf-8') as f:
#     json.dump(result, f, indent=4, ensure_ascii=False)

# print("Created app_cities.json with", len(result), "countries.")