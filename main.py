import base64
import hashlib
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def login(username, password):
    # login
    password_hash = "$sha1$" + sha1(str(password) + str(username))
    authcred = base64.b64encode(
        (str(username) + "\n" + password_hash).encode('utf-8')).decode('utf-8')
    return authcred


def get_response_by_address(authcred, ip, port, address):
    session = requests.Session()
    session.cookies.set("authcred", authcred)
    # sessionid in login form is useless
    # session.cookies.set("sessionid", sessionid)
    response = session.get("http://" + ip + ":" + port + "/ServerAdmin" + address)
    return response


def get_player_info_list(authcred, ip, port):
    current_response = get_response_by_address(authcred, ip, port, "/current/players")
    soup = BeautifulSoup(current_response.text, 'html.parser')
    players = soup.find('table', {'id': 'players'})
    rows = soup.find_all('tr')
    player_info_list = []
    for index, row in enumerate(rows):
        if index == 0:
            continue
        list = row.contents
        filtered_list = [element for index, element in enumerate(list) if index % 2 != 0]
        player_info = [filter.text for filter in filtered_list[:8]]
        player_info_list.append(player_info)
    if player_info_list == [['There are no players']]:
        return None
    return player_info_list


def kick_task(authcred, ip, port, limit_ping, player_trigger):
    print(str(datetime.now())+" run kick_task...")
    original_array = get_player_info_list(authcred, ip, port)
    # no player
    if not original_array:
        return True
    # if few player no kick
    if len(original_array) < player_trigger:
        return True
    current_response = get_response_by_address(authcred, ip, port, "/current/players")
    soup = BeautifulSoup(current_response.text, 'html.parser')
    rows = soup.find_all('tr')
    # 1 row => 1 player info
    for index, row in enumerate(rows):
        if index == 0:
            continue
        list = row.contents
        # get from <td>
        ping = str(list[5].contents)[2:-2]
        if limit_ping < int(ping):
            print("kick player id: " + str(list[3].contents)[2:-2] +
                  " ping : " + str(list[5].contents)[2:-2] +
                  " ip : " + str(list[7].contents)[2:-2]
                  )
            html_string = str(list[17].contents)
            # playerid is random ?
            playerid, playerkey = get2value(html_string)
            kick_user(ip, port, playerid, playerkey, authcred)


def get2value(html_string):

    playerid_start = html_string.find('playerid" type="hidden" value="') + len('playerid" type="hidden" value="')
    playerid_end = html_string.find('"/>', playerid_start)
    playerid = html_string[playerid_start:playerid_end]

    playerkey_start = html_string.find('playerkey" type="hidden" value="') + len('playerkey" type="hidden" value="')
    playerkey_end = html_string.find('"/>', playerkey_start)
    playerkey = html_string[playerkey_start:playerkey_end]
    return playerid, playerkey


def kick_user(ip, port, playerid, playerkey,authcred):
    # str = kick sessionban banip banid mutevoice unmutevoice
    url = "http://" + ip + ":" + port + "/ServerAdmin/current/players"  
    data = {
        "playerid": playerid,
        "playerkey": playerkey,
        "action": "kick"
    }
    session = requests.Session()
    session.cookies.set("authcred", authcred)
    session.post(url, data=data)
    
def revoke_user(ip, port,authcred):
    print("port:: "+ port + " " + str(datetime.now())+" run revoke_user...")
    url = "http://" + ip + ":" + port + "/ServerAdmin/policy/session"  
    data = {
        "banid": 0,
        "action": "revoke"
    }
    session = requests.Session()
    session.cookies.set("authcred", authcred)
    session.post(url, data=data)


def sha1(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


# u ip xxx.xx.xxx.xxx
ip = ""
port = "8080"
port_2 = "8081"
user = "Admin"
password = "password"
authcred = login(user, password)
print("go...")
while True:
    ping = 200
    player_trigger = 30
    # kick_task(authcred, ip, port, ping, player_trigger)
    revoke_user(ip, port,authcred)
    revoke_user(ip, port_2,authcred)
    time.sleep(30)
