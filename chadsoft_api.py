import requests
import json
import gspread
import datetime
import time
import traceback

# Google Sheet : https://docs.google.com/spreadsheets/d/19qNyxZstZ2htq48dLRoupDBu74ZJOFw66vb8RXhN6XE/edit#gid=58+3825868


start_time = time.time()
TIME_WAIT_AFTER_GET = 1/2
TIME_WAIT_AFTER_HEAD = 1/10

GS_START_INDEX = 10
GS_TRACKS_INTERVAL = 8
NUM_ROWS_PARTIAL_UPDATE = 5

### Values meaning ###
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
### ###### ####### ###

RT_CATEGORIES = {
    "1AE1A7D894960B38E09E7494373378D87305A163": [-1],   # Circuito di Luigi
    "90720A7D57A7C76E2347782F6BDE5D22342FB7DD": [-1],  # Prateria verde
    "0E380357AFFCFD8722329994885699D9927F8276": [18, 1],  # Gola Fungo (Normal / Glitch)
    "1896AEA49617A571C66FF778D8F2ABBE9E5D7479": [2, 16],  # Fabbrica di Toad (Non-SC / SC)
    "7752BB51EDBC4A95377C0A05B0E0DA1503786625": [0, 1],  # Circuito di Mario (Normal / Glitch)
    "E4BF364CB0C5899907585D731621CA930A4EF85C": [2, 16, 1],  # Outlet Cocco (Non-SC / SC / Glitch)
    "B02ED72E00B400647BDA6845BE387C47D251F9D1": [-1],  # Pista snowboard DK
    "D1A453B43D6920A78565E65A4597E353B177ABD0": [0, 1],  # Miniera d'oro di Wario (Normal / Glitch)
    "72D0241C75BE4A5EBD242B9D8D89B1D6FD56BE8F": [-1],  # Circuito di Daisy
    "52F01AE3AED1E0FA4C7459A648494863E83A548C": [0, 1],  # Punta Koopa (Normal / Glitch)
    "48EBD9D64413C2B98D2B92E5EFC9B15ECD76FEE6": [0, 1],  # Pista degli aceri (Normal / Glitch)
    "ACC0883AE0CE7879C6EFBA20CFE5B5909BF7841B": [2, 16, 1],  # Vulcano brontolone (Non-SC / SC / Glitch)
    "38486C4F706395772BD988C1AC5FA30D27CAE098": [-1],  # Rovine desertiche
    "B13C515475D7DA207DFD5BADD886986147B906FF": [-1],  # Autostrada lunare
    "B9821B14A89381F9C015669353CB24D7DB1BB25D": [2, 16],  # Castello di Bowser (Non-SC / SC)
    "FFE518915E5FAAA889057C8A3D3E439868574508": [0, 1],  # Pista Arcobaleno (Normal / Glitch)
    "8014488A60F4428EEF52D01F8C5861CA9565E1CA": [0, 1],  # GCN Spiaggia di Peach (Normal / Glitch)
    "8C854B087417A92425110CC71E23C944D6997806": [-1],  # DS Cascate di Yoshi
    "071D697C4DDB66D3B210F36C7BF878502E79845B": [0, 1],  # SNES Valle fantasma 2 (Normal / Glitch)
    "49514E8F74FEA50E77273C0297086D67E58123E8": [-1],  # N64 Pista di Mario
    "BA9BCFB3731A6CB17DBA219A8D37EA4D52332256": [0, 1],  # N64 Circuito gelato (Normal / Glitch)
    "E8ED31605CC7D6660691998F024EED6BA8B4A33F": [0, 1],  # GBA Spiaggia Tipo Timido (Normal / Glitch)
    "BC038E163D21D9A1181B60CF90B4D03EFAD9E0C5": [-1],  # DS Borgo Delfino   
    "418099824AF6BF1CD7F8BB44F61E3A9CC3007DAE": [0, 1],  # GCN Stadio di Waluigi (Normal / Glitch)
    "4EC538065FDC8ACF49674300CBDEC5B80CC05A0D": [2, 16],  # DS Deserto Picchiasol (Non-SC / SC)
    "A4BEA41BE83D816F793F3FAD97D268F71AD99BF9": [2, 16],  # GBA Castello di Bowser 3 (Non-SC / SC)
    "692D566B05434D8C66A55BDFF486698E0FC96095": [2, 16, 1],  # N64 Viale Giungla DK (Non-SC / SC / Glitch)
    "1941A29AD2E7B7BBA8A29E6440C95EF5CF76B01D": [2, 16],  # GCN Circuito di Mario
    "077111B996E5C4F47D20EC29C2938504B53A8E76": [-1],  # SNES Circuito di Mario 3
    "F9A62BEF04CC8F499633E4023ACC7675A92771F0": [-1],  # DS Giardino di Peach
    "B036864CF0016BE0581449EF29FB52B2E58D78A4": [2, 16],  # GCN Montagne di DK (Non-SC / SC)
    "15B303B288F4707E5D0AF28367C8CE51CDEAB490": [2, 1],  # N64 Castello di Bowser (Normal / Glitch)
}

base_url = "https://tt.chadsoft.co.uk/"
modifiers_url = "?times=pb" #To get only the PBs
sa = gspread.service_account(filename="account_service_ghosts.json")
sh = sa.open("Cose Per Automatizzare Tempi TT")
wks = sh.worksheet("ProvaDatabase")
print("SUCCESSFULLY CONNECTED TO GOOGLE SHEETS IN %.2f SECONDS" % (time.time() - start_time))

def get_chadsoftAPI_request(ID):
    player_url = "players/" + ID[:2] + "/" + ID[2:] + ".json" #API structure to get Player info
    final_url = base_url + player_url + modifiers_url
    r = requests.get(final_url)
    time.sleep(TIME_WAIT_AFTER_GET)
    return r.text

def cd_get_last_modified(ID):
    player_url = "players/" + ID[:2] + "/" + ID[2:] + ".json" #API structure to get Player info
    final_url = base_url + player_url + modifiers_url
    r = requests.head(final_url)
    time.sleep(TIME_WAIT_AFTER_HEAD)
    return get_datetime_from_cd_date(r.headers["Last-Modified"])

def get_flap(ID, trackId, categoryId):
    return "WORK IN PROGRESS"

def get_datetime_from_cd_date(cd_date):
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

def get_ghost_mii(ghost):
    return "https://www.chadsoft.co.uk/time-trials" + ghost[:-3] + "mii"

def get_ghost_link(ghost):
    return "https://www.chadsoft.co.uk/time-trials" + ghost[:-3] + "html"

def get_vehicle(ID):
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

def get_driver(ID):
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

def get_controller(ID):
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

def get_gs_track_index(ID, categoryId):
    base = 0
    pos = list(RT_CATEGORIES.keys()).index(ID)
    if (categoryId == 2 or categoryId == 16) and 18 in RT_CATEGORIES[ID]:
        offset = 0
    else:
        try:
            offset = RT_CATEGORIES[ID].index(categoryId)
        except ValueError:
            return "INVALID_TRACK_CATEGORY"

    for value in list(RT_CATEGORIES.values())[:pos]:
        base += len(value)

    # print(f"ID: {ID}, cID: {categoryId}, base: {base}, offset: {offset}")
    return GS_START_INDEX + GS_TRACKS_INTERVAL * (base + offset)

def get_category(ID):
    if ID == -1 or ID == 0 or ID == 2:
        return "No-SC"
    elif ID == 1:
        return "Glitch"
    elif ID == 16:
        return "SC"
    else:
        return f"unknown{ID}"

def get_jolly_and_purify_ID(ID):
    if "*" in ID:
        return "".join(ID.split("*")), -ID.count("*")
    else:
        return "".join(ID.split("*")), 0

def get_timedelta_from_chadsoft(time):
    mins = int(time.split(':')[0])
    secs = int(time.split(':')[1].split('.')[0])
    ms = int(time.split(':')[1].split('.')[1])
    return datetime.timedelta(minutes=mins, seconds=secs, milliseconds=ms)

def get_gs_time_from_timedelta(time):
    time = str(time).split(':')[1:]
    if len(time[1]) == 2:
        time[1] += ".000"
        return time[0] + ':' + time[1]
    else:
        return time[0] + ':' + time[1][:-3]

def main():
    global wks
    full_gs = wks.get_values(value_render_option="FORMULA")
    IDs = [i[1] for i in full_gs[2:]]
    LMs = [i[2] for i in full_gs[2:]]
    row = 1 #Current row
    from_last_gs_update = 0
    for ID, LM in zip(IDs, LMs):
        row += 1
        if ID == "noID" or ID == "":
            print(f"[PLAYER SKIPPED AT ROW {row}]")
            continue
        ID, jolly = get_jolly_and_purify_ID(ID)
        
        print("[CHECKING] ID:", ID)

        cd_LM = cd_get_last_modified(ID)
        if LM != "" and datetime.datetime.fromisoformat(LM) > cd_LM:
            continue

        print("  [OUTDATED DATA FOUND] fetching player JSON from Chadsoft...")
        from_last_gs_update += 1
        player_data = json.loads(get_chadsoftAPI_request(ID))
        ghosts = player_data["ghosts"]
        gs_row_values = full_gs[row+jolly]
        for g in ghosts:
            if g["200cc"] == True or g["trackId"] not in list(RT_CATEGORIES.keys()):
                continue
            trackId = g["trackId"]
            try:
                categoryId = g["categoryId"]
            except:
                categoryId = -1
            gs_track_column = get_gs_track_index(trackId, categoryId)
            if gs_track_column == "INVALID_TRACK_CATEGORY":
                print("  [SKIPPING INVALID TRACK CATEGORY]", g["trackName"] + "; category:", get_category(categoryId))
                continue

            new_time = g["finishTimeSimple"]
            new_time = get_timedelta_from_chadsoft(new_time)
            try:
                old_time = gs_row_values[gs_track_column]
                old_time = get_timedelta_from_chadsoft(old_time)
            except:
                old_time = datetime.timedelta()
                
            if not (old_time == datetime.timedelta() or (full_gs[row+jolly][gs_track_column+3] == "TBA" and new_time <= old_time) or (full_gs[row+jolly][gs_track_column+3] != "TBA" and new_time < old_time)):
                continue

            new_time = get_gs_time_from_timedelta(new_time)
            
            print("  (NEW GHOSTS FOUND)", g["trackName"] + "; category:", get_category(categoryId) + "; time:", new_time)
            # Modify the values in the full_gs to the ones of the GHOST
            full_gs[row+jolly][gs_track_column-1] = "=IMAGE(\"" + get_ghost_mii(g["href"]) + "\")" # Mii image link, taken from chadsoft, mettere formula =IMAGE([link])
            full_gs[row+jolly][gs_track_column] = str(new_time)
            full_gs[row+jolly][gs_track_column+1] = g["dateSet"][:-1]
            full_gs[row+jolly][gs_track_column+2] = get_flap(ID, trackId, categoryId)
            full_gs[row+jolly][gs_track_column+3] = "=HYPERLINK(\"" + get_ghost_link(g["href"]) + "\"; \"Sì\")" # Ghost info, taken from chadsoft, mettere
            full_gs[row+jolly][gs_track_column+4] = get_vehicle(g["vehicleId"])
            full_gs[row+jolly][gs_track_column+5] = get_driver(g["driverId"])
            full_gs[row+jolly][gs_track_column+6] = get_controller(g["controller"])

        shifted_LM = cd_LM + datetime.timedelta(minutes=20)
        full_gs[row][2] = shifted_LM.isoformat()

        if from_last_gs_update >= NUM_ROWS_PARTIAL_UPDATE:
            from_last_gs_update = 0
            wks.update(full_gs, value_input_option="USER_ENTERED")
            full_gs = wks.get_values(value_render_option="FORMULA")
            print(f"[SUCCESSFUL] UPDATED {NUM_ROWS_PARTIAL_UPDATE} ROWS OF GOOGLE SHEETS, PROCEEDING WITH THE NEXT BLOCK...")

    wks.update(full_gs, value_input_option="USER_ENTERED")

if __name__ == "__main__":
    try:
        main()
        input("\n\n[SUCCESSFUL] The program terminated without errors. \n\nPress ENTER to exit...")
    except gspread.exceptions.APIError:
        print("\n\n----------------------------------------\nGOOGLE SHEET ERROR CODE 429: Quota of requests exceeded.")
        print("\nFirst try to rerun the program a couple of times. If it still happens execute the program with the Debug mode ON and send me the full output of the program on discord (Wol_loW#5995)")
        input("\n\nPress ENTER to exit...")
    except Exception:
        traceback.print_exc()
