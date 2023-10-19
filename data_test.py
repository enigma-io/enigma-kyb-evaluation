import requests
import json
import csv
import time
import random
import pandas as pd

BASE_URL = 'https://api.enigma.com/v1/kyb/'
API_KEY = '<YOUR_API_KEY>'
start_time = time.time()

def make_request(row):
    business_name, street_address1, street_address2, city, state, postal_code = row
    data_payload = {
        "data": {
            "names": [business_name],
            "addresses": [{"street_address1": street_address1, "street_address2": street_address2, "city": city, "state": state, "postal_code":postal_code}]
        }
    }

    headers = {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(data_payload))
        response.raise_for_status()
        response_data = response.json()
        num_registrations = count_registrations(response_data)
        return response_data, row, num_registrations
    except requests.RequestException as e:
        error_msg = f"Error making request for {row[0]}, {row[1]}: {e}\n"
        print(error_msg)
        with open(error_log_filename, 'a') as error_file:
            error_file.write(error_msg)
        return None, row, 0

def count_registrations(response_data):
    legal_entities = response_data.get('data', {}).get('legal_entities', [])
    return sum(len(entity.get('registrations', [])) for entity in legal_entities)

def extract_data(response_data, prefix=''):
    flattened_data = {}

    if isinstance(response_data, dict):
        for key, value in response_data.items():
            if key == 'data' and isinstance(value, dict):
                flattened_data.update({f"{prefix}{nested_key}": nested_value for nested_key, nested_value in value.items()})
            elif isinstance(value, dict):
                flattened_data.update(extract_data(value, f"{prefix}{key}_"))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        flattened_data.update({f"{prefix}{key}_{nested_key}_{i}": nested_value for nested_key, nested_value in item.items()})
                    else:
                        flattened_data[f"{prefix}{key}_{i}"] = item
            else:
                flattened_data[f"{prefix}{key}"] = value

    return flattened_data

def write_results_to_csv(rows, results_filename):
    with open(results_filename, 'w', newline='') as results_file:
        results_writer = csv.writer(results_file)
        # Write header
        results_writer.writerow(['Name', 'Street_Address1', 'Street_Address2', 'City', 'State', 'Postal_Code', 'Data'])
        results_file.flush()  # Flush to write the header immediately

        for row in rows:
            response_data, _, _ = make_request(row)
            if response_data:
                extracted_data = extract_data(response_data['data'], 'data_')
                results_writer.writerow([row[0], row[1], row[2], row[3], row[4], row[5], json.dumps(extracted_data)])
                results_file.flush()

        print("\nResults written to CSV successfully.")

def unnest_data_column(results_filename, unnested_filename):
    df = pd.read_csv(results_filename)
    df_data = pd.json_normalize(df['Data'].apply(json.loads))
    df_result = pd.concat([df, df_data], axis=1).drop('Data', axis=1)
    df_result.to_csv(unnested_filename, index=False)
    print(f"\nUnnested results written to {unnested_filename} successfully.")

if __name__ == "__main__":
    filename = 'sample_file.csv'
    results_filename = 'results.csv'
    full_results_filename = 'full_results.json'  # File to store full response data
    error_log_filename = 'errors.log'
    unnested_filename = 'unnested_results.csv'

    lines_processed = 0

    with open(filename, mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        random.shuffle(rows)

        write_results_to_csv(rows, results_filename)
        unnest_data_column(results_filename, unnested_filename)

        end_time = time.time()
        runtime = end_time - start_time

        with open('runtime_stats.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Runtime (seconds)'])
            writer.writerow([runtime])

        print(f"\nScript finished. Total runtime: {runtime:.2f} seconds.")
