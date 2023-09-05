from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.edge.service import Service
import pandas as pd
import os
import zipfile
import requests
from datetime import timedelta
import time
import re


def get_chrome_driver():
    chrome_version, chrome_path = '115.0.5790.102', r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    chrome_architecture = '32' if 'x86' in chrome_path else '64'
    chrome_milestone = chrome_version.split('.')[0]
    print(f'Your Google Chrome version: {chrome_version}')
    chrome_driver_file = 'chromedriver.exe'
    chrome_driver_path = os.path.join(os.getcwd(), chrome_driver_file)
    chrome_driver_exists = os.path.isfile(chrome_driver_path)
    print(f'External Chrome driver exists? {chrome_driver_exists}')
    chrome_driver_compatible = False
    if chrome_driver_exists:
        chrome_driver_version = os.popen(
            f'\"{chrome_driver_path}\" --version').read().split(' ')[1]
        chrome_driver_compatible = chrome_version.split(
            '.')[:3] == chrome_driver_version.split('.')[:3]
        print(
            f'Existing Chrome driver path: {os.path.join(chrome_driver_path, chrome_driver_file)}')
        print(f'Existing Chrome driver version: {chrome_driver_version}')
        print(f'Existing Chrome driver compatible? {chrome_driver_compatible}')
        print()

    if not chrome_driver_exists or not chrome_driver_compatible:
        # Downloads the chromedriver.exe file from the links
        # provided by the Chrome for Testing project:
        # https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json
        # and places it in the same directory as this script.
        chrome_for_testing_url = 'https://googlechromelabs.github.io/chrome-for-testing/'
        chrome_for_testing_json_endpoint = 'latest-versions-per-milestone-with-downloads.json'
        chrome_for_testing = requests.get(
            chrome_for_testing_url + chrome_for_testing_json_endpoint).json()
        chrome_driver_downloads = chrome_for_testing['milestones'][
            chrome_milestone]['downloads']['chromedriver']
        chrome_driver_zip_url = None
        for download in chrome_driver_downloads:
            if download['platform'] == 'win' + chrome_architecture:
                chrome_driver_zip_url = download['url']
                break
        # Download, replacing the existing chromedriver.exe if it exists.
        print(
            f'Downloading {"latest " if chrome_driver_exists else ""}Chrome driver...')
        if chrome_driver_exists:
            os.remove(chrome_driver_path)
        chrome_driver_zip = requests.get(chrome_driver_zip_url)
        chrome_driver_zip_folder = f'chromedriver-win{chrome_architecture}'
        if os.path.isdir(chrome_driver_zip_folder):
            os.rename(chrome_driver_zip_folder,
                      chrome_driver_zip_folder + '_old')
        with open(chrome_driver_zip_folder + '.zip', 'wb') as f:
            f.write(chrome_driver_zip.content)
        with zipfile.ZipFile(chrome_driver_zip_folder + '.zip', 'r') as zip_ref:
            zip_ref.extract(chrome_driver_zip_folder +
                            '/chromedriver.exe', os.getcwd())
        os.rename(chrome_driver_zip_folder +
                  '/chromedriver.exe', 'chromedriver.exe')
        os.remove(chrome_driver_zip_folder + '.zip')
        os.removedirs(chrome_driver_zip_folder)
        if os.path.isdir(chrome_driver_zip_folder + '_old'):
            os.removedirs(chrome_driver_zip_folder + '_old')

        print('Chrome driver downloaded.')
        chrome_driver_compatible = True

    return os.path.isfile(chrome_driver_path), chrome_driver_path


def webdriver_connection():
    """
    Establishes a connection to the Chrome WebDriver.

    Returns:
        webdriver.Chrome: The WebDriver instance for Chrome.
    """
    try:
        chrome_options = Options()
        # Run in headless mode to avoid opening a browser window
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dns-prefetch')
        # Modify the user agent to avoid detection
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        # Disable WebRTC
        chrome_options.add_experimental_option(
            "prefs", {"webrtc.ip_handling_policy": "disable_non_proxied_udp"})

        # Suppress console logs
        chrome_options.add_argument('--log-level=3')
        driver = webdriver.Chrome(options=chrome_options)

        # JavaScript Execution to avoid detection
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print(e)
    else:
        driver.maximize_window()
    return driver


def convert_time(match_time):
    minutes, seconds = map(int, match_time.split(':'))
    return timedelta(minutes=minutes, seconds=seconds)


def get_data_from_22_bet(url, driver_path):
    service = Service(executable_path=driver_path)
    chrome_options = Options()
    # Run in headless mode to avoid opening a browser window
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dns-prefetch')
    # Modify the user agent to avoid detection
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # Disable WebRTC
    chrome_options.add_experimental_option(
        "prefs", {"webrtc.ip_handling_policy": "disable_non_proxied_udp"})

    # Suppress console logs
    chrome_options.add_argument('--log-level=3')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # JavaScript Execution to avoid detection
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    # Wait for the team names to be present in the page source

    driver.set_page_load_timeout(100)
    driver.get(url)
    start_time = time.time()
    
    wait = WebDriverWait(driver, 100)
    wait.until(EC.presence_of_all_elements_located(
        (By.CLASS_NAME, 'c-events__team')))

    site_content = driver.page_source
    soup = BeautifulSoup(site_content, 'html.parser')

    # Extract team names
    team_names = soup.find_all('span', class_='c-events__team u-ovh')
    team_names_list = [team.text for team in team_names]

    # Extract time
    time_elements = soup.find_all('div', class_='c-events__time min')

    end_time = time.time()

    execution_time = end_time - start_time
    execution_seconds = int(execution_time)
    # print(execution_seconds)

    time_list = [time_element.find(
        'span').text for time_element in time_elements]

    time_list = []
    for time_element in time_elements:
        match_time = time_element.find('span').text
        if match_time:  # Check if match_time is not an empty string
            match_time_obj = convert_time(match_time)
            new_time_obj = match_time_obj + \
                timedelta(seconds=execution_seconds)
            total_seconds = new_time_obj.total_seconds()
            new_minutes = int(total_seconds // 60)
            new_seconds = int(total_seconds % 60)
            new_time_str = f"{new_minutes:02}:{new_seconds:02}"
            time_list.append(new_time_str)
        else:
            # or whatever default value you want for empty times
            time_list.append('00:00')

    # Extract values for 1, X, and 2
    bet_values_elements = soup.find_all('div', class_='c-bets')
    bet_values_list = []
    for bet_values in bet_values_elements:
        bets = bet_values.find_all('span', class_='c-bets__inner')
        if len(bets) >= 3:
            bet_values_list.append([bets[0].text, bets[1].text, bets[2].text])

    # Create lists for team1, team2, their times, and their bet values
    team1_names = team_names_list[::2]
    team2_names = team_names_list[1::2]
    bet1_values = [bet_values[0] for bet_values in bet_values_list]
    betX_values = [bet_values[1] for bet_values in bet_values_list]
    bet2_values = [bet_values[2] for bet_values in bet_values_list]
    # Check lengths
    min_length = min(len(team1_names), len(team2_names), len(
        time_list), len(bet1_values), len(betX_values), len(bet2_values))

    # Truncate lists to the minimum length
    team1_names = team1_names[:min_length]
    team2_names = team2_names[:min_length]
    time_list = time_list[:min_length]
    bet1_values = bet1_values[:min_length]
    betX_values = betX_values[:min_length]
    bet2_values = bet2_values[:min_length]

    driver.quit()

    return pd.DataFrame({
        'Team1': team1_names,
        'Team2': team2_names,
        'Time': time_list,
        '1': bet1_values,
        'X': betX_values,
        '2': bet2_values
    })


def adjust_time_format(time_str):
    # Regular expression to match the format "90:00+03:18"
    match = re.match(r"(\d+):(\d+)\+(\d+):(\d+)", time_str)
    if match:
        # Extract the main minutes, main seconds, added minutes, and added seconds
        main_minutes, main_seconds, added_minutes, added_seconds = map(
            int, match.groups())

        # Calculate the total minutes and seconds
        total_seconds = main_seconds + added_seconds
        total_minutes = main_minutes + added_minutes + total_seconds // 60
        total_seconds %= 60

        # Return the adjusted time format
        return f"{total_minutes}:{total_seconds:02}"
    else:
        return time_str


def extract_details(response):
    # Extract the relevant data from the JSON response
    matches = response["result"]

    # Create empty lists to store the extracted data
    team1_list = []
    team2_list = []
    time_list = []
    score_list = []
    list_1 = []
    list_x = []
    list_2 = []

    # Iterate through each match in the JSON data
    for match in matches:
        # Check if 'starting' and '1X2' exist in the dictionary
        if 'live' in match['odds'] and '1X2' in match['odds']['live'] and 'bet365' in match['odds']['live']['1X2']:
            team1_name = match["teamA"]["name"]
            team2_name = match["teamB"]["name"]
            match_time = match["timer"]
            adjusted_time = adjust_time_format(match_time)
            # score_team1 = match["teamA"]["score"]["f"]
            # score_team2 = match["teamB"]["score"]["f"]

            # Append the extracted data to the respective lists
            team1_list.append(team1_name)
            team2_list.append(team2_name)
            time_list.append(adjusted_time)
            # score_list.append(f"{score_team1} - {score_team2}")

            odds = match['odds']['live']
            get_odds = odds['1X2']
            get_bet = get_odds['bet365']
            list_1.append(get_bet['1'])
            list_2.append(get_bet['2'])
            list_x.append(get_bet['X'])

    # Create a DataFrame using the extracted data
    df = pd.DataFrame({
        "Team1": team1_list,
        "Team2": team2_list,
        "Time": time_list,
        # "Score": score_list,
        "1": list_1,
        "X": list_x,
        "2": list_2
    })
    return df


def display_22betlive_matches():
    # URLs of the websites
    url1 = "https://22bet.com/en/live/football"
    chrome_driver_exists, chrome_driver_path = get_chrome_driver()
    # Scrape data with 22bet
    df2 = get_data_from_22_bet(url1, chrome_driver_path)

    return df2


def display_bet365live_matches():
    url2 = "https://soccer-football-info.p.rapidapi.com/live/full/"

    querystring = {"l": "en_US", "e": "no"}

    headers = {
        "X-RapidAPI-Key": "2bfa3739e4mshea92d9cff8130c7p1fddb2jsn31ec27a45e3d",
        "X-RapidAPI-Host": "soccer-football-info.p.rapidapi.com"
    }

    response = requests.get(url2, headers=headers, params=querystring)

    df1 = extract_details(response.json())
    return df1


# Convert time to seconds
def time_to_seconds(time_str):
    minutes, seconds = map(int, time_str.split(':'))
    return minutes * 60 + seconds


def get_timedelay(df1= display_bet365live_matches(), df2 = display_22betlive_matches()):
    df1['Time_in_seconds'] = df1['Time'].apply(time_to_seconds)
    df2['Time_in_seconds'] = df2['Time'].apply(time_to_seconds)

    # Merge dataframes based on team names
    merged_df = pd.merge(
        df1, df2, on=['Team1', 'Team2'], suffixes=('_df1', '_df2'))

    # Calculate time difference and filter rows
    merged_df['Time_difference'] = abs(
        merged_df['Time_in_seconds_df1'] - merged_df['Time_in_seconds_df2'])
    filtered_df = merged_df[merged_df['Time_difference'] >= 15]

    # Determine which dataframe's time is greater
    filtered_df['Greater_time_df'] = filtered_df.apply(
        lambda row: 'df1' if row['Time_in_seconds_df1'] > row['Time_in_seconds_df2'] else 'df2', axis=1)

    result = filtered_df[['Team1', 'Team2', 'Time_df1', 'Time_df2', '1_df1',
                          'X_df1', '2_df1', '1_df2', 'X_df2', '2_df2', 'Greater_time_df']]

    return result
