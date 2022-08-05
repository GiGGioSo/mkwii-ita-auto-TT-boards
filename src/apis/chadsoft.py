import requests
import datetime
import time

TIME_WAIT_AFTER_GET = 1/2
TIME_WAIT_AFTER_HEAD = 1/10

DEFAULT_BASE_URL = "https://tt.chadsoft.co.uk/"
DEFAULT_URL_MODIFIERS = "?times=pb" #To get only the PBs

### Values meaning of categoryId ###
# 
#   If there's only one mode, usually there's no categoryId field, so i put -1 as placeholder
#
#   If there's a GLITCH but not a SC, then:
#       0 represents Normal
#       1 represents Glitch
#
#   If there's a Non-SC and a SC (and eventually a GLITCH):
#       2 represents Non-SC
#       16 represents SC
#       [optional] 1 represents Glitch
#
### ###### ####### ## ########## ###

def get_player_pbs(ID: str, base_url: str = DEFAULT_BASE_URL, url_modifiers: str = DEFAULT_URL_MODIFIERS) -> str:
    """Make a GET request to chadsoft API to fetch info about a certain ID.

    return: All the player's PBs in a JSON format
    """
    player_url = "players/" + ID[:2] + "/" + ID[2:] + ".json" #API structure to get Player info
    final_url = base_url + player_url + url_modifiers
    r = requests.get(final_url)
    time.sleep(TIME_WAIT_AFTER_GET)
    return r.text

def get_player_last_modified(ID: str, base_url: str = DEFAULT_BASE_URL, url_modifiers: str = DEFAULT_URL_MODIFIERS) -> datetime.datetime:
    """Make a HEAD request to chadsoft API to fetch info about a certain ID.

    return: "Last-Modified" response header
    """
    player_url = "players/" + ID[:2] + "/" + ID[2:] + ".json" #API structure to get Player info
    final_url = base_url + player_url + url_modifiers
    r = requests.head(final_url)
    time.sleep(TIME_WAIT_AFTER_HEAD)
    return get_datetime_from_chadsoft_date(r.headers["Last-Modified"])

def get_datetime_from_chadsoft_date(cd_date: str) -> datetime.datetime:
    """Transform chadsoft date into a datetime.datetime object

    return:
    """
    cd_date = cd_date.split()
    hr_raw = [int(x) for x in cd_date[4].split(":")]
    if cd_date[2] == "Jan":
        cd_date[2] = 1
    elif cd_date[2] == "Feb":
        cd_date[2] = 2
    elif cd_date[2] == "Mar":
        cd_date[2] = 3
    elif cd_date[2] == "Apr":
        cd_date[2] = 4
    elif cd_date[2] == "May":
        cd_date[2] = 5
    elif cd_date[2] == "Jun":
        cd_date[2] = 6
    elif cd_date[2] == "Jul":
        cd_date[2] = 7
    elif cd_date[2] == "Aug":
        cd_date[2] = 8
    elif cd_date[2] == "Sep":
        cd_date[2] = 9
    elif cd_date[2] == "Oct":
        cd_date[2] = 10
    elif cd_date[2] == "Nov":
        cd_date[2] = 11
    elif cd_date[2] == "Dec":
        cd_date[2] = 12
    else:
        print("[ERROR] '"+cd_date[2]+"' is an invalid month")

    return datetime.datetime(int(cd_date[3]), cd_date[2], int(cd_date[1]), hr_raw[0], hr_raw[1], hr_raw[2])

def get_ghost_mii(ghost: str) -> str:
    return "https://www.chadsoft.co.uk/time-trials" + ghost[:-3] + "mii"

def get_ghost_link(ghost: str) -> str:
    return "https://www.chadsoft.co.uk/time-trials" + ghost[:-3] + "html"

def get_vehicle(ID: int) -> str:
    if ID == 0: 
        return "Standard Kart S"  
    if ID == 1: 
        return "Standard Kart M"  
    if ID == 2: 
        return "Standard Kart L"  
    if ID == 3: 
        return "Booster Seat"  
    if ID == 4: 
        return "Classic Dragster"  
    if ID == 5: 
        return "Offroader"  
    if ID == 6: 
        return "Mini Beast"  
    if ID == 7: 
        return "Wild Wing"  
    if ID == 8: 
        return "Flame Flyer"  
    if ID == 9: 
        return "Cheep Charger"  
    if ID == 10: 
        return "Super Blooper"  
    if ID == 11: 
        return "Piranha Prowler"  
    if ID == 12: 
        return "Tiny Titan"  
    if ID == 13: 
        return "Daytripper"  
    if ID == 14: 
        return "Jetsetter"  
    if ID == 15: 
        return "Blue Falcon"  
    if ID == 16: 
        return "Sprinter"  
    if ID == 17: 
        return "Honeycoupe"  
    if ID == 18: 
        return "Standard Bike S"  
    if ID == 19: 
        return "Standard Bike M"  
    if ID == 20: 
        return "Standard Bike L"  
    if ID == 21: 
        return "Bullet Bike"  
    if ID == 22: 
        return "Mach Bike"  
    if ID == 23: 
        return "Flame Runner"  
    if ID == 24: 
        return "Bit Bike"  
    if ID == 25: 
        return "Sugarscoot"  
    if ID == 26: 
        return "Wario Bike"  
    if ID == 27: 
        return "Quacker"  
    if ID == 28: 
        return "Zip Zip"  
    if ID == 29: 
        return "Shooting Star"  
    if ID == 30: 
        return "Magikruiser"  
    if ID == 31: 
        return "Sneakster"  
    if ID == 32: 
        return "Spear"  
    if ID == 33: 
        return "Jet Bubble"  
    if ID == 34: 
        return "Dolphin Dasher"  
    if ID == 35: 
        return "Phantom"  
    else: 
        return "" 

def get_driver(ID: int) -> str:
    if ID == 0: 
        return "Mario"
    if ID == 1: 
        return "Baby Peach"
    if ID == 2: 
        return "Waluigi"
    if ID == 3: 
        return "Bowser"
    if ID == 4: 
        return "Baby Daisy"
    if ID == 5: 
        return "Dry Bones"
    if ID == 6: 
        return "Baby Mario"
    if ID == 7: 
        return "Luigi"
    if ID == 8: 
        return "Toad"
    if ID == 9: 
        return "Donkey Kong"
    if ID == 10: 
        return "Yoshi"
    if ID == 11: 
        return "Wario"
    if ID == 12: 
        return "Baby Luigi"
    if ID == 13: 
        return "Toadette"
    if ID == 14: 
        return "Koopa"
    if ID == 15: 
        return "Daisy"
    if ID == 16: 
        return "Peach"
    if ID == 17: 
        return "Birdo"
    if ID == 18: 
        return "Diddy Kong"
    if ID == 19: 
        return "King Boo"
    if ID == 20: 
        return "Bowser Jr."
    if ID == 21: 
        return "Dry Bowser"
    if ID == 22: 
        return "Funky Kong"
    if ID == 23: 
        return "Rosalina"
    if ID == 24: 
        return "Small Mii A Male"
    if ID == 25: 
        return "Small Mii A Female"
    if ID == 26: 
        return "Small Mii B Male"
    if ID == 27: 
        return "Small Mii B Female"
    if ID == 30: 
        return "Medium Mii A Male"
    if ID == 31: 
        return "Medium Mii A Female"
    if ID == 32: 
        return "Medium Mii B Male"
    if ID == 33: 
        return "Medium Mii B Female"
    if ID == 36: 
        return "Large Mii A Male"
    if ID == 37: 
        return "Large Mii A Female"
    if ID == 38: 
        return "Large Mii B Male"
    if ID == 39: 
        return "Large Mii B Female"
    else: 
        return ""

def get_controller(ID: int) -> str:
    if ID == 0: 
        return "Wii Wheel" 
    if ID == 1: 
        return "Nunchuck" 
    if ID == 2: 
        return "Classic"
    if ID == 3: 
        return "GameCube"
    if ID == 15: 
        return "???" 
    else: 
        return ""

def get_category(ID: int) -> str:
    if ID == -1 or ID == 0 or ID == 2:
        return "No-SC"
    elif ID == 1:
        return "Glitch"
    elif ID == 16:
        return "SC"
    else:
        return f"unknown:{ID}"
