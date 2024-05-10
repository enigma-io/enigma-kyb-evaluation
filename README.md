# enigma-kyb-evaluation
## Enigma KYB Self-Serve Evaluation Guide
This contains the python script and sample file for running a self-serve KYB evaluation on Enigma's KYB endpoint. For further instructions, please refer to the [docs site](https://developers.enigma.com/docs/kyb-evaluation-guide).

## Instructions
1. This package contains 3 files:
   1. `sample_file.csv` : This is the test asset we’ll be running an evaluation on. 
   2. `sample_file_tin.csv` : This is the test asset we’ll be running a TIN evaluation on. Please note that the TINS in this file are invalid.
   3. `data_test.py` : This is a Python script to run the inputs from `sample_file.csv` or `sample_fil_tin.csv` through Enigma’s KYB endpoint and generate the results files: `unnested_results.csv` and `tin_results.csv`.
2. Open `data_test.py`. In line 9, paste your API key. This is the same key from your Console dashboard (see [“Create a Console Account” section](https://developers.enigma.com/docs/kyb-evaluation-guide#create-a-console-account)).

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
4. If you'd like to enrich your file with tin, you can run the code as is. However, if you don't want TIN, then you can either call the script via command line and append "-t n" to the end so the command would be `data_test.py -t n`. You can also manually set the value to "n" within the script on line 185 like so
   1. ```
       tin_flag = "n"
      ```
5. Run the script. Once this script has successfully run it will produce a CSV file with the endpoint responses in the root directory called `unnested_results.csv`. If you set tin flag to "y" a file called `tin_results.csv` will contain the TIN results.

## Results
To learn more about output results, please visit the [results section of the KYB self-serve evaluation documentation](https://developers.enigma.com/docs/kyb-evaluation-guide#output-results).