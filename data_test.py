import requests
import json
import csv
import time
import pandas as pd
import argparse

BASE_URL = 'https://api.enigma.com/v1/kyb/?package=kyb_with_tin'
API_KEY = '<YOUR_API_KEY>'
start_time = time.time()


def make_request(row, tin_flag):
    if tin_flag == 'y':
        input_name, input_street_address1, input_street_address2, input_city, input_state, input_postal_code, input_tin = row
    else:
        input_name, input_street_address1, input_street_address2, input_city, input_state, input_postal_code = row
    data_payload = {
        "data": {
            "names": [input_name],
            "addresses": [{"street_address1": input_street_address1, "street_address2": input_street_address2,
                           "city": input_city, "state": input_state, "postal_code": input_postal_code}]
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


def make_tin_request(row):
    if 'input_business_name_2' in row.index and not pd.isna(row["input_business_name_2"]):
        name = [row["input_business_name"] + ", " + row["input_business_name_2"]]
    else:
        name = [row['input_business_name']]
    for col in row.index:
        if pd.isna(row[col]):
            row[col] = ""
    data_payload = {
        "data": {"names": name,
                 "addresses": [{
                     "street_address1": str(row["input_street_address1"]),
                     "street_address2": str(row["input_street_address2"]),
                     "city": str(row["input_city"]),
                     "state": str(row["input_state"]),
                     "postal_code": str(row["input_postal_code"])
                 }],
                 "tins": [str(row["input_tin"])]
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

        return response_data
    except requests.RequestException as e:
        error_msg = f"Error making request for {row[0]}, {row[1]}: {e}\n"
        with open(error_log_filename, 'a') as error_file:
            error_file.write(error_msg)
        return None


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


def write_results_to_csv(rows, results_filename, tin_flag):
    with open(results_filename, 'w', newline='') as results_file:
        results_writer = csv.writer(results_file)
        # Write header
        if tin_flag == 'y':
            results_writer.writerow(['input_business_name', 'input_street_address1', 'input_street_address2',
                                     'input_city', 'input_state', 'input_postal_code', 'input_tin', 'Data'])
        else:
            results_writer.writerow(
                ['input_business_name', 'input_street_address1', 'input_street_address2', 'input_city', 'input_state',
                 'input_postal_code', 'Data'])
        results_file.flush()  # Flush to write the header immediately

        for row in rows:
            response_data, _, _ = make_request(row, tin_flag)
            if response_data:
                extracted_data = extract_data(response_data['data'], 'data_')
                if tin_flag == 'y':
                    results_writer.writerow(
                        [row[0], row[1], row[2], row[3], row[4], row[5], row[6], json.dumps(extracted_data)])
                else:
                    results_writer.writerow([row[0], row[1], row[2], row[3], row[4], row[5],
                                             json.dumps(extracted_data)])
                results_file.flush()

        print("\nResults written to CSV successfully.")


def unnest_data_column(results_filename, unnested_filename):
    df = pd.read_csv(results_filename)
    df_data = pd.json_normalize(df['Data'].apply(json.loads))
    df_result = pd.concat([df, df_data], axis=1).drop('Data', axis=1)
    df_result.to_csv(unnested_filename, index=False)
    print(f"\nUnnested results written to {unnested_filename} successfully.")


def extract_tin(row):
    if row is not None:
        for item in row:
            if item['task_name'] == 'tin_verification':
                return item
    return None


def tin_pull(input_file, tin_file_name, max_calls=100):
    input_df = pd.read_csv(input_file, header=0)
    request_df = input_df.head(max_calls)
    request_df['response'] = request_df.apply((lambda r: make_tin_request(r)), axis=1)
    request_df['tasks'] = request_df.apply(
        lambda r: r['response']['risk_summary']['tasks'] if r['response'] is not None else None, axis=1)
    request_df.to_csv('test.csv')
    task_df = request_df['tasks'].apply(extract_tin)
    df_tin = pd.json_normalize(task_df)
    df_tin.rename(columns={"status": "task_status", "result": "task_result", "reason": "task_reason"}, inplace=True)
    df_tin['task_name'] = df_tin['task_name'].fillna('tin_verification')
    df_tin['task_status'] = df_tin['task_status'].fillna('error with input')
    df_result = pd.concat([input_df, df_tin], axis=1)
    position = df_result.columns.get_loc('input_tin') + 1
    df_result.insert(position, 'task_name', df_result.pop('task_name'))
    df_result.insert(position + 1, 'task_status', df_result.pop('task_status'))
    df_result.insert(position + 2, 'task_result', df_result.pop('task_result'))
    df_result.insert(position + 3, 'task_reason', df_result.pop('task_reason'))
    df_result.to_csv(tin_file_name, index=False)
    print(f"\n Tin results written to {tin_file_name} successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-t', '--tin_flag', type=str, help='Whether you want to query the KYB api or just grab tin. '
                                                           'Should be y if you want tin, n if you only want KYB',
                        default="y")
    # BELOW LINE IS FOR INTERNAL ENIGMA USE ONLY
    parser.add_argument('-d', '--dds_output_flag', type=str, help='Whether this is a dds output or not',
                        default="n")

    args = parser.parse_args()
    dds_output_flag = args.dds_output_flag
    tin_flag = args.tin_flag
    if tin_flag == 'y':
        filename = 'sample_file_tin.csv'
    elif tin_flag == 'n':
        filename = 'sample_file.csv'
    results_filename = 'results.csv'
    full_results_filename = 'full_results.json'  # File to store full response data
    error_log_filename = 'errors.log'
    unnested_filename = 'unnested_results.csv'
    tin_file_name = 'tin_results.csv'
    lines_processed = 0

    with open(filename, mode='r') as file:
        reader = csv.reader(file)
        next(reader)
        rows = list(reader)
        if dds_output_flag == 'n':
            write_results_to_csv(rows, results_filename, tin_flag)
            unnest_data_column(results_filename, unnested_filename)
            if tin_flag == 'y':
                tin_pull(unnested_filename, tin_file_name, 100)
        elif dds_output_flag == 'y':
            tin_pull(filename, tin_file_name, 100)
        end_time = time.time()
        runtime = end_time - start_time

    with open('runtime_stats.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Runtime (seconds)'])
        writer.writerow([runtime])

        print(f"\nScript finished. Total runtime: {runtime:.2f} seconds.")
