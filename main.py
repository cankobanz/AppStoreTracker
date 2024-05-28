"""
+ 1. Go to page.
+ 2. Get Name and maybe id of the user
+ 4. Get the game links.
+ Save last checked game links to check later
5. Check every hour is there a change in the games.
+ 6. Send user-name, game link to discord channel.
7. Create database or csv file to manage links of the users
8. Find a place to continuously run the script. https://python.plainenglish.io/auto-schedule-python-scripts-on-mac-37adac5db520
"""
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import lo

excel_file = pd.read_excel('SoftLaunch_AppStore.xlsx', sheet_name='Sheet1', usecols='B')
APP_STORE_URLS = excel_file['Store Name']
SEE_ALL_URL = '?see-all=i-phonei-pad-apps'


# with open("user_urls.txt", "r") as file:
#     APP_STORE_URLS = file.read().splitlines()


def handle_url(url: str) -> dict:
    components = url.split('/')
    user_id = components[-1]
    user_name = components[-2]
    user_info = {
        "name": user_name,
        "url": url
    }
    return user_id, user_info


def get_games(soup: BeautifulSoup) -> dict:
    games = {}
    for p in soup.find_all(name="a", class_="we-lockup"):
        game_info = p['aria-label'].split('. ')
        game_name = game_info[0]
        game_category = game_info[1].strip('.')
        game_link = p['href']
        games[game_name] = {
            'name': game_name,
            'category': game_category,
            'link': game_link
        }
    return games


def scrap_data():
    users_info = {}
    for url in APP_STORE_URLS:
        user_id, info = handle_url(url=url)
        users_info[user_id] = info

    for key, val, in users_info.items():
        response = requests.get(val['url'] + SEE_ALL_URL)
        data = response.text
        soup = BeautifulSoup(data, "html.parser")
        games = get_games(soup=soup)
        users_info[key]['games'] = games
    return users_info


def detect_differences(p: dict, c: dict):
    difference = []
    for key, val in p.items():
        p_games = val['games']
        try:
            c_games = c[key]['games']

            # Find keys that are in A: current but not in B: past
            for k in c_games.keys():
                if k not in p_games.keys():
                    d = {"user_id": key, "user_name": c[key]['name'], "diff_game_info": c_games[k]}
                    difference.append(d)
        except KeyError:
            print(f'User {key} is added new. The user will be tracked until now.')
            pass
    if not difference:
        return None
    m = ""
    for component in difference:
        m = m + f"{component['user_name']} is uploaded {component['diff_game_info']['name']} here the link to game:\n{component['diff_game_info']['link']}\n\n"
    return m


def write_file(users_info, file_name='users_info.json'):
    json_users = json.dumps(users_info)
    with open(file_name, 'w') as outfile:
        # print(f'{file_name} file is available to track updates.')
        outfile.write(json_users)


def send_discord_message(content):
    webhook_url = ""  # Add your discord webhook here.
    m = {
        'content': content
    }
    # Convert the message dictionary to JSON format
    payload = json.dumps(m)

    # Set the content type to JSON
    headers = {'Content-Type': 'application/json'}

    # Send the POST request to the webhook URL
    response = requests.post(webhook_url, data=payload, headers=headers)

    # Check if the message was sent successfully
    if response.status_code == 204:
        print('Message sent successfully')
    else:
        print('Failed to send message')
        print('Response:', response.text)


if __name__ == '__main__':

    import time

    start_time = time.time()

    try:
        with open("users_info.json", "r") as json_file:
            past_users_info = json.load(json_file)
            curr_users_info = scrap_data()
            message = detect_differences(past_users_info, curr_users_info)
            if message is not None:
                send_discord_message(message)
            write_file(curr_users_info)
    except FileNotFoundError:
        print("You are running the program first time. Data is collecting.")
        users_info = scrap_data()
        write_file(users_info)

    end_time = time.time()

    # Calculate elapsed time
    elapsed_time = end_time - start_time
    print("Elapsed time: ", elapsed_time)
