# enigma-kyb-evaluation
## Enigma KYB Self-Serve Evaluation Guide
This contains the python script and sample file for running a self-serve KYB evaluation on Enigma's KYB endpoint. For further instructions, please refer to the [docs site](https://developers.enigma.com/docs/kyb-evaluation-guide).

## Instructions
1. This package contains 2 files:
   1. `sample_file.csv` : This is the test asset we’ll be running an evaluation on. Here’s a snapshot of the data.
   2. `data_test.py` : This is a Python script to run the inputs from `sample_file.csv` through Enigma’s KYB endpoint and generate a results file: `unnested_results.csv`.
2. Open `data_test.py`. In line 9, paste your API key. This is the same key from your Console dashboard (see “Create a Console Account” section).

   1. ```
      import requests
      import json
      import csv
      import time
      import random
      import pandas as pd

      BASE_URL = 'https://api.enigma.com/v1/kyb/'
      API_KEY = '<YOUR_API_KEY>'
      start_time = time.time()
      ```
3. If necessary, don’t forget to install dependencies specified in the file (eg, pandas).
4. Run the script. Once this script has successfully run it will produce a CSV file with the endpoint responses in the root directory called `unnested_results.csv`.
