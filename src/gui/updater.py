import json
import datetime
import gspread
import os
from PySide6.QtCore import QThread, Signal
from shutil import rmtree

from apis.mii2studio import mii2studio as m2s
from apis import google_sheet as gs
from apis import chadsoft as cd

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
        self.setOptions(10, True, True, True, True, True, True, True)

    def stop_msg(self):
        self.display_msg.emit("\n\n[OPERATION STOPPED]")

    def setOptions(self, partial_update_rows:int, debug_checked: bool, debug_skipped: bool, debug_ghosts: bool, debug_found: bool, debug_complete: bool, debug_gs_3laps_info: bool, debug_gs_unr_info: bool):
        self.partial_update_rows = partial_update_rows
        self.debug_checked = debug_checked
        self.debug_skipped = debug_skipped
        self.debug_ghosts = debug_ghosts
        self.debug_found = debug_found
        self.debug_complete = debug_complete
        self.debug_gs_3laps_info = debug_gs_3laps_info
        self.debug_gs_unr_info = debug_gs_unr_info

    def setMode(self, active_3laps: bool, active_unr: bool) -> None:
        if active_3laps and active_unr:
            self.mode = 0
        elif active_3laps:
            self.mode = 1
        elif active_unr:
            self.mode = 2
        else:
            self.mode = 3

    def update_flaps(self, wks: gspread.worksheet.Worksheet = None):
        log_out = ""
        try:
            os.mkdir("tmp")
        except:
            pass
        self.display_msg.emit("\n[FLAPs UPDATE STARTED]")
        if wks == None: 
            wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
            if feedback and self.debug_gs_3laps_info:
                self.display_msg.emit(feedback)
        full_gs = gs.get_all_values(wks)
        IDs = [i[gs.ID_COLUMN] for i in full_gs[2:]]
        row = 1 #Current row
        Tracks =
        from_last_gs_update = 0
        for Track in Tracks:
            for ID in IDs:
                if self.isInterruptionRequested():
                    with open("log.txt","w") as f:
                        log_out += "[OPERATION STOPPED]"
                        f.write(log_out)
                    self.stopped.emit()
                    gs.set_all_values(wks, full_gs)
                    try:
                        rmtree("tmp/")
                    except:
                        pass
                    return -1
                row += 1

    def update_3laps(self, wks: gspread.worksheet.Worksheet = None):
        log_out = ""
        try:
            os.mkdir("tmp")
        except:
            pass
        self.display_msg.emit("\n[3LAPs UPDATE STARTED]")
        if wks == None: 
            wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
            if feedback and self.debug_gs_3laps_info:
                self.display_msg.emit(feedback)
        full_gs = gs.get_all_values(wks)
        IDs = [i[gs.ID_COLUMN] for i in full_gs[2:]]
        LMs = [i[gs.LAST_MODIFIED_COLUMN] for i in full_gs[2:]]
        row = 1 #Current row
        from_last_gs_update = 0
        for ID, LM in zip(IDs, LMs):
            if self.isInterruptionRequested():
                with open("log.txt","w") as f:
                    log_out += "[OPERATION STOPPED]"
                    f.write(log_out)
                self.stopped.emit()
                gs.set_all_values(wks, full_gs)
                try:
                    rmtree("tmp/")
                except:
                    pass
                return -1
            row += 1
            if ID == "noID":
                if self.debug_skipped: self.display_msg.emit(f"[SKIPPING ROW {row+1}] NO ID") # +1 for the Spreadsheet's offset
                continue
            elif ID == "":
                if self.debug_skipped: self.display_msg.emit(f"  [SKIPPING ROW {row+1}] EMPTY ID CELL")
                log_out += f"  [SKIPPING ROW {row+1}] EMPTY ID CELL\n"
                continue
            ID, jolly = gs.get_jolly_and_purify_ID(ID)

            Player_Name = full_gs[row][0]

            if self.debug_checked: self.display_msg.emit(f"[CHECKING ROW {row+1}] Player Name: {Player_Name}, ID: {ID}")

            cd_LM = cd.get_player_last_modified(ID)
            if LM != "" and datetime.datetime.fromisoformat(LM) > cd_LM:
                continue

            if self.debug_checked: self.display_msg.emit(f"  [DATA FOUND AT ROW {row+1}] fetching player JSON from Chadsoft...")
            log_out += f"  [DATA FOUND AT ROW {row+1}] fetching {Player_Name}'s JSON from Chadsoft...\n"
            from_last_gs_update += 1
            player_data = json.loads(cd.get_player_pbs(ID))
            ghosts = player_data["ghosts"]
            gs_row_values = full_gs[row+jolly]
            for g in ghosts:
                if self.isInterruptionRequested():
                    with open("log.txt","w") as f:
                        log_out += "[OPERATION STOPPED]"
                        f.write(log_out)
                    self.stopped.emit()
                    gs.set_all_values(wks, full_gs)
                    try:
                        rmtree("tmp/")
                    except:
                        pass
                    return -1
                if g["200cc"] == True or g["trackId"] not in list(gs.RT_CATEGORIES.keys()):
                    continue
                trackId = g["trackId"]
                try:
                    categoryId = g["categoryId"]
                except:
                    categoryId = -1
                gs_track_column = gs.get_track_column(trackId, categoryId)
                if gs_track_column == "INVALID_TRACK_CATEGORY":
                    if self.debug_ghosts: self.display_msg.emit(f"  [SKIPPING INVALID TRACK CATEGORY] {g['trackName']}; category: {cd.get_category(categoryId)}")
                    log_out += f"  [SKIPPING INVALID TRACK CATEGORY] {g['trackName']}; category: {cd.get_category(categoryId)}\n"
                    continue

                new_time = g["finishTimeSimple"]
                new_time = gs.get_timedelta_from_timestring(new_time)
                try:
                    old_time = gs_row_values[gs_track_column]
                    old_time = gs.get_timedelta_from_timestring(old_time)
                except:
                    old_time = datetime.timedelta()

                if not (old_time == datetime.timedelta() 
                    or (full_gs[row+jolly][gs_track_column+3] in ["TBA", "No"] and new_time <= old_time) 
                    or (full_gs[row+jolly][gs_track_column+3] not in ["TBA", "No"] and new_time < old_time)):
                    continue

                new_time = gs.get_timestring_from_timedelta(new_time, categoryId)
                old_3lap_vid_link = full_gs[row+jolly][gs_track_column+5] # Used to warn about possibly overwriting a TBA video
                rkg_info = cd.get_ghost_rkg(g["href"])

                if self.debug_ghosts: self.display_msg.emit(f"  (NEW GHOSTS FOUND), {g['trackName']}; category: {cd.get_category(categoryId)}; time: {new_time}, ghost_link: {cd.get_ghost_link(g['href'])}")
                log_out += f"  (NEW GHOSTS FOUND), {g['trackName']}; category: {cd.get_category(categoryId)}; time: {new_time}, ghost_link: {cd.get_ghost_link(g['href'])}\n"
                # Modify the values in the full_gs to the ones of the GHOST
                if old_3lap_vid_link != "":
                    self.display_msg.emit(f"      [Old Video Link found] {old_3lap_vid_link}")
                    log_out += f"      [OLD VIDEO LINK FOUND] {old_3lap_vid_link}\n"
                full_gs[row+jolly][gs_track_column-1] = m2s.genRender(rkg_info)
                full_gs[row+jolly][gs_track_column] = new_time
                full_gs[row+jolly][gs_track_column+1] = cd.get_date_from_rkg(rkg_info)
                full_gs[row+jolly][gs_track_column+3] = "=HYPERLINK(\"" + cd.get_ghost_link(g["href"]) + "\"; \"Sì\")" # Ghost info, taken from chadsoft
                full_gs[row+jolly][gs_track_column+5] = ""
                full_gs[row+jolly][gs_track_column+7] = cd.get_driver(g["driverId"])
                full_gs[row+jolly][gs_track_column+8] = cd.get_vehicle(g["vehicleId"])
                full_gs[row+jolly][gs_track_column+9] = cd.get_controller(g["controller"])



            shifted_LM = cd_LM + datetime.timedelta(minutes=30)
            full_gs[row][gs.LAST_MODIFIED_COLUMN] = shifted_LM.isoformat()

            if from_last_gs_update >= self.partial_update_rows:
                from_last_gs_update = 0
                gs.set_all_values(wks, full_gs)
                full_gs = gs.get_all_values(wks)
                if self.debug_gs_3laps_info: self.display_msg.emit(f"[SUCCESSFUL] UPDATED {self.partial_update_rows} ROWS OF GOOGLE SHEETS, PROCEEDING WITH THE NEXT BLOCK...")

        gs.set_all_values(wks, full_gs)
        with open("log.txt","w") as f:
            f.write(log_out)
        self.display_msg.emit("\n[3LAPs UPDATE FINISHED]")

    def update_unrestricted_and_checks(self, wks: gspread.worksheet.Worksheet = None):
        self.display_msg.emit("\n[UNRESTRICTED UPDATE STARTED]")
        if wks == None: 
            wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
            if feedback and self.debug_gs_unr_info:
                self.display_msg.emit(feedback)
        full_gs = gs.get_all_values(wks)

        # After everything, check the unrestricted
        names = [i[0] for i in full_gs[2:]]
        row = 1
        for name in names:
            if self.isInterruptionRequested():
                gs.set_all_values(wks, full_gs)
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
                        if self.debug_found: self.display_msg.emit(f"[UNRESTRICTED_3LAP] Found at row: {row+1}, column: {next_column+1}")

                if not track_has_sc_glitch: complete_3lap_unr = False

            if complete_3lap_norm: complete_3lap_unr = True
            full_gs[row][gs.CHECK_FULL_3LAP_NORMAL_COLUMN] = complete_3lap_norm
            full_gs[row][gs.CHECK_FULL_3LAP_UNRESTRICTED_COLUMN] = complete_3lap_unr

            if self.debug_complete:
                if complete_3lap_norm: self.display_msg.emit(f"[3LAP NORMAL]       is complete at row {row+1}")
                if complete_3lap_unr:  self.display_msg.emit(f"[3LAP UNRESTRICTED] is complete at row {row+1}")


        if self.debug_gs_unr_info: self.display_msg.emit("[UPDATING...] Uploading data to Google Sheets")
        gs.set_all_values(wks, full_gs)
        self.display_msg.emit("\n[UNRESTRICTED_3LAPs UPDATE FINISHED]")

        row = 1
        for name in names:
            if self.isInterruptionRequested():
                gs.set_all_values(wks, full_gs)
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
                        if self.debug_found: self.display_msg.emit(f"[UNRESTRICTED_FLAP] Found at row: {row+1}, column: {next_column+3}") # +3 instead of +1 for the offset

                if not track_has_sc_glitch: complete_flap_unr = False

            if complete_flap_norm: complete_flap_unr = True
            full_gs[row][gs.CHECK_FULL_FLAP_NORMAL_COLUMN] = complete_flap_norm
            full_gs[row][gs.CHECK_FULL_FLAP_UNRESTRICTED_COLUMN] = complete_flap_unr

            if self.debug_complete:
                if complete_flap_norm: self.display_msg.emit(f"[FLAP NORMAL]       is complete at row {row+1}")
                if complete_flap_unr:  self.display_msg.emit(f"[FLAP UNRESTRICTED] is complete at row {row+1}")

        if self.debug_gs_unr_info: self.display_msg.emit("[UPDATING...] Uploading data to Google Sheets")
        gs.set_all_values(wks, full_gs)
        self.display_msg.emit("\n[UNRESTRICTED_FLAP UPDATE FINISHED]")

    def update_everything(self):
        self.display_msg.emit("\n[UPDATE OF EVERYTHING STARTED]")
        wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
        if feedback:
            if self.debug_gs_3laps_info or self.debug_gs_unr_info: self.display_msg.emit(feedback)
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
        
        match self.mode:
            case 0 : self.update_everything()
            case 1 : self.update_3laps()
            case 2 : self.update_unrestricted_and_checks()
            case 3 : self.display_msg.emit("\n\n[NOTHING TO DO]\n\n")