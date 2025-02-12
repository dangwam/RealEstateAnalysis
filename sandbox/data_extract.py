import requests
import pandas as pd
import json
import os
from collections import Counter
from datetime import datetime


# List of US states
list_of_states = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]
# API configuration
url = "https://zillow-working-api.p.rapidapi.com/search/byaddress"
headers = {
    "X-RapidAPI-Host": "zillow-working-api.p.rapidapi.com",
    "X-RapidAPI-Key": "8d455c96b8msh3a9f43cf0c88dc4p11cc38jsnc4b82e3c5c66"
}
####################################################################################RentCat API property data ###################################################
#### Rentcat API
# API configuration
prefix = "marketdata"
#zip = 23059
rc_url = "https://api.rentcast.io/v1/markets"
rc_headers = {
    "accept": "application/json",
    "X-Api-Key": "bbf806b0962242c495828a0db2715c00" # your secret key
}

# Function to fetch data from the API
def rc_fetch_data(params=rc_querystring):
    try:
        #response = requests.get(url, headers=headers, params=params)
        response = requests.get(url=rc_url, headers=rc_headers, params=rc_querystring)
        response.raise_for_status()  # HTTPError for bad responses
        data = response.json()
        with open(fname,'w') as f: json.dump(data, f, indent=4)
        print(f"Data successfully fetched and saved to {fname}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON response")
        return None
    except IOError:
        print(f"Error saving data to {fname}")
        return None

# Fetch data
def rc_load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f: return json.load(f)
    else:
        print(f"File {filename} not found.")
        return None

####################################################################################RentCat API property data ###################################################
# Function to fetch data from the API
def fetch_data(params,fname):
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # HTTPError for bad responses
        data = response.json()
        with open(fname,'w') as f: json.dump(data, f, indent=4)
        print(f"Data successfully fetched and saved to {fname}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON response")
        return None
    except IOError:
        print(f"Error saving data to {fname}")
        return None

    

# Fetch data

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f: return json.load(f)
    else:
        print(f"File {filename} not found.")
        return None

def analyze_json_structure(data, prefix=''):
    if isinstance(data, dict):
        return {prefix + k: analyze_json_structure(v, prefix + k + '.') for k, v in data.items()}
    elif isinstance(data, list):
        return {prefix[:-1]: f"List with {len(data)} items"}
    else:
        return {prefix[:-1]: type(data).__name__}

def count_records(data):
    if isinstance(data, list):
        return len(data)
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                return len(value)
    return 1  # If it's a single object

def get_json_info(data):
    structure = analyze_json_structure(data)
    record_count = count_records(data)
    
    print(f"Number of records: {record_count}")
    #print("JSON Structure:")
    #for key, value in structure.items():
     #   print(f"{key}: {value}")
    
    #if isinstance(data, dict):
     #   print("\nTop-level keys:")
      #  for key in data.keys():
       #     print(f"- {key}")





