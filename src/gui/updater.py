import json
import datetime
from operator import index
from textwrap import indent
from tracemalloc import start
import gspread
import os
import json
import time
from PySide6.QtCore import QThread, Signal
from shutil import rmtree

from apis.mii2studio import mii2studio as m2s
from apis import google_sheet as gs
from apis import chadsoft as cd
from apis.chadsoft import RT_TRACKS

SERVICE_KEY_FILENAME = "mkwii-ita-auto-tt-service-key.json"
GOOGLE_SHEET_KEY = "1pzvXA5NeHaqgaUe5ft_d4TauEbX9lVFxVp3dM51HsuA"
WORKSHEET_NAME = "Dati"

class Updater(QThread):

    # 0 = update everything
    # 1 = update only 3laps
    # 2 = update only unrestricted
    # 3 = update nothing
    mode = 0

    display_msg = Signal(str)

    stopped = Signal()

    def __init__(self, parent = None):
        super(Updater, self).__init__(parent)
        self.setOptions(10, True, True, True, 10, True, True, True, True)

    def stop_msg(self):
        self.display_msg.emit("\n\n[OPERATION STOPPED]")

    def setOptions(self, track_skip_3lap:int, rkg_dl_3lap: bool, check_2_3lap: bool, check_3_3lap: bool, track_skip_flap: int, rkg_dl_flap: bool, check_2_flap: bool, check_3_flap: bool, check_print_info_unr: bool):
        self.track_skip_3lap = track_skip_3lap
        self.rkg_dl_3lap = rkg_dl_3lap
        self.check_2_3lap = check_2_3lap
        self.check_3_3lap = check_3_3lap
        self.track_skip_flap = track_skip_flap
        self.rkg_dl_flap = rkg_dl_flap
        self.check_2_flap = check_2_flap
        self.check_3_flap = check_3_flap
        self.check_print_info_unr = check_print_info_unr

    def setMode(self, active_3lap: bool, active_flap: bool, active_unr: bool) -> None:
        self.active_3lap = active_3lap
        self.active_flap = active_flap
        self.active_unr = active_unr

    def update_flaps(self, wks: gspread.worksheet.Worksheet = None):
        if self.isInterruptionRequested():
            self.stopped.emit()
            try: rmtree("tmp/")
            except: pass
            return -1
        self.display_msg.emit("[FLAPs UPDATE STARTED]")
        log_out = ""
        total_time = 0
        if wks == None: 
            wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
            if feedback: self.display_msg.emit(feedback)
        full_gs = gs.get_all_values(wks)
        gs_track_column = 2 + gs.GS_START_INDEX
        
        start_offset = self.track_skip_flap
        t_display = start_offset
   
        IDs = [i[gs.ID_COLUMN] for i in full_gs[2:]]
        filtered_IDs_tuples = list(map(gs.get_jolly_and_purify_ID,IDs))
        id_jolly = []
        filtered_IDs = []
        unfiltered_IDs = []
        for i in filtered_IDs_tuples:
            if i[0] != "noID":
                filtered_IDs.append(i[0])
                id_jolly.append(i[1])
            unfiltered_IDs.append(i[0])

        tracks = list(RT_TRACKS.keys())

        while start_offset > 0: # reminder: do -1 for user input 
            print(str(gs_track_column) + " | https://chadsoft.co.uk/time-trials/leaderboard/" + tracks[0] + "00-fast-lap.html")
            gs_track_column += gs.GS_TRACKS_INTERVAL * len(RT_TRACKS[tracks[0]])
            if start_offset==3:
                gs_track_column = gs_track_column - gs.GS_TRACKS_INTERVAL
            start_offset = start_offset -1           
            tracks.pop(0)     

        for track_link in tracks:
            category_ids = RT_TRACKS[track_link]
            cat_n = 0
            t_display += 1
            for category_id in category_ids:
                row = 1 #Current row
                start_time = time.time()
                self.display_msg.emit("Connecting to Chadsoft...")
                cat_name = str(cd.get_category_2(track_link,category_id))
                if track_link == "02/0E380357AFFCFD8722329994885699D9927F8276/" and category_id == "00":
                    gs_track_column = gs_track_column - gs.GS_TRACKS_INTERVAL
                    cat_n = cat_n -1
                if self.isInterruptionRequested():
                    self.stopped.emit()
                    try:
                        rmtree("tmp/")
                    except:
                        pass
                    return -1
                track_lb = cd.get_leaderboard_page(track_link,category_id,flap=True) # Could do Async requests or put the requests on another thread but Chadsoft.co.uk is too bad of a site for it to work properly
                track_name = track_lb["name"]
                track_lb = track_lb["ghosts"]
                self.display_msg.emit(f"Connected to the {track_name} {cat_name} leaderboard in {time.time()-start_time}.")
                log_out += f"Connected to the {track_name} {cat_name} leaderboard in {time.time()-start_time}.\n"
                start_time_local = time.time()
                for player_info in track_lb:
                    if player_info["playerId"] in filtered_IDs:
                        ID = player_info["playerId"]
                        jolly = id_jolly[filtered_IDs.index(ID)]
                        row = unfiltered_IDs.index(ID)+2
                        if self.isInterruptionRequested():
                            with open("log_flap.txt","w") as f:
                                f.write(log_out)
                            self.stopped.emit()
                            try:
                                rmtree("tmp/")
                            except:
                                pass
                            return -1

                        player_name = full_gs[row][0]
                        self.display_msg.emit(f"Player Found: {player_name}, ID: {ID}, Row: {row+1}")

                        if self.isInterruptionRequested():
                            with open("log_flap.txt","w") as f:
                                f.write(log_out)
                            self.stopped.emit()
                            try:
                                rmtree("tmp/")
                            except:
                                pass
                            return -1
                        new_time = player_info["bestSplitSimple"]
                        new_time = gs.get_timedelta_from_timestring(new_time)
                        gs_row_values = full_gs[row+jolly]
                        try:
                            old_time = gs_row_values[gs_track_column]
                            old_time = gs.get_timedelta_from_timestring(old_time)
                        except:
                            old_time = datetime.timedelta()
                        if not (old_time == datetime.timedelta() 
                            or (full_gs[row+jolly][gs_track_column+2] == "TBA" and new_time <= old_time)
                            or (full_gs[row+jolly][gs_track_column+2] == "No" and new_time <= old_time)
                            or (full_gs[row+jolly][gs_track_column+2] == "" and new_time <= old_time) 
                            or new_time < old_time):
                                continue
                        log_out += f"Player Found: {player_name}, ID: {ID}, Row: {row+1}\n"
                        new_link = "https://chadsoft.co.uk/time-trials" + player_info["href"][:-3]+"html"
                        new_time = gs.get_timestring_from_timedelta_2(new_time,cat_n)
                        self.display_msg.emit("  (NEW GHOSTS FOUND), " + track_name + ", category: " + cat_name + ", time: " + new_time + ", ghost_link: "+ new_link)
                        log_out += "  (NEW GHOSTS FOUND), " + track_name + ", category: " + cat_name + ", time: " + new_time + ", ghost_link: "+ new_link+"\n"
                        new_cell_link = "=HYPERLINK(\""+new_link+"\";\"Sì\")"
                        old_flap_vid_link = full_gs[row+jolly][gs_track_column+4] # Used to warn about possibly overwriting a TBA video
                        if old_flap_vid_link != "":
                            self.display_msg.emit(f"      [Old Video Link found] {old_flap_vid_link}")
                            log_out += f"      [OLD VIDEO LINK FOUND] {old_flap_vid_link}\n"
                        full_gs[row+jolly][gs_track_column] = new_time
                        full_gs[row+jolly][gs_track_column+2] = new_cell_link
                        full_gs[row+jolly][gs_track_column+4] = ""
                        if self.rkg_dl_flap:
                            rkg = cd.get_ghost_rkg(player_info["href"])
                            try: os.mkdir("ghosts_flap")
                            except: pass
                            try: os.mkdir("ghosts_flap/"+track_name)
                            except: pass
                            with open("ghosts_flap/"+track_name+"/"+player_name.replace("*","")+".rkg","wb") as f:
                                f.write(rkg)
                self.display_msg.emit(f"{track_name} {cat_name} took {time.time()-start_time_local} to update")
                total_time += time.time()-start_time
                self.display_msg.emit(f"Total Time Elapsed: {total_time}\n")
                log_out += f"Total Time Elapsed: {total_time}\n"
                gs_track_column += gs.GS_TRACKS_INTERVAL
                cat_n += 1
            gs.set_all_values(wks, full_gs)
            full_gs = gs.get_all_values(wks)
            self.display_msg.emit(f"[SUCCESSFUL] Updated ({t_display}) {track_name}, proceeding with the next track...")
            with open("log_flap.txt","w") as f:
                f.write(log_out)
        self.display_msg.emit("[FLAPS UPDATE FINISHED]")

    def update_3laps(self, wks: gspread.worksheet.Worksheet = None):
        if self.isInterruptionRequested():
            self.stopped.emit()
            try: rmtree("tmp/")
            except: pass
            return -1
        self.display_msg.emit("\n[3LAPs UPDATE STARTED]")
        total_time = 0
        log_out = ""
        try: os.mkdir("tmp")
        except: pass
        if wks == None: 
            wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
            if feedback:
                self.display_msg.emit(feedback)
        full_gs = gs.get_all_values(wks)
        gs_track_column = gs.GS_START_INDEX
        IDs = [i[gs.ID_COLUMN] for i in full_gs[2:]]
        row = 1 #Current row
        
        start_offset = self.track_skip_3lap
        t_display = start_offset
   
        IDs = [i[gs.ID_COLUMN] for i in full_gs[2:]]
        filtered_IDs_tuples = list(map(gs.get_jolly_and_purify_ID,IDs))
        id_jolly = []
        filtered_IDs = []
        unfiltered_IDs = []
        for i in filtered_IDs_tuples:
            if i[0] != "noID":
                filtered_IDs.append(i[0])
                id_jolly.append(i[1])
            unfiltered_IDs.append(i[0])

        tracks = list(RT_TRACKS.keys())

        while start_offset > 0: # reminder: do -1 for user input 
            print(str(gs_track_column) + " | https://chadsoft.co.uk/time-trials/leaderboard/" + tracks[0] + "00.html")
            gs_track_column += gs.GS_TRACKS_INTERVAL * len(RT_TRACKS[tracks[0]])
            if start_offset==3:
                gs_track_column = gs_track_column - gs.GS_TRACKS_INTERVAL
            start_offset = start_offset -1           
            tracks.pop(0)     

        for track_link in tracks:
            category_ids = RT_TRACKS[track_link]
            cat_n = 0
            t_display += 1
            for category_id in category_ids:
                row = 1 #Current row
                start_time = time.time()
                self.display_msg.emit("Connecting to Chadsoft...")
                cat_name = str(cd.get_category_2(track_link,category_id))
                if track_link == "02/0E380357AFFCFD8722329994885699D9927F8276/" and category_id == "00":
                    gs_track_column = gs_track_column - gs.GS_TRACKS_INTERVAL
                    cat_n = cat_n -1
                if self.isInterruptionRequested():
                    self.stopped.emit()
                    try: rmtree("tmp/")
                    except: pass
                    return -1
                track_lb = cd.get_leaderboard_page(track_link,category_id,flap=False) # Could do Async requests or put the requests on another thread but Chadsoft.co.uk is too bad of a site for it to work properly
                track_name = track_lb["name"]
                track_lb = track_lb["ghosts"]
                self.display_msg.emit(f"Connected to the {track_name} {cat_name} leaderboard in {time.time()-start_time}.")
                log_out += f"Connected to the {track_name} {cat_name} leaderboard in {time.time()-start_time}.\n"
                start_time_local = time.time()
                for player_info in track_lb:
                    if player_info["playerId"] in filtered_IDs:
                        ID = player_info["playerId"]
                        jolly = id_jolly[filtered_IDs.index(ID)]
                        row = unfiltered_IDs.index(ID)+2
                        if self.isInterruptionRequested():
                            with open("log_3lap.txt","w") as f: f.write(log_out)
                            self.stopped.emit()
                            try: rmtree("tmp/")
                            except: pass
                            return -1

                        player_name = full_gs[row][0]
                        self.display_msg.emit(f"Player Found: {player_name}, ID: {ID}, Row: {row+1}")

                        if self.isInterruptionRequested():
                            with open("log_3lap.txt","w") as f: f.write(log_out)
                            self.stopped.emit()
                            try: rmtree("tmp/")
                            except: pass
                            return -1
                        new_time = player_info["finishTimeSimple"]
                        new_time = gs.get_timedelta_from_timestring(new_time)
                        gs_row_values = full_gs[row+jolly]
                        try:
                            old_time = gs_row_values[gs_track_column]
                            old_time = gs.get_timedelta_from_timestring(old_time)
                        except:
                            old_time = datetime.timedelta()
                        if not (old_time == datetime.timedelta() 
                            or (full_gs[row+jolly][gs_track_column+3] == "TBA" and new_time <= old_time)
                            or (full_gs[row+jolly][gs_track_column+3] == "No" and new_time <= old_time)
                            or (full_gs[row+jolly][gs_track_column+3] == "" and new_time <= old_time) 
                            or new_time < old_time):
                                continue
                        log_out += f"Player Found: {player_name}, ID: {ID}, Row: {row+1}\n"
                        new_link = "https://chadsoft.co.uk/time-trials" + player_info["href"][:-3]+"html"
                        new_time = gs.get_timestring_from_timedelta_2(new_time,cat_n)
                        self.display_msg.emit("  (NEW GHOSTS FOUND), " + track_name + ", category: " + cat_name + ", time: " + new_time + ", ghost_link: "+ new_link)
                        log_out += "  (NEW GHOSTS FOUND), " + track_name + ", category: " + cat_name + ", time: " + new_time + ", ghost_link: "+ new_link+"\n"
                        new_cell_link = "=HYPERLINK(\""+new_link+"\";\"Sì\")"
                        old_flap_vid_link = full_gs[row+jolly][gs_track_column+5] # Used to warn about possibly overwriting a TBA video
                        rkg_info = cd.get_ghost_rkg(player_info["href"])
                        if old_flap_vid_link != "":
                            self.display_msg.emit(f"      [Old Video Link found] {old_flap_vid_link}")
                            log_out += f"      [OLD VIDEO LINK FOUND] {old_flap_vid_link}\n"
                        full_gs[row+jolly][gs_track_column-1] = m2s.genRender(rkg_info)
                        full_gs[row+jolly][gs_track_column] = new_time
                        full_gs[row+jolly][gs_track_column+1] = cd.get_date_from_rkg(rkg_info)
                        full_gs[row+jolly][gs_track_column+3] = new_cell_link
                        full_gs[row+jolly][gs_track_column+5] = ""
                        full_gs[row+jolly][gs_track_column+7] = cd.get_driver(player_info["driverId"])
                        full_gs[row+jolly][gs_track_column+8] = cd.get_vehicle(player_info["vehicleId"])
                        full_gs[row+jolly][gs_track_column+9] = cd.get_controller(player_info["controller"])
                        if self.rkg_dl_3lap:
                            try: os.mkdir("ghosts_3lap")
                            except: pass
                            try: os.mkdir("ghosts_3lap/"+track_name)
                            except: pass
                            with open("ghosts_3lap/"+track_name+"/"+player_name.replace("*","")+".rkg","wb") as f:
                                f.write(rkg_info)
                self.display_msg.emit(f"{track_name} {cat_name} took {time.time()-start_time_local} to update")
                total_time += time.time()-start_time
                self.display_msg.emit(f"Total Time Elapsed: {total_time}")
                log_out += f"Total Time Elapsed: {total_time}\n"
                gs_track_column += gs.GS_TRACKS_INTERVAL
                cat_n += 1
            gs.set_all_values(wks, full_gs)
            full_gs = gs.get_all_values(wks)
            self.display_msg.emit(f"[SUCCESSFUL] Updated ({t_display}) {track_name}, proceeding with the next track...")
            with open("log_3lap.txt","w") as f:
                f.write(log_out)
        gs.set_all_values(wks, full_gs)
        with open("log_3lap.txt","w") as f:
            f.write(log_out)
        self.display_msg.emit("\n[3LAPs UPDATE FINISHED]")

    def update_unrestricted_and_checks(self, wks: gspread.worksheet.Worksheet = None):
        self.display_msg.emit("\n[UNRESTRICTED UPDATE STARTED]")
        if wks == None: 
            wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
            if feedback:
                self.display_msg.emit(feedback)
        full_gs = gs.get_all_values(wks)
        track_interval = gs.GS_TRACKS_INTERVAL

        # After everything, check the unrestricted
        names = [i[0] for i in full_gs[2:]]
        row = 1

        for name in names:
            if "*" in name:
                continue
            if self.isInterruptionRequested():
                self.stopped.emit()
                return -1
            current_column = gs.GS_START_INDEX
            row += 1
            current_row = full_gs[row]

            complete_3lap_norm = True
            complete_3lap_unr = True
            complete_flap_norm = True
            complete_flap_unr = True

            for track_num, track_categories in list(enumerate(cd.RT_TRACKS.values())):
                if self.isInterruptionRequested():
                    gs.set_all_values(wks, full_gs)
                    self.stopped.emit()
                    return -1
                length_track = len(track_categories)
                if track_num == 2: length_track -= 1
                if length_track == 1:   # No-SC, easy check
                    stuff_to_do_check = [0,0,0,0,0]
                    current_3lap_time = current_row[current_column]
                    current_flap_time = current_row[current_column+2]

                    if current_3lap_time == "": complete_3lap_norm, complete_3lap_unr = False, False
                    elif current_3lap_time != "" and "sì" in current_row[current_column+3].lower():
                        
                        if "chadsoft" in current_row[current_column-1].lower() or current_row[current_column-1] == "": current_row[current_column-1] = stuff_to_do_check[0] = 1
                        if str(current_row[current_column+1]).lower() == "sconosciuto" or str(current_row[current_column+1]).lower() == "": stuff_to_do_check[1] = 1
                        if current_row[current_column+7] == "" or current_row[current_column+7].lower() == "sconosciuto": stuff_to_do_check[2] = 1
                        if current_row[current_column+8] == "" or current_row[current_column+8].lower() == "sconosciuto": stuff_to_do_check[3] = 1
                        if current_row[current_column+9] == "" or current_row[current_column+9].lower() == "sconosciuto": stuff_to_do_check[4] = 1

                    if stuff_to_do_check != [0,0,0,0,0]:

                        if "chadsoft" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                        elif "discord" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3].split("\"")[1])
                        elif "maschell" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3].split("\"")[1])
                        else: pass

                        if stuff_to_do_check[0] == 1: current_row[current_column-1] = m2s.genRender(rkg)
                        if stuff_to_do_check[1] == 1: current_row[current_column+1] = cd.get_date_from_rkg(rkg)
                        if stuff_to_do_check[2] == 1: current_row[current_column+7] = cd.get_driver(cd.get_driver_id_bin(rkg))
                        if stuff_to_do_check[3] == 1: current_row[current_column+8] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                        if stuff_to_do_check[4] == 1: current_row[current_column+9] = cd.get_controller(cd.get_controller_id_bin(rkg))

                    if current_flap_time == "": complete_flap_norm, complete_flap_unr = False, False
                    current_column += track_interval
                
                elif length_track == 2:
                    stuff_to_do_check = [0,0,0,0,0,0,0,0,0,0]
                    current_3lap_time = current_row[current_column]
                    current_flap_time = current_row[current_column+2]
                    sc_3lap_time = current_row[current_column+track_interval]
                    sc_flap_time = current_row[current_column+2+track_interval]
                    if current_3lap_time == "" and sc_3lap_time == "": complete_3lap_norm, complete_3lap_unr = False, False
                    elif current_3lap_time == "" and sc_3lap_time != "":
                        complete_3lap_norm = False
                        if "sì" in current_row[current_column+3+track_interval].lower():
                            if "chadsoft" in current_row[current_column-1+track_interval].lower() or current_row[current_column-1+track_interval] == "": current_row[current_column-1+track_interval] = stuff_to_do_check[5] = 1
                            if str(current_row[current_column+1+track_interval]).lower() == "sconosciuto" or str(current_row[current_column+1+track_interval]).lower(): stuff_to_do_check[6] = 1
                            if current_row[current_column+7+track_interval] == "" or current_row[current_column+7+track_interval].lower() == "sconosciuto": stuff_to_do_check[7] = 1
                            if current_row[current_column+8+track_interval] == "" or current_row[current_column+8+track_interval].lower() == "sconosciuto": stuff_to_do_check[8] = 1
                            if current_row[current_column+9+track_interval] == "" or current_row[current_column+9+track_interval].lower() == "sconosciuto": stuff_to_do_check[9] = 1

                        if stuff_to_do_check != [0,0,0,0,0,0,0,0,0,0]:
                            if "chadsoft" in current_row[current_column+3+track_interval].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3+track_interval].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                            elif "discord" in current_row[current_column+3+track_interval].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3+track_interval].split("\"")[1])
                            elif "maschell" in current_row[current_column+3+track_interval].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3+track_interval].split("\"")[1])
                            else: pass

                            if stuff_to_do_check[5] == 1: current_row[current_column-1+track_interval] = m2s.genRender(rkg)
                            if stuff_to_do_check[6] == 1: current_row[current_column+1+track_interval] = cd.get_date_from_rkg(rkg)
                            if stuff_to_do_check[7] == 1: current_row[current_column+7+track_interval] = cd.get_driver(cd.get_driver_id_bin(rkg))
                            if stuff_to_do_check[8] == 1: current_row[current_column+8+track_interval] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                            if stuff_to_do_check[9] == 1: current_row[current_column+9+track_interval] = cd.get_controller(cd.get_controller_id_bin(rkg))

                    elif current_3lap_time != "" and sc_3lap_time == "":
                        if "sì" in current_row[current_column+3].lower():
                            if "chadsoft" in current_row[current_column-1].lower() or current_row[current_column-1] == "": current_row[current_column-1] = stuff_to_do_check[0] = 1
                            if str(current_row[current_column+1]).lower() == "sconosciuto" or str(current_row[current_column+1]).lower() == "": stuff_to_do_check[1] = 1
                            if current_row[current_column+7] == "" or current_row[current_column+7].lower() == "sconosciuto": stuff_to_do_check[2] = 1
                            if current_row[current_column+8] == "" or current_row[current_column+8].lower() == "sconosciuto": stuff_to_do_check[3] = 1
                            if current_row[current_column+9] == "" or current_row[current_column+9].lower() == "sconosciuto": stuff_to_do_check[4] = 1

                        if stuff_to_do_check != [0,0,0,0,0,0,0,0,0,0]:
                            if "chadsoft" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                            elif "discord" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3].split("\"")[1])
                            elif "maschell" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3].split("\"")[1])
                            else: pass

                            if stuff_to_do_check[0] == 1: current_row[current_column-1] = m2s.genRender(rkg)
                            if stuff_to_do_check[1] == 1: current_row[current_column+1] = cd.get_date_from_rkg(rkg)
                            if stuff_to_do_check[2] == 1: current_row[current_column+7] = cd.get_driver(cd.get_driver_id_bin(rkg))
                            if stuff_to_do_check[3] == 1: current_row[current_column+8] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                            if stuff_to_do_check[4] == 1: current_row[current_column+9] = cd.get_controller(cd.get_controller_id_bin(rkg))

                        current_row[current_column-1] = current_row[current_column-1]
                        current_row[current_column]   = current_row[current_column]
                        current_row[current_column+1] = current_row[current_column+1]
                        current_row[current_column+3] = current_row[current_column+3]
                        current_row[current_column+5] = current_row[current_column+5]
                        current_row[current_column+7] = current_row[current_column+7]
                        current_row[current_column+8] = current_row[current_column+8]
                        current_row[current_column+9] = current_row[current_column+9]
                        
                    elif current_3lap_time != "" and sc_3lap_time != "":
                        if gs.get_timedelta_from_timestring(current_3lap_time) < gs.get_timedelta_from_timestring(sc_3lap_time):
                            if "sì" in current_row[current_column+3].lower():
                                if "chadsoft" in current_row[current_column-1].lower() or current_row[current_column-1] == "": current_row[current_column-1] = stuff_to_do_check[0] = 1
                                if str(current_row[current_column+1]).lower() == "sconosciuto" or str(current_row[current_column+1]).lower() == "": stuff_to_do_check[1] = 1
                                if current_row[current_column+7] == "" or current_row[current_column+7].lower() == "sconosciuto": stuff_to_do_check[2] = 1
                                if current_row[current_column+8] == "" or current_row[current_column+8].lower() == "sconosciuto": stuff_to_do_check[3] = 1
                                if current_row[current_column+9] == "" or current_row[current_column+9].lower() == "sconosciuto": stuff_to_do_check[4] = 1

                            if stuff_to_do_check != [0,0,0,0,0,0,0,0,0,0]:
                                if "chadsoft" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                                elif "discord" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3].split("\"")[1])
                                elif "maschell" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3].split("\"")[1])
                                else: pass

                                if stuff_to_do_check[0] == 1: current_row[current_column-1] = m2s.genRender(rkg)
                                if stuff_to_do_check[1] == 1: current_row[current_column+1] = cd.get_date_from_rkg(rkg)
                                if stuff_to_do_check[2] == 1: current_row[current_column+7] = cd.get_driver(cd.get_driver_id_bin(rkg))
                                if stuff_to_do_check[3] == 1: current_row[current_column+8] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                                if stuff_to_do_check[4] == 1: current_row[current_column+9] = cd.get_controller(cd.get_controller_id_bin(rkg))
                                
                            current_row[current_column-1+track_interval] = current_row[current_column-1]
                            current_row[current_column+track_interval]   = current_row[current_column]
                            current_row[current_column+1+track_interval] = current_row[current_column+1]
                            current_row[current_column+3+track_interval] = current_row[current_column+3]
                            current_row[current_column+5+track_interval] = current_row[current_column+5]
                            current_row[current_column+7+track_interval] = current_row[current_column+7]
                            current_row[current_column+8+track_interval] = current_row[current_column+8]
                            current_row[current_column+9+track_interval] = current_row[current_column+9]
                        elif gs.get_timedelta_from_timestring(current_3lap_time) == gs.get_timedelta_from_timestring(sc_3lap_time):
                            if "sì" in current_row[current_column+3].lower():
                                if "chadsoft" in current_row[current_column-1].lower() or current_row[current_column-1] == "": current_row[current_column-1] = stuff_to_do_check[0] = 1
                                if str(current_row[current_column+1]).lower() == "sconosciuto" or str(current_row[current_column+1]).lower() == "": stuff_to_do_check[1] = 1
                                if current_row[current_column+7] == "" or current_row[current_column+7].lower() == "sconosciuto": stuff_to_do_check[2] = 1
                                if current_row[current_column+8] == "" or current_row[current_column+8].lower() == "sconosciuto": stuff_to_do_check[3] = 1
                                if current_row[current_column+9] == "" or current_row[current_column+9].lower() == "sconosciuto": stuff_to_do_check[4] = 1

                            if stuff_to_do_check != [0,0,0,0,0,0,0,0,0,0]:
                                if "chadsoft" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                                elif "discord" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3].split("\"")[1])
                                elif "maschell" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3].split("\"")[1])
                                else: pass

                                if stuff_to_do_check[0] == 1: current_row[current_column-1] = m2s.genRender(rkg)
                                if stuff_to_do_check[1] == 1: current_row[current_column+1] = cd.get_date_from_rkg(rkg)
                                if stuff_to_do_check[2] == 1: current_row[current_column+7] = cd.get_driver(cd.get_driver_id_bin(rkg))
                                if stuff_to_do_check[3] == 1: current_row[current_column+8] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                                if stuff_to_do_check[4] == 1: current_row[current_column+9] = cd.get_controller(cd.get_controller_id_bin(rkg))
                                
                            current_row[current_column-1+track_interval] = current_row[current_column-1]
                            current_row[current_column+track_interval]   = current_row[current_column]
                            current_row[current_column+1+track_interval] = current_row[current_column+1]
                            current_row[current_column+3+track_interval] = current_row[current_column+3]
                            current_row[current_column+7+track_interval] = current_row[current_column+7]
                            current_row[current_column+8+track_interval] = current_row[current_column+8]
                            current_row[current_column+9+track_interval] = current_row[current_column+9]

                            if current_row[current_column+5] == "" : current_row[current_column+5] = current_row[current_column+5+track_interval]
                            elif current_row[current_column+5+track_interval] == "" : current_row[current_column+5+track_interval] = current_row[current_column+5]

                        else:
                            if "sì" in current_row[current_column+3].lower():
                                if "chadsoft" in current_row[current_column-1].lower() or current_row[current_column-1] == "": current_row[current_column-1] = stuff_to_do_check[0] = 1
                                if str(current_row[current_column+1]).lower() == "sconosciuto" or str(current_row[current_column+1]).lower() == "": stuff_to_do_check[1] = 1
                                if current_row[current_column+7] == "" or current_row[current_column+7].lower() == "sconosciuto": stuff_to_do_check[2] = 1
                                if current_row[current_column+8] == "" or current_row[current_column+8].lower() == "sconosciuto": stuff_to_do_check[3] = 1
                                if current_row[current_column+9] == "" or current_row[current_column+9].lower() == "sconosciuto": stuff_to_do_check[4] = 1

                            if "sì" in current_row[current_column+3+track_interval].lower():
                                if "chadsoft" in current_row[current_column-1+track_interval].lower() or current_row[current_column-1+track_interval] == "": current_row[current_column-1+track_interval] = stuff_to_do_check[5] = 1
                                if str(current_row[current_column+1+track_interval]).lower() == "sconosciuto" or str(current_row[current_column+1+track_interval]).lower(): stuff_to_do_check[6] = 1
                                if current_row[current_column+7+track_interval] == "" or current_row[current_column+7+track_interval].lower() == "sconosciuto": stuff_to_do_check[7] = 1
                                if current_row[current_column+8+track_interval] == "" or current_row[current_column+8+track_interval].lower() == "sconosciuto": stuff_to_do_check[8] = 1
                                if current_row[current_column+9+track_interval] == "" or current_row[current_column+9+track_interval].lower() == "sconosciuto": stuff_to_do_check[9] = 1

                            if stuff_to_do_check != [0,0,0,0,0,0,0,0,0,0]:
                                if "chadsoft" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                                elif "discord" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3].split("\"")[1])
                                elif "maschell" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3].split("\"")[1])
                                else: pass
                                
                                if "chadsoft" in current_row[current_column+3+track_interval].lower(): rkg_sc = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3+track_interval].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                                elif "discord" in current_row[current_column+3+track_interval].lower(): rkg_sc = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3+track_interval].split("\"")[1])
                                elif "maschell" in current_row[current_column+3+track_interval].lower(): rkg_sc = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3+track_interval].split("\"")[1])
                                else: pass

                                if stuff_to_do_check[0] == 1: current_row[current_column-1] = m2s.genRender(rkg)
                                if stuff_to_do_check[1] == 1: current_row[current_column+1] = cd.get_date_from_rkg(rkg)
                                if stuff_to_do_check[2] == 1: current_row[current_column+7] = cd.get_driver(cd.get_driver_id_bin(rkg))
                                if stuff_to_do_check[3] == 1: current_row[current_column+8] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                                if stuff_to_do_check[4] == 1: current_row[current_column+9] = cd.get_controller(cd.get_controller_id_bin(rkg))
                                if stuff_to_do_check[5] == 1: current_row[current_column-1+track_interval] = m2s.genRender(rkg_sc)
                                if stuff_to_do_check[6] == 1: current_row[current_column+1+track_interval] = cd.get_date_from_rkg(rkg_sc)
                                if stuff_to_do_check[7] == 1: current_row[current_column+7+track_interval] = cd.get_driver(cd.get_driver_id_bin(rkg_sc))
                                if stuff_to_do_check[8] == 1: current_row[current_column+8+track_interval] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg_sc))
                                if stuff_to_do_check[9] == 1: current_row[current_column+9+track_interval] = cd.get_controller(cd.get_controller_id_bin(rkg_sc))

                    # If the player doesn't have a time, set the completion flag to False.
                    # If the player does have a time and it's faster than the SC (or there's no SC in general), copy the time over the SC.
                    # Special, rare case for videos, if the times are equal and one of the two doesn't have the video, put it up.

                    if current_flap_time == "" and sc_flap_time == "": complete_flap_norm, complete_flap_unr = False, False
                    elif current_flap_time == "" and sc_flap_time != "": complete_flap_norm = False
                    elif current_flap_time != "" and sc_flap_time == "":
                        current_row[current_column+2+track_interval] = current_row[current_column+2]
                        current_row[current_column+4+track_interval] = current_row[current_column+4]
                        current_row[current_column+6+track_interval] = current_row[current_column+6]
                    elif current_flap_time != "" and sc_flap_time != "":
                        if gs.get_timedelta_from_timestring(current_flap_time) < gs.get_timedelta_from_timestring(sc_flap_time):
                            current_row[current_column+2+track_interval] = current_row[current_column+2]
                            current_row[current_column+4+track_interval] = current_row[current_column+4]
                            current_row[current_column+6+track_interval] = current_row[current_column+6]
                        elif gs.get_timedelta_from_timestring(current_flap_time) == gs.get_timedelta_from_timestring(sc_flap_time):
                            if current_row[current_column+6] == "" : current_row[current_column+6] = current_row[current_column+6+track_interval]
                            elif current_row[current_column+6+track_interval] == "" : current_row[current_column+6+track_interval] = current_row[current_column+6]

                    current_column += track_interval * 2
                
                elif length_track == 3:
                    for i in range(2):
                        stuff_to_do_check = [0,0,0,0,0,0,0,0,0,0]
                        current_3lap_time = current_row[current_column]
                        current_flap_time = current_row[current_column+2]
                        sc_3lap_time = current_row[current_column+track_interval]
                        sc_flap_time = current_row[current_column+2+track_interval]
                        if current_3lap_time == "" and sc_3lap_time == "": complete_3lap_norm, complete_3lap_unr = False, False
                        elif current_3lap_time == "" and sc_3lap_time != "":
                            complete_3lap_norm = False
                            if "sì" in current_row[current_column+3+track_interval].lower():
                                if "chadsoft" in current_row[current_column-1+track_interval].lower() or current_row[current_column-1+track_interval] == "": current_row[current_column-1+track_interval] = stuff_to_do_check[5] = 1
                                if str(current_row[current_column+1+track_interval]).lower() == "sconosciuto" or str(current_row[current_column+1+track_interval]).lower(): stuff_to_do_check[6] = 1
                                if current_row[current_column+7+track_interval] == "" or current_row[current_column+7+track_interval].lower() == "sconosciuto": stuff_to_do_check[7] = 1
                                if current_row[current_column+8+track_interval] == "" or current_row[current_column+8+track_interval].lower() == "sconosciuto": stuff_to_do_check[8] = 1
                                if current_row[current_column+9+track_interval] == "" or current_row[current_column+9+track_interval].lower() == "sconosciuto": stuff_to_do_check[9] = 1

                            if stuff_to_do_check != [0,0,0,0,0,0,0,0,0,0]:
                                if "chadsoft" in current_row[current_column+3+track_interval].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3+track_interval].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                                elif "discord" in current_row[current_column+3+track_interval].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3+track_interval].split("\"")[1])
                                elif "maschell" in current_row[current_column+3+track_interval].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3+track_interval].split("\"")[1])
                                else: pass

                                if stuff_to_do_check[5] == 1: current_row[current_column-1+track_interval] = m2s.genRender(rkg)
                                if stuff_to_do_check[6] == 1: current_row[current_column+1+track_interval] = cd.get_date_from_rkg(rkg)
                                if stuff_to_do_check[7] == 1: current_row[current_column+7+track_interval] = cd.get_driver(cd.get_driver_id_bin(rkg))
                                if stuff_to_do_check[8] == 1: current_row[current_column+8+track_interval] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                                if stuff_to_do_check[9] == 1: current_row[current_column+9+track_interval] = cd.get_controller(cd.get_controller_id_bin(rkg))

                        elif current_3lap_time != "" and sc_3lap_time == "":
                            if "sì" in current_row[current_column+3].lower():
                                if "chadsoft" in current_row[current_column-1].lower() or current_row[current_column-1] == "": current_row[current_column-1] = stuff_to_do_check[0] = 1
                                if str(current_row[current_column+1]).lower() == "sconosciuto" or str(current_row[current_column+1]).lower() == "": stuff_to_do_check[1] = 1
                                if current_row[current_column+7] == "" or current_row[current_column+7].lower() == "sconosciuto": stuff_to_do_check[2] = 1
                                if current_row[current_column+8] == "" or current_row[current_column+8].lower() == "sconosciuto": stuff_to_do_check[3] = 1
                                if current_row[current_column+9] == "" or current_row[current_column+9].lower() == "sconosciuto": stuff_to_do_check[4] = 1

                            if stuff_to_do_check != [0,0,0,0,0,0,0,0,0,0]:
                                if "chadsoft" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                                elif "discord" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3].split("\"")[1])
                                elif "maschell" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3].split("\"")[1])
                                else: pass

                                if stuff_to_do_check[0] == 1: current_row[current_column-1] = m2s.genRender(rkg)
                                if stuff_to_do_check[1] == 1: current_row[current_column+1] = cd.get_date_from_rkg(rkg)
                                if stuff_to_do_check[2] == 1: current_row[current_column+7] = cd.get_driver(cd.get_driver_id_bin(rkg))
                                if stuff_to_do_check[3] == 1: current_row[current_column+8] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                                if stuff_to_do_check[4] == 1: current_row[current_column+9] = cd.get_controller(cd.get_controller_id_bin(rkg))

                            current_row[current_column-1] = current_row[current_column-1]
                            current_row[current_column]   = current_row[current_column]
                            current_row[current_column+1] = current_row[current_column+1]
                            current_row[current_column+3] = current_row[current_column+3]
                            current_row[current_column+5] = current_row[current_column+5]
                            current_row[current_column+7] = current_row[current_column+7]
                            current_row[current_column+8] = current_row[current_column+8]
                            current_row[current_column+9] = current_row[current_column+9]
                            
                        elif current_3lap_time != "" and sc_3lap_time != "":
                            if gs.get_timedelta_from_timestring(current_3lap_time) < gs.get_timedelta_from_timestring(sc_3lap_time):
                                if "sì" in current_row[current_column+3].lower():
                                    if "chadsoft" in current_row[current_column-1].lower() or current_row[current_column-1] == "": current_row[current_column-1] = stuff_to_do_check[0] = 1
                                    if str(current_row[current_column+1]).lower() == "sconosciuto" or str(current_row[current_column+1]).lower() == "": stuff_to_do_check[1] = 1
                                    if current_row[current_column+7] == "": stuff_to_do_check[2] = 1
                                    if current_row[current_column+8] == "": stuff_to_do_check[3] = 1
                                    if current_row[current_column+9] == "": stuff_to_do_check[4] = 1

                                if stuff_to_do_check != [0,0,0,0,0,0,0,0,0,0]:
                                    if "chadsoft" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                                    elif "discord" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3].split("\"")[1])
                                    elif "maschell" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3].split("\"")[1])
                                    else: pass

                                    if stuff_to_do_check[0] == 1: current_row[current_column-1] = m2s.genRender(rkg)
                                    if stuff_to_do_check[1] == 1: current_row[current_column+1] = cd.get_date_from_rkg(rkg)
                                    if stuff_to_do_check[2] == 1: current_row[current_column+7] = cd.get_driver(cd.get_driver_id_bin(rkg))
                                    if stuff_to_do_check[3] == 1: current_row[current_column+8] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                                    if stuff_to_do_check[4] == 1: current_row[current_column+9] = cd.get_controller(cd.get_controller_id_bin(rkg))
                                    
                                current_row[current_column-1+track_interval] = current_row[current_column-1]
                                current_row[current_column+track_interval]   = current_row[current_column]
                                current_row[current_column+1+track_interval] = current_row[current_column+1]
                                current_row[current_column+3+track_interval] = current_row[current_column+3]
                                current_row[current_column+5+track_interval] = current_row[current_column+5]
                                current_row[current_column+7+track_interval] = current_row[current_column+7]
                                current_row[current_column+8+track_interval] = current_row[current_column+8]
                                current_row[current_column+9+track_interval] = current_row[current_column+9]
                            elif gs.get_timedelta_from_timestring(current_3lap_time) == gs.get_timedelta_from_timestring(sc_3lap_time):
                                if "sì" in current_row[current_column+3].lower():
                                    if "chadsoft" in current_row[current_column-1].lower() or current_row[current_column-1] == "": current_row[current_column-1] = stuff_to_do_check[0] = 1
                                    if str(current_row[current_column+1]).lower() == "sconosciuto" or str(current_row[current_column+1]).lower() == "": stuff_to_do_check[1] = 1
                                    if current_row[current_column+7] == "" or current_row[current_column+7].lower() == "sconosciuto": stuff_to_do_check[2] = 1
                                    if current_row[current_column+8] == "" or current_row[current_column+8].lower() == "sconosciuto": stuff_to_do_check[3] = 1
                                    if current_row[current_column+9] == "" or current_row[current_column+9].lower() == "sconosciuto": stuff_to_do_check[4] = 1

                                if stuff_to_do_check != [0,0,0,0,0,0,0,0,0,0]:
                                    if "chadsoft" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                                    elif "discord" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3].split("\"")[1])
                                    elif "maschell" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3].split("\"")[1])
                                    else: pass

                                    if stuff_to_do_check[0] == 1: current_row[current_column-1] = m2s.genRender(rkg)
                                    if stuff_to_do_check[1] == 1: current_row[current_column+1] = cd.get_date_from_rkg(rkg)
                                    if stuff_to_do_check[2] == 1: current_row[current_column+7] = cd.get_driver(cd.get_driver_id_bin(rkg))
                                    if stuff_to_do_check[3] == 1: current_row[current_column+8] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                                    if stuff_to_do_check[4] == 1: current_row[current_column+9] = cd.get_controller(cd.get_controller_id_bin(rkg))
                                    
                                current_row[current_column-1+track_interval] = current_row[current_column-1]
                                current_row[current_column+track_interval]   = current_row[current_column]
                                current_row[current_column+1+track_interval] = current_row[current_column+1]
                                current_row[current_column+3+track_interval] = current_row[current_column+3]
                                current_row[current_column+7+track_interval] = current_row[current_column+7]
                                current_row[current_column+8+track_interval] = current_row[current_column+8]
                                current_row[current_column+9+track_interval] = current_row[current_column+9]

                                if current_row[current_column+5] == "" : current_row[current_column+5] = current_row[current_column+5+track_interval]
                                elif current_row[current_column+5+track_interval] == "" : current_row[current_column+5+track_interval] = current_row[current_column+5]

                            else:
                                if "sì" in current_row[current_column+3].lower():
                                    if "chadsoft" in current_row[current_column-1].lower() or current_row[current_column-1] == "": current_row[current_column-1] = stuff_to_do_check[0] = 1
                                    if str(current_row[current_column+1]).lower() == "sconosciuto" or str(current_row[current_column+1]).lower() == "": stuff_to_do_check[1] = 1
                                    if current_row[current_column+7] == "": stuff_to_do_check[2] = 1
                                    if current_row[current_column+8] == "": stuff_to_do_check[3] = 1
                                    if current_row[current_column+9] == "": stuff_to_do_check[4] = 1

                                if "sì" in current_row[current_column+3+track_interval].lower():
                                    if "chadsoft" in current_row[current_column-1+track_interval].lower() or current_row[current_column-1+track_interval] == "": current_row[current_column-1+track_interval] = stuff_to_do_check[5] = 1
                                    if str(current_row[current_column+1+track_interval]).lower() == "sconosciuto" or str(current_row[current_column+1+track_interval]).lower(): stuff_to_do_check[6] = 1
                                    if current_row[current_column+7+track_interval] == "": stuff_to_do_check[7] = 1
                                    if current_row[current_column+8+track_interval] == "": stuff_to_do_check[8] = 1
                                    if current_row[current_column+9+track_interval] == "": stuff_to_do_check[9] = 1

                                if stuff_to_do_check != [0,0,0,0,0,0,0,0,0,0]:
                                    if "chadsoft" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                                    elif "discord" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3].split("\"")[1])
                                    elif "maschell" in current_row[current_column+3].lower(): rkg = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3].split("\"")[1])
                                    else: pass
                                    
                                    if "chadsoft" in current_row[current_column+3+track_interval].lower(): rkg_sc = cd.get_ghost_rkg("/rkgd/"+current_row[current_column+3+track_interval].split("\"")[1].split("/rkgd/")[1][:-4]+"rkg")
                                    elif "discord" in current_row[current_column+3+track_interval].lower(): rkg_sc = cd.get_ghost_rkg_from_other_site(site_name="discord",link=current_row[current_column+3+track_interval].split("\"")[1])
                                    elif "maschell" in current_row[current_column+3+track_interval].lower(): rkg_sc = cd.get_ghost_rkg_from_other_site(site_name="maschell",link=current_row[current_column+3+track_interval].split("\"")[1])
                                    else: pass

                                    if stuff_to_do_check[0] == 1: current_row[current_column-1] = m2s.genRender(rkg)
                                    if stuff_to_do_check[1] == 1: current_row[current_column+1] = cd.get_date_from_rkg(rkg)
                                    if stuff_to_do_check[2] == 1: current_row[current_column+7] = cd.get_driver(cd.get_driver_id_bin(rkg))
                                    if stuff_to_do_check[3] == 1: current_row[current_column+8] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg))
                                    if stuff_to_do_check[4] == 1: current_row[current_column+9] = cd.get_controller(cd.get_controller_id_bin(rkg))
                                    if stuff_to_do_check[5] == 1: current_row[current_column-1+track_interval] = m2s.genRender(rkg_sc)
                                    if stuff_to_do_check[6] == 1: current_row[current_column+1+track_interval] = cd.get_date_from_rkg(rkg_sc)
                                    if stuff_to_do_check[7] == 1: current_row[current_column+7+track_interval] = cd.get_driver(cd.get_driver_id_bin(rkg_sc))
                                    if stuff_to_do_check[8] == 1: current_row[current_column+8+track_interval] = cd.get_vehicle(cd.get_vehicle_id_bin(rkg_sc))
                                    if stuff_to_do_check[9] == 1: current_row[current_column+9+track_interval] = cd.get_controller(cd.get_controller_id_bin(rkg_sc))

                        # If the player doesn't have a time, set the completion flag to False.
                        # If the player does have a time and it's faster than the SC (or there's no SC in general), copy the time over the SC.
                        # Special, rare case for videos, if the times are equal and one of the two doesn't have the video, put it up.

                        if current_flap_time == "" and sc_flap_time == "": complete_flap_norm, complete_flap_unr = False, False
                        elif current_flap_time == "" and sc_flap_time != "": complete_flap_norm = False
                        elif current_flap_time != "" and sc_flap_time == "":
                            current_row[current_column+2+track_interval] = current_row[current_column+2]
                            current_row[current_column+4+track_interval] = current_row[current_column+4]
                            current_row[current_column+6+track_interval] = current_row[current_column+6]
                        elif current_flap_time != "" and sc_flap_time != "":
                            if gs.get_timedelta_from_timestring(current_flap_time) < gs.get_timedelta_from_timestring(sc_flap_time):
                                current_row[current_column+2+track_interval] = current_row[current_column+2]
                                current_row[current_column+4+track_interval] = current_row[current_column+4]
                                current_row[current_column+6+track_interval] = current_row[current_column+6]
                            elif gs.get_timedelta_from_timestring(current_flap_time) == gs.get_timedelta_from_timestring(sc_flap_time):
                                if current_row[current_column+6] == "" : current_row[current_column+6] = current_row[current_column+6+track_interval]
                                elif current_row[current_column+6+track_interval] == "" : current_row[current_column+6+track_interval] = current_row[current_column+6]

                        # Runs the 2 Category code twice so it checks SC and Glitch in an easier to understand way

                        if i == 0: current_column += track_interval
                        elif i == 1: current_column += track_interval * 2

            current_row[1] = complete_3lap_norm
            current_row[2] = complete_3lap_unr
            current_row[3] = complete_flap_norm
            current_row[4] = complete_flap_unr

            if complete_3lap_norm: self.display_msg.emit(f"[3LAP NORMAL]       is complete at row {row+1}")
            if complete_3lap_unr:  self.display_msg.emit(f"[3LAP UNRESTRICTED] is complete at row {row+1}")
            if complete_flap_norm: self.display_msg.emit(f"[FLAP NORMAL]       is complete at row {row+1}")
            if complete_flap_unr:  self.display_msg.emit(f"[FLAP UNRESTRICTED] is complete at row {row+1}")

            if row % 50 == 0: gs.set_all_values(wks, full_gs)

        self.display_msg.emit("[UPDATING...] Uploading data to Google Sheets")
        gs.set_all_values(wks, full_gs)
        self.display_msg.emit("\n[FINISHED]")

    def run(self):

        if self.isInterruptionRequested():
            self.stopped.emit()
            try:
                rmtree("tmp/")
            except:
                pass
            return -1

        if self.active_3lap: self.update_3laps()
        if self.active_flap: self.update_flaps()
        if self.active_unr: self.update_unrestricted_and_checks()
        self.display_msg.emit("\n\n[NOTHING TO DO]\n\n")
