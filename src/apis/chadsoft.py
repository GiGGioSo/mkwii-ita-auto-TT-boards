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
    match cd_date[2]:
        case "Jan" : cd_date[2] = 1
        case "Feb" : cd_date[2] = 2
        case "Mar" : cd_date[2] = 3
        case "Apr" : cd_date[2] = 4
        case "May" : cd_date[2] = 5
        case "Jun" : cd_date[2] = 6
        case "Jul" : cd_date[2] = 7
        case "Aug" : cd_date[2] = 8
        case "Sep" : cd_date[2] = 9
        case "Oct" : cd_date[2] = 10
        case "Nov" : cd_date[2] = 11
        case "Dec" : cd_date[2] = 12
        case _: print("[ERROR] '"+cd_date[2]+"' is an invalid month")

    return datetime.datetime(int(cd_date[3]), cd_date[2], int(cd_date[1]), hr_raw[0], hr_raw[1], hr_raw[2])

def get_ghost_mii(ghost: str) -> str:
    return "https://www.chadsoft.co.uk/time-trials" + ghost[:-3] + "mii"

def get_ghost_link(ghost: str) -> str:
    return "https://www.chadsoft.co.uk/time-trials" + ghost[:-3] + "html"

def get_vehicle(ID: int) -> str:

    match ID:
        case 0  : return "Standard Kart S"  
        case 1  : return "Standard Kart M"  
        case 2  : return "Standard Kart L"  
        case 3  : return "Booster Seat"  
        case 4  : return "Classic Dragster"  
        case 5  : return "Offroader"  
        case 6  : return "Mini Beast"  
        case 7  : return "Wild Wing"  
        case 8  : return "Flame Flyer"  
        case 9  : return "Cheep Charger"  
        case 10 : return "Super Blooper"  
        case 11 : return "Piranha Prowler"  
        case 12 : return "Tiny Titan"  
        case 13 : return "Daytripper"  
        case 14 : return "Jetsetter"  
        case 15 : return "Blue Falcon"  
        case 16 : return "Sprinter"  
        case 17 : return "Honeycoupe"  
        case 18 : return "Standard Bike S"  
        case 19 : return "Standard Bike M"  
        case 20 : return "Standard Bike L"  
        case 21 : return "Bullet Bike"  
        case 22 : return "Mach Bike"  
        case 23 : return "Flame Runner"  
        case 24 : return "Bit Bike"  
        case 25 : return "Sugarscoot"  
        case 26 : return "Wario Bike"  
        case 27 : return "Quacker"  
        case 28 : return "Zip Zip"  
        case 29 : return "Shooting Star"  
        case 30 : return "Magikruiser"  
        case 31 : return "Sneakster"  
        case 32 : return "Spear"  
        case 33 : return "Jet Bubble"  
        case 34 : return "Dolphin Dasher"  
        case 35 : return "Phantom"  
        case _: return "" 

def get_driver(ID: int) -> str:
    
    match ID:
        case 0  : return "Mario"
        case 1  : return "Baby Peach"
        case 2  : return "Waluigi"
        case 3  : return "Bowser"
        case 4  : return "Baby Daisy"
        case 5  : return "Dry Bones"
        case 6  : return "Baby Mario"
        case 7  : return "Luigi"
        case 8  : return "Toad"
        case 9  : return "Donkey Kong"
        case 10 : return "Yoshi"
        case 11 : return "Wario"
        case 12 : return "Baby Luigi"
        case 13 : return "Toadette"
        case 14 : return "Koopa"
        case 15 : return "Daisy"
        case 16 : return "Peach"
        case 17 : return "Birdo"
        case 18 : return "Diddy Kong"
        case 19 : return "King Boo"
        case 20 : return "Bowser Jr."
        case 21 : return "Dry Bowser"
        case 22 : return "Funky Kong"
        case 23 : return "Rosalina"
        case 24 : return "Small Mii A Male"
        case 25 : return "Small Mii A Female"
        case 26 : return "Small Mii B Male"
        case 27 : return "Small Mii B Female"
        case 30 : return "Medium Mii A Male"
        case 31 : return "Medium Mii A Female"
        case 32 : return "Medium Mii B Male"
        case 33 : return "Medium Mii B Female"
        case 36 : return "Large Mii A Male"
        case 37 : return "Large Mii A Female"
        case 38 : return "Large Mii B Male"
        case 39 : return "Large Mii B Female"
        case _  : return ""

def get_controller(ID: int) -> str:
    match ID:
        case 0  : return "Wii Wheel" 
        case 1  : return "Nunchuck" 
        case 2  : return "Classic"
        case 3  : return "GameCube"
        case 15 : return "???" 
        case _  : return ""

def get_category(ID: int) -> str:
    if ID in [0, -1, 2, 18]:
        return "No-SC"
    elif ID == 1:
        return "Glitch"
    elif ID == 16:
        return "SC"
    else:
        return f"unknown:{ID}"
