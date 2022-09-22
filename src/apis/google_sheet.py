import gspread
import time
import datetime

# https://docs.google.com/spreadsheets/d/1pzvXA5NeHaqgaUe5ft_d4TauEbX9lVFxVp3dM51HsuA/edit#gid=1854354439

# Don't touch
GS_START_INDEX = 14
GS_TRACKS_INTERVAL = 11

CHECK_FULL_3LAP_NORMAL_COLUMN = 1
CHECK_FULL_3LAP_UNRESTRICTED_COLUMN = 2
CHECK_FULL_FLAP_NORMAL_COLUMN = 3
CHECK_FULL_FLAP_UNRESTRICTED_COLUMN = 4

ID_COLUMN = 5
LAST_MODIFIED_COLUMN = 6

GLITCH_ID = "01"
NORMAL_ID_C1 = "00"
NORMAL_ID_C2 = "02"
SHORTCUT_ID_C1 = "00"
SHORTCUT_ID_C2 = "02"
NORMAL_AND_SC_ID = "18"

#   Categories: Normal
#   ID          | 00
#
#   Categories: Normal, Shortcut
#   Normal ID   | 00
#   Shortcut ID | 02
#
#   Categories: Normal, Glitch
#   Normal ID   | 00
#   Glitch ID   | 01
#
#   Categories: Normal, Shortcut, Glitch
#   Normal ID   | 02
#   Shortcut ID | 00
#   Glitch ID   | 01
#
#   If we mix Normal and SC, we kept 18 as the custom ID because of legacy reasons, plus this way we make sure we won't have issues overlapping actual IDs.
#
#   It makes no sense but we gotta deal with it.

RT_CATEGORIES = {
    "1AE1A7D894960B38E09E7494373378D87305A163": [-1],        # LC                   Circuito di Luigi
    "90720A7D57A7C76E2347782F6BDE5D22342FB7DD": [-1],        # MMM                  Prateria verde
    "0E380357AFFCFD8722329994885699D9927F8276": [18, 1],     # MG    (NO-SC+SC/G)   Gola Fungo
    "1896AEA49617A571C66FF778D8F2ABBE9E5D7479": [2, 16],     # TF    (NO-SC/SC)     Fabbrica di Toad
    "7752BB51EDBC4A95377C0A05B0E0DA1503786625": [0, 1],      # MC    (NO-SC/G)      Circuito di Mario
    "E4BF364CB0C5899907585D731621CA930A4EF85C": [2, 16, 1],  # CM    (NO-SC/SC/G)   Outlet Cocco
    "B02ED72E00B400647BDA6845BE387C47D251F9D1": [-1],        # DKSC                 Pista Snowboard DK
    "D1A453B43D6920A78565E65A4597E353B177ABD0": [0, 1],      # WGM   (NO-SC/G)      Miniera d'oro di Wario
    "72D0241C75BE4A5EBD242B9D8D89B1D6FD56BE8F": [-1],        # DC                   Circuito di Daisy
    "52F01AE3AED1E0FA4C7459A648494863E83A548C": [0, 1],      # KC    (NO-SC/G)      Punta Koopa
    "48EBD9D64413C2B98D2B92E5EFC9B15ECD76FEE6": [0, 1],      # MT    (NO-SC/G)      Pista degli aceri
    "ACC0883AE0CE7879C6EFBA20CFE5B5909BF7841B": [2, 16, 1],  # GV    (NO-SC/SC/G)   Vulcano brontolone
    "38486C4F706395772BD988C1AC5FA30D27CAE098": [-1],        # DDR                  Rovine desertiche
    "B13C515475D7DA207DFD5BADD886986147B906FF": [-1],        # MH                   Autostrada lunare
    "B9821B14A89381F9C015669353CB24D7DB1BB25D": [2, 16],     # BC    (NO-SC/SC)     Castello di Bowser
    "FFE518915E5FAAA889057C8A3D3E439868574508": [0, 1],      # RR    (NO-SC/G)      Pista Arcoblaleno
    "8014488A60F4428EEF52D01F8C5861CA9565E1CA": [0, 1],      # rPB   (NO-SC/G)      GCN Spiaggia di Peach
    "8C854B087417A92425110CC71E23C944D6997806": [-1],        # rYF                  DS Cascate di Yoshi
    "071D697C4DDB66D3B210F36C7BF878502E79845B": [0, 1],      # rGV2  (NO-SC/G)      SNES Valle fantasma 2
    "49514E8F74FEA50E77273C0297086D67E58123E8": [-1],        # rMR                  N64 Pista di Mario
    "BA9BCFB3731A6CB17DBA219A8D37EA4D52332256": [0, 1],      # rSL   (NO-SC/G)      N64 Circuito Gelato
    "E8ED31605CC7D6660691998F024EED6BA8B4A33F": [0, 1],      # rSGB  (NO-SC/G)      GBA Spiaggia Tipo Timido
    "BC038E163D21D9A1181B60CF90B4D03EFAD9E0C5": [-1],        # rDS                  DS Borgo Delfino
    "418099824AF6BF1CD7F8BB44F61E3A9CC3007DAE": [0, 1],      # rWS   (NO-SC/G)      GCN Stadio di Waluigi
    "4EC538065FDC8ACF49674300CBDEC5B80CC05A0D": [2, 16],     # rDH   (NO-SC/SC)     DS Deserto Picchiasol
    "A4BEA41BE83D816F793F3FAD97D268F71AD99BF9": [2, 16],     # rBC3  (NO-SC/SC)     GBA Castello di Bowser 3
    "692D566B05434D8C66A55BDFF486698E0FC96095": [2, 16, 1],  # rDKJP (NO-SC/SC/G)   N64 Viale Giungla DK
    "1941A29AD2E7B7BBA8A29E6440C95EF5CF76B01D": [2, 16],     # rMC   (NO-SC/SC)     GCN Circuito di Mario
    "077111B996E5C4F47D20EC29C2938504B53A8E76": [-1],        # rMC3                 SNES Circuito di Mario 3
    "F9A62BEF04CC8F499633E4023ACC7675A92771F0": [-1],        # rPG                  DS Giardino di Peach
    "B036864CF0016BE0581449EF29FB52B2E58D78A4": [2, 16],     # rDKM  (NO-SC/SC)     GCN Montagne DK
    "15B303B288F4707E5D0AF28367C8CE51CDEAB490": [2, 1],      # rBC   (NO-SC/G)      N64 Castello di Bowser
}

def get_worksheet(service_key_filename: str, google_sheet_key: str, worksheet_name: str) -> gspread.worksheet.Worksheet: #TODO: Error handling in here
    """Connect to the Google Sheets API with gspread, using a service_accout key, the sheet's key and the worksheet's name.

    return: Worksheet object of the wanted sheet
    """
    start_time = time.time()
    sa = gspread.service_account(filename=service_key_filename)
    sh = sa.open_by_key(google_sheet_key)
    return sh.worksheet(worksheet_name), f"SUCCESSFULLY CONNECTED TO GOOGLE SHEETS IN {time.time() - start_time} SECONDS"

def get_track_column(ID: str, categoryId: int) -> int:
    """Calculate the column of the track using the track ID and the category ID, based on the tracks in RT_CATEGORIES.
    The starting offset is decided by GS_START_INDEX and the space between each track is controlled by GS_TRACKS_INTERVAL.

    return: column index of the track
    """
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
    return GS_START_INDEX + GS_TRACKS_INTERVAL * (base + offset)

def get_timedelta_from_timestring(time: str) -> datetime.timedelta:
    if "°" in time: time = time[:-1]
    mins = int(time.split(':')[0])
    secs = int(time.split(':')[1].split('.')[0])
    ms = int(time.split(':')[1].split('.')[1])
    return datetime.timedelta(minutes=mins, seconds=secs, milliseconds=ms)

def get_timestring_from_timedelta(time: datetime.timedelta, categoryId: int) -> str:
    time = str(time).split(':')[1:]
    if categoryId not in [-1, 0, 2, 18]: jolly = "°"
    else: jolly = ""
    if len(time[1]) == 2:
        time[1] += ".000"
        return f"{time[0]}:{time[1]}{jolly}"
    else:
        return f"{time[0]}:{time[1][:-3]}{jolly}"

def get_jolly_and_purify_ID(ID: str) -> (str, int):
    if "*" in ID:
        return ("".join(ID.split("*")), -ID.count("*"))
    else:
        return ("".join(ID.split("*")), 0)

def get_value_safely(sheet: list[list[any], ...], row: int, column: int) -> str:
    """Get value of worksheet at a specific row and column.

    If worksheet cell is empty, return: empty string.
    Otherwise, return: cell value
    """
    try:
        value = str(sheet[row][column])
    except:
        value = ""
    finally:
        return value

def get_all_values(wks: gspread.worksheet.Worksheet, render_option: str = "FORMULA") -> list[list[any, ...]]:
    """Fetch all the values from the worksheet, using a certain option.

    For more information about the option: https://developers.google.com/sheets/api/reference/rest/v4/ValueRenderOption

    Default option is FORMULA.

    return: all cell values of the worksheet
    """
    values = wks.get_values(value_render_option=render_option)
    return values

def set_all_values(wks: gspread.worksheet.Worksheet, data: list[list[any], ...], input_option: str = "USER_ENTERED") -> None:
    """Update the worksheet with the new values using a certain option. 

    For more information about the option: https://developers.google.com/sheets/api/reference/rest/v4/ValueInputOption

    Default option is USER_ENTERED.

    If the values passed are smaller than the worksheet, the values will be inserted starting from the top-left corner.

    return: nothing
    """
    wks.update(data, value_input_option=input_option)

def get_date_from_gs_timestamp(time_stamp: str) -> datetime.timedelta:
    """When fetching a string from google sheets formatted like YYYY-MM-DD, it will convert it to the distance in days from the date 1900-1-1 (for some reason it's 2 days behind, so the distance is calculated from the date 1899-12-30)

    If the time is already correctly formatted, return: time_stamp as it was.
    Otherwise, return: time converted in the format YYYY-MM-DD
    If the value is "Sconosciuto", return: "Sconosciuto"

    REIMPLEMENT THIS IN A BETTER WAY PLS
    """
    # This is surely an awful way to check if the format's correct, GO LEARN REGEXs
    try:
        int(time_stamp)
        try:
            assert(len(time_stamp) == 10)
            assert(len(time_stamp.split("-")[0]) == 4)
            assert(len(time_stamp.split("-")[1]) == 2)
            assert(len(time_stamp.split("-")[2]) == 2)
            int(time_stamp.split("-")[0])
            int(time_stamp.split("-")[1])
            int(time_stamp.split("-")[2])
        except:
            base_time = datetime.datetime(1899, 12, 30)
            return (base_time + datetime.timedelta(days=int(time_stamp))).isoformat()[:10]
        else:
            return time_stamp
    except:
        return time_stamp
