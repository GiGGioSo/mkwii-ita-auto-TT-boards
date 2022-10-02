import json
import datetime
from operator import index
from textwrap import indent
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
        self.display_msg.emit("[FLAPs UPDATE STARTED]")
        log_out = ""
        total_time = 0
        if wks == None: 
            wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
            if feedback: self.display_msg.emit(feedback)
        full_gs = gs.get_all_values(wks)
        gs_track_column = 2 + gs.GS_START_INDEX
        
        start_offset = self.track_skip_flap
   
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
                            with open("log.txt","w") as f:
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
                            with open("log.txt","w") as f:
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
                            or (full_gs[row+jolly][gs_track_column+2] in ["TBA", "", "No"] and new_time <= old_time) 
                            or (full_gs[row+jolly][gs_track_column+2] not in ["TBA", "", "No"] and new_time < old_time)):
                                continue
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
                self.display_msg.emit(f"{track_name} took {time.time()-start_time_local} to update")
                total_time += time.time()-start_time
                self.display_msg.emit(f"Total Time Elapsed: {total_time}")
                log_out += f"Total Time Elapsed: {total_time}"
                gs_track_column += gs.GS_TRACKS_INTERVAL
                cat_n += 1
            gs.set_all_values(wks, full_gs)
            full_gs = gs.get_all_values(wks)
            self.display_msg.emit(f"[SUCCESSFUL] Updated {track_name} {cat_name}, proceeding with the next track...")
            with open("log.txt","w") as f:
                f.write(log_out)
        self.display_msg.emit("[FLAPS UPDATE FINISHED]")

    def update_3laps(self, wks: gspread.worksheet.Worksheet = None):
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
                            with open("log.txt","w") as f: f.write(log_out)
                            self.stopped.emit()
                            try: rmtree("tmp/")
                            except: pass
                            return -1

                        player_name = full_gs[row][0]
                        self.display_msg.emit(f"Player Found: {player_name}, ID: {ID}, Row: {row+1}")

                        if self.isInterruptionRequested():
                            with open("log.txt","w") as f: f.write(log_out)
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
                            or (full_gs[row+jolly][gs_track_column+2] in ["TBA", "", "No"] and new_time <= old_time) 
                            or (full_gs[row+jolly][gs_track_column+2] not in ["TBA", "", "No"] and new_time < old_time)):
                                continue
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
                        full_gs[row+jolly][gs_track_column] = cd.get_date_from_rkg(rkg_info)
                        full_gs[row+jolly][gs_track_column] = new_time
                        full_gs[row+jolly][gs_track_column+3] = new_cell_link
                        full_gs[row+jolly][gs_track_column+5] = ""
                        full_gs[row+jolly][gs_track_column+7] = cd.get_driver(player_info["driverId"])
                        full_gs[row+jolly][gs_track_column+8] = cd.get_vehicle(player_info["vehicleId"])
                        full_gs[row+jolly][gs_track_column+9] = cd.get_controller(player_info["controller"])
                        if self.rkg_dl_3lap:
                            try: os.mkdir("ghosts_flap")
                            except: pass
                            try: os.mkdir("ghosts_flap/"+track_name)
                            except: pass
                            with open("ghosts_flap/"+track_name+"/"+player_name.replace("*","")+".rkg","wb") as f:
                                f.write(rkg_info)
                self.display_msg.emit(f"{track_name} took {time.time()-start_time_local} to update")
                total_time += time.time()-start_time
                self.display_msg.emit(f"Total Time Elapsed: {total_time}")
                log_out += f"Total Time Elapsed: {total_time}"
                gs_track_column += gs.GS_TRACKS_INTERVAL
                cat_n += 1
            gs.set_all_values(wks, full_gs)
            full_gs = gs.get_all_values(wks)
            self.display_msg.emit(f"[SUCCESSFUL] Updated {track_name} {cat_name}, proceeding with the next track...")
            with open("log.txt","w") as f:
                f.write(log_out)
        self.display_msg.emit("[FLAPS UPDATE FINISHED]")


        gs.set_all_values(wks, full_gs)
        with open("log.txt","w") as f:
            f.write(log_out)
        self.display_msg.emit("\n[3LAPs UPDATE FINISHED]")

    def update_unrestricted_and_checks(self, wks: gspread.worksheet.Worksheet = None):
        self.display_msg.emit("\n[UNRESTRICTED UPDATE STARTED]")
        if wks == None: 
            wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
            if feedback:
                self.display_msg.emit(feedback)
        full_gs = gs.get_all_values(wks)

        # After everything, check the unrestricted
        names = [i[0] for i in full_gs[2:]]
        row = 1
        for name in names:
            if self.isInterruptionRequested():
                self.stopped.emit()
                return -1
            row += 1
            current_row = full_gs[row]

            complete_3lap_norm = True
            complete_3lap_unr = True

            for trackId, categories in gs.RT_CATEGORIES.items():
                if self.isInterruptionRequested():
                    gs.set_all_values(wks, full_gs)
                    self.stopped.emit()
                    return -1
                track_has_sc_glitch = False
                for i in range(len(categories) - 1):
                    try:
                        this_gs_time = current_row[gs.get_track_column(trackId, categories[i])]
                        this_time = gs.get_timedelta_from_timestring(this_gs_time)
                    except:
                        if categories[i] in [0, 2, 18, -1]: complete_3lap_norm = False
                        continue

                    if categories[i] in [16, 1]: track_has_sc_glitch = True

                    try:
                        next_gs_time = current_row[gs.get_track_column(trackId, categories[i+1])]
                        next_time = gs.get_timedelta_from_timestring(next_gs_time)
                    except:
                        next_time = datetime.timedelta()

                    if next_time == datetime.timedelta() or this_time < next_time:
                        this_column = gs.get_track_column(trackId, categories[i])
                        next_column = gs.get_track_column(trackId, categories[i+1])
                        mii = gs.get_value_safely(full_gs, row, this_column-1)
                        date = gs.get_date_from_gs_timestamp(gs.get_value_safely(full_gs, row, this_column+1))
                        ghost = gs.get_value_safely(full_gs, row, this_column+3)
                        video = gs.get_value_safely(full_gs, row, this_column+5)
                        vehicle = gs.get_value_safely(full_gs, row, this_column+7)
                        player = gs.get_value_safely(full_gs, row, this_column+8)
                        controller = gs.get_value_safely(full_gs, row, this_column+9)

                        full_gs[row][next_column-1] = mii
                        full_gs[row][next_column] = this_gs_time
                        full_gs[row][next_column+1] = date
                        full_gs[row][next_column+3] = ghost
                        full_gs[row][next_column+5] = video
                        full_gs[row][next_column+7] = vehicle
                        full_gs[row][next_column+8] = player
                        full_gs[row][next_column+9] = controller
                        self.display_msg.emit(f"[UNRESTRICTED_3LAP] Found at row: {row+1}, column: {next_column+1}")

                if not track_has_sc_glitch: complete_3lap_unr = False

            if complete_3lap_norm: complete_3lap_unr = True
            full_gs[row][gs.CHECK_FULL_3LAP_NORMAL_COLUMN] = complete_3lap_norm
            full_gs[row][gs.CHECK_FULL_3LAP_UNRESTRICTED_COLUMN] = complete_3lap_unr

            if complete_3lap_norm: self.display_msg.emit(f"[3LAP NORMAL]       is complete at row {row+1}")
            if complete_3lap_unr:  self.display_msg.emit(f"[3LAP UNRESTRICTED] is complete at row {row+1}")


        self.display_msg.emit("[UPDATING...] Uploading data to Google Sheets")
        gs.set_all_values(wks, full_gs)
        self.display_msg.emit("\n[UNRESTRICTED_3LAPs UPDATE FINISHED]")

        row = 1
        for name in names:
            if self.isInterruptionRequested():
                self.stopped.emit()
                return -1
            row += 1
            current_row = full_gs[row]

            complete_flap_norm = True
            complete_flap_unr = True

            for trackId, categories in gs.RT_CATEGORIES.items():
                if self.isInterruptionRequested():
                    gs.set_all_values(wks, full_gs)
                    self.stopped.emit()
                    return -1
                track_has_sc_glitch = False
                for i in range(len(categories) - 1):
                    try:
                        this_gs_time = current_row[gs.get_track_column(trackId, categories[i]) + 2] # + 2 because the flap time is offset 2 from 3lap time
                        this_time = gs.get_timedelta_from_timestring(this_gs_time)
                    except:
                        if categories[i] in [0, 2, 18, -1]: complete_flap_norm = False
                        continue

                    if categories[i] in [16, 1]: track_has_sc_glitch = True

                    try:
                        next_gs_time = current_row[gs.get_track_column(trackId, categories[i+1]) + 2] # + 2 because the flap time is offset 2 from 3lap time
                        next_time = gs.get_timedelta_from_timestring(next_gs_time)
                    except:
                        next_time = datetime.timedelta()

                    if next_time == datetime.timedelta() or this_time < next_time:
                        this_column = gs.get_track_column(trackId, categories[i])
                        next_column = gs.get_track_column(trackId, categories[i+1])

                        ghost = gs.get_value_safely(full_gs, row, this_column+4)
                        video = gs.get_value_safely(full_gs, row, this_column+6)

                        full_gs[row][next_column+2] = this_gs_time
                        full_gs[row][next_column+4] = ghost
                        full_gs[row][next_column+6] = video
                        self.display_msg.emit(f"[UNRESTRICTED_FLAP] Found at row: {row+1}, column: {next_column+3}") # +3 instead of +1 for the offset

                if not track_has_sc_glitch: complete_flap_unr = False

            if complete_flap_norm: complete_flap_unr = True
            full_gs[row][gs.CHECK_FULL_FLAP_NORMAL_COLUMN] = complete_flap_norm
            full_gs[row][gs.CHECK_FULL_FLAP_UNRESTRICTED_COLUMN] = complete_flap_unr

            if complete_flap_norm: self.display_msg.emit(f"[FLAP NORMAL]       is complete at row {row+1}")
            if complete_flap_unr:  self.display_msg.emit(f"[FLAP UNRESTRICTED] is complete at row {row+1}")

        self.display_msg.emit("[UPDATING...] Uploading data to Google Sheets")
        gs.set_all_values(wks, full_gs)
        self.display_msg.emit("\n[UNRESTRICTED_FLAP UPDATE FINISHED]")

    def update_everything(self):
        self.display_msg.emit("\n[UPDATE OF EVERYTHING STARTED]")
        wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
        if feedback: self.display_msg.emit(feedback)
        exit_code = self.update_3laps(wks)
        if exit_code == -1: return -1
        self.update_unrestricted_and_checks(wks)
        self.display_msg.emit("\n[UPDATE OF EVERYTHING FINISHED]")

    def run(self):

        if self.isInterruptionRequested():
            self.stopped.emit()
            try:
                rmtree("tmp/")
            except:
                pass
            return -1

        if self.active_3lap: self.update_3laps()
        elif self.active_flap: self.update_flaps()
        elif self.active_unr: self.update_unrestricted_and_checks()
        else: self.display_msg.emit("\n\n[NOTHING TO DO]\n\n")
