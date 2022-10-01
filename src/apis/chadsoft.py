import requests
import datetime
import time

from apis.google_sheet import RT_CATEGORIES
from apis.google_sheet import CATEGORY_IDS

TIME_WAIT_AFTER_GET = 1/2
TIME_WAIT_AFTER_HEAD = 1/10

DEFAULT_BASE_URL = "https://tt.chadsoft.co.uk/"
DEFAULT_URL_MODIFIERS = "?times=pb" #To get only the PBs

RT_TRACKS = {
    "08/1AE1A7D894960B38E09E7494373378D87305A163/" : CATEGORY_IDS["Case_Normal"],                 # LC                 Circuito di Luigi
    "01/90720A7D57A7C76E2347782F6BDE5D22342FB7DD/" : CATEGORY_IDS["Case_Normal"],                 # MMM                Prateria verde
    "02/0E380357AFFCFD8722329994885699D9927F8276/" : CATEGORY_IDS["Case_Normal_Shortcut_Glitch"], # MG    (NO-SC+SC/G) Gola Fungo
    "04/1896AEA49617A571C66FF778D8F2ABBE9E5D7479/" : CATEGORY_IDS["Case_Normal_Shortcut"],        # TF    (NO-SC/SC)   Fabbrica di Toad
    "00/7752BB51EDBC4A95377C0A05B0E0DA1503786625/" : CATEGORY_IDS["Case_Normal_Glitch"],          # MC    (NO-SC/G)    Circuito di Mario
    "05/E4BF364CB0C5899907585D731621CA930A4EF85C/" : CATEGORY_IDS["Case_Normal_Shortcut_Glitch"], # CM    (NO-SC/SC/G) Outlet Cocco
    "06/B02ED72E00B400647BDA6845BE387C47D251F9D1/" : CATEGORY_IDS["Case_Normal"],                 # DKSC               Pista Snowboard DK
    "07/D1A453B43D6920A78565E65A4597E353B177ABD0/" : CATEGORY_IDS["Case_Normal_Glitch"],          # WGM   (NO-SC/G)    Miniera d'oro di Wario
    "09/72D0241C75BE4A5EBD242B9D8D89B1D6FD56BE8F/" : CATEGORY_IDS["Case_Normal"],                 # DC                 Circuito di Daisy
    "0F/52F01AE3AED1E0FA4C7459A648494863E83A548C/" : CATEGORY_IDS["Case_Normal_Glitch"],          # KC    (NO-SC/G)    Punta Koopa
    "0B/48EBD9D64413C2B98D2B92E5EFC9B15ECD76FEE6/" : CATEGORY_IDS["Case_Normal_Glitch"],          # MT    (NO-SC/G)    Pista degli aceri
    "03/ACC0883AE0CE7879C6EFBA20CFE5B5909BF7841B/" : CATEGORY_IDS["Case_Normal_Shortcut_Glitch"], # GV    (NO-SC/SC/G) Vulcano brontolone
    "0E/38486C4F706395772BD988C1AC5FA30D27CAE098/" : CATEGORY_IDS["Case_Normal"],                 # DDR                Rovine desertiche
    "0A/B13C515475D7DA207DFD5BADD886986147B906FF/" : CATEGORY_IDS["Case_Normal"],                 # MH                 Autostrada lunare
    "0C/B9821B14A89381F9C015669353CB24D7DB1BB25D/" : CATEGORY_IDS["Case_Normal_Shortcut"],        # BC    (NO-SC/SC)   Castello di Bowser
    "0D/FFE518915E5FAAA889057C8A3D3E439868574508/" : CATEGORY_IDS["Case_Normal_Glitch"],          # RR    (NO-SC/G)    Pista Arcobaleno
    "10/8014488A60F4428EEF52D01F8C5861CA9565E1CA/" : CATEGORY_IDS["Case_Normal_Glitch"],          # rPB   (NO-SC/G)    GCN Spiaggia di Peach
    "14/8C854B087417A92425110CC71E23C944D6997806/" : CATEGORY_IDS["Case_Normal"],                 # rYF                DS Cascate di Yoshi
    "19/071D697C4DDB66D3B210F36C7BF878502E79845B/" : CATEGORY_IDS["Case_Normal_Glitch"],          # rGV2  (NO-SC/G)    SNES Valle fantasma 2
    "1A/49514E8F74FEA50E77273C0297086D67E58123E8/" : CATEGORY_IDS["Case_Normal"],                 # rMR                N64 Pista di Mario
    "1B/BA9BCFB3731A6CB17DBA219A8D37EA4D52332256/" : CATEGORY_IDS["Case_Normal_Glitch"],          # rSL   (NO-SC/G)    N64 Circuito Gelato
    "1F/E8ED31605CC7D6660691998F024EED6BA8B4A33F/" : CATEGORY_IDS["Case_Normal_Glitch"],          # rSGB  (NO-SC/G)    GBA Spiaggia Tipo Timido
    "17/BC038E163D21D9A1181B60CF90B4D03EFAD9E0C5/" : CATEGORY_IDS["Case_Normal"],                 # rDS                DS Borgo Delfino
    "12/418099824AF6BF1CD7F8BB44F61E3A9CC3007DAE/" : CATEGORY_IDS["Case_Normal_Glitch"],          # rWS   (NO-SC/G)    GCN Stadio di Waluigi
    "15/4EC538065FDC8ACF49674300CBDEC5B80CC05A0D/" : CATEGORY_IDS["Case_Normal_Shortcut"],        # rDH   (NO-SC/SC)   DS Deserto Picchiasol
    "1E/A4BEA41BE83D816F793F3FAD97D268F71AD99BF9/" : CATEGORY_IDS["Case_Normal_Shortcut"],        # rBC3  (NO-SC/SC)   GBA Castello di Bowser 3
    "1D/692D566B05434D8C66A55BDFF486698E0FC96095/" : CATEGORY_IDS["Case_Normal_Shortcut_Glitch"],          # rDKJP (NO-SC/SC/G) N64 Viale Giungla DK
    "11/1941A29AD2E7B7BBA8A29E6440C95EF5CF76B01D/" : CATEGORY_IDS["Case_Normal_Shortcut"],        # rMC   (NO-SC/SC)   GCN Circuito di Mario
    "18/077111B996E5C4F47D20EC29C2938504B53A8E76/" : CATEGORY_IDS["Case_Normal"],                 # rMC3               SNES Circuito di Mario 3
    "16/F9A62BEF04CC8F499633E4023ACC7675A92771F0/" : CATEGORY_IDS["Case_Normal"],                 # rPG                DS Giardino di Peach
    "13/B036864CF0016BE0581449EF29FB52B2E58D78A4/" : CATEGORY_IDS["Case_Normal_Shortcut"],        # rDKM  (NO-SC/SC)   GCN Montagne DK
    "1C/15B303B288F4707E5D0AF28367C8CE51CDEAB490/" : CATEGORY_IDS["Case_Normal_Glitch"],          # rBC   (NO-SC/G)    N64 Castello di Bowser
}

### Values meaning of categoryId ###
# 
#   If there's only one mode, usually there's no categoryId field, so i put -1 as placeholder
#
#       02 represents Normal
#       01 represents Glitch
#       00 represents No-Glitch
#
### ###### ####### ## ########## ###

def get_leaderboard_page(track_link:str,category_id:str,flap:bool):
    if flap == True: flap = "-fast-lap"
    else: flap = ""
    base_url = "https://tt.chadsoft.co.uk/leaderboard/"
    r = requests.get(base_url+track_link+category_id+flap+".json?times=pb")
    return r.json()

def get_player_pbs(ID: str, base_url: str = DEFAULT_BASE_URL, url_modifiers: str = DEFAULT_URL_MODIFIERS) -> str:
    """Make a GET request to chadsoft API to fetch info about a certain ID.

    return: All the player's PBs in a JSON format
    """
    player_url = "players/" + ID[:2] + "/" + ID[2:] + ".json" #API structure to get Player info
    final_url = base_url + player_url + url_modifiers
    r = requests.get(final_url)
    time.sleep(TIME_WAIT_AFTER_GET)
    return r.text

def get_track_json(track_link: str, base_url: str = DEFAULT_BASE_URL, url_modifiers: str = DEFAULT_URL_MODIFIERS) -> str:
    """Make a GET request to chadsoft API to fetch info about a certain ID.

    return: All the player's PBs in a JSON format
    """
    player_url = "players/" + ID[:2] + "/" + ID[2:] + "-fast-lap.json" #API structure to get Player info
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

def get_date_from_rkg(rkg_file):
    rkg_file = "{:08b}".format(int(rkg_file.hex(), 16))
    year = str(2000 + int(rkg_file[75:82],base=2))
    month = str(int(rkg_file[82:86],base=2)).zfill(2)
    day = str(int(rkg_file[86:91],base=2)).zfill(2)
    return f"{year}-{month}-{day}"

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

def get_ghost_link(ghost: str) -> str:
    return "https://www.chadsoft.co.uk/time-trials" + ghost[:-3] + "html"

def get_ghost_rkg(ghost: str) -> str:
    r = requests.get("https://www.chadsoft.co.uk/time-trials" + ghost[:-3] + "rkg")
    return r.content 

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
