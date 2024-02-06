import base64;
import json
import traceback
from time import sleep

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from seleniumwire.utils import decode


def remove_name_extension(name):
    """
    Remove specific name extensions from a given name.
    """
    suffixes_to_remove = ["Jr.", "Sr.", "II", "III", "IV", "Ph.D."]  # Add more suffixes if needed
    cleaned_name = name.replace("'", "").replace("-", "")
    for suffix in suffixes_to_remove:
        cleaned_name = cleaned_name.replace(suffix, "").strip()
    return cleaned_name


# Function to scrape and save data
def scrape_and_save_data(driver, base_url, url_extension):
    decoded_url = str(base64.b64decode(base_url).decode()) + "" + url_extension
    print("Opening URL", decoded_url)
    # Open the initial page
    driver.get(decoded_url)

    # Adjust the locator based on your HTML structure
    table_locator = (By.TAG_NAME, 'table')

    # Wait for the presence of the table
    table = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(table_locator)
    )

    sleep(15)

    dfdata = []
    for request in list(driver.requests):

        # print(
        #     request.url,
        #     request.response.status_code,
        #     request.response.headers['Content-Type'],
        #     flush=True
        # )

        if request.response and 'optimizer-soc' in request.url:
            print("In if",
                  request.url,
                  request.response.status_code,
                  request.response.headers['Content-Type'],
                  flush=True
                  )

            body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
            json_data = json.loads(body)

            with open("test.json", 'w') as file:
                json.dump(json_data, file, indent=4)
                print("JSON data has been written to the file.")

            # f = open('file.json', 'w')
            # f.write(body)
            # f.close()

            # Attempt to parse the extracted text as JSON
            try:
                # Combine the text content of all <pre> elements into a single JSON string
                # combined_json_data = ''.join(json_data_list)

                data = json_data

                for d in data:
                    if d['injury'].strip() == "":
                        name = remove_name_extension(d['first_name'] + " " + d['last_name'])
                        pos = d['position']
                        team = d['team']
                        fp_proj = float(d['proj_points'])
                        print(name, pos, team, fp_proj, flush=True)
                        player = {"PLAYER": name, "POS": pos, "TEAM": team, "FP": fp_proj}
                        dfdata.append(player)

            except json.JSONDecodeError:
                print("The extracted text is not valid JSON.")

    df = pd.DataFrame(dfdata)

    df = df.rename(columns={"PLAYER": "Name", "POS": "Position", "TEAM": "Team", "FP": "Projection"})

    df = df.loc[:, ['Name', 'Position', 'Team', 'Projection']]
    df['Projection'] = df['Projection'].astype(float)
    df = df.sort_values(by=['Projection'], ascending=False)

    return df;


def get_projections():
    # URLs and output folder
    url_root = "aHR0cHM6Ly93d3cucm90b3dpcmUuY29tL2RhaWx5L3NvY2Nlci9vcHRpbWl6ZXIucGhwPw=="

    urls = {
        "epl": "competitionID=1",
        "ucl": "competitionID=22",
        "laliga": "competitionID=5",
        "seriea": "competitionID=6",
        "bundesliga": "competitionID=2",
        "mls": "competitionID=7",
        "ligamx": "competitionID=16",
        "interleague": "competitionID=0",
    }

    dataframes = []
    for key, value in urls.items():
        # Set up the web driver (make sure to specify the path to your browser driver)
        driver = webdriver.Chrome()
        print("Query", key, value, flush=True)
        try:
            dataframes.append(scrape_and_save_data(driver, url_root, value))
        except Exception as e:
            # Print the exception traceback
            traceback.print_exc()
            print("Exception", e)
            print("No projections present for ", value, flush=True)
        # Close the browser
        driver.quit()

    df = pd.concat(dataframes)
    df = df.sort_values(by=['Projection'], ascending=False)
    return df;
