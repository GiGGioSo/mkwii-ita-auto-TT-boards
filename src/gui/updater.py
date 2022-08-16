import json
import datetime
import gspread
from PySide6.QtCore import QThread, Signal

from apis import google_sheet as gs
from apis import chadsoft as cd

SERVICE_KEY_FILENAME = "mkwii-ita-auto-tt-service-key.json"
GOOGLE_SHEET_KEY = "1pzvXA5NeHaqgaUe5ft_d4TauEbX9lVFxVp3dM51HsuA"
WORKSHEET_NAME = "ProvaDatabase"

class Updater(QThread):

    # 0 = update everything
    # 1 = update only 3laps
    # 2 = update only unrestricted
    mode = 0

    display_msg = Signal(str)

    def __init__(self, parent = None):
        super(Updater, self).__init__(parent)

    def update_3laps(self, wks: gspread.worksheet.Worksheet = None, debug: bool = True) -> None:
        if wks == None: 
            wks = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME, True)
        full_gs = gs.get_all_values(wks)
        IDs = [i[gs.ID_COLUMN] for i in full_gs[2:]]
        LMs = [i[gs.LAST_MODIFIED_COLUMN] for i in full_gs[2:]]
        row = 1 #Current row
        from_last_gs_update = 0
        for ID, LM in zip(IDs, LMs):
            if self.isInterruptionRequested(): return
            row += 1
            if ID == "noID" or ID == "":
                if debug: self.display_msg.emit(f"[PLAYER SKIPPED AT ROW {row}]")
                continue
            ID, jolly = gs.get_jolly_and_purify_ID(ID)
            
            if debug: self.display_msg.emit(f"[CHECKING ROW {row}] ID: {ID}")

            cd_LM = cd.get_player_last_modified(ID)
            if LM != "" and datetime.datetime.fromisoformat(LM) > cd_LM:
                continue

            if debug: self.display_msg.emit("  [OUTDATED DATA FOUND] fetching player JSON from Chadsoft...")
            from_last_gs_update += 1
            player_data = json.loads(cd.get_player_pbs(ID))
            ghosts = player_data["ghosts"]
            gs_row_values = full_gs[row+jolly]
            for g in ghosts:
                if self.isInterruptionRequested(): return
                if g["200cc"] == True or g["trackId"] not in list(gs.RT_CATEGORIES.keys()):
                    continue
                trackId = g["trackId"]
                try:
                    categoryId = g["categoryId"]
                except:
                    categoryId = -1
                gs_track_column = gs.get_track_column(trackId, categoryId)
                if gs_track_column == "INVALID_TRACK_CATEGORY":
                    if debug: self.display_msg.emit(f"  [SKIPPING INVALID TRACK CATEGORY] {g['trackName']}; category: {cd.get_category(categoryId)}")
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

                if debug: self.display_msg.emit(f"  (NEW GHOSTS FOUND), {g['trackName']}; category: {cd.get_category(categoryId)}; time: {new_time}")
                # Modify the values in the full_gs to the ones of the GHOST
                full_gs[row+jolly][gs_track_column-1] = "=IMAGE(\"" + cd.get_ghost_mii(g["href"]) + "\")" # Mii image link, taken from chadsoft, mettere formula =IMAGE([link])
                full_gs[row+jolly][gs_track_column] = new_time
                full_gs[row+jolly][gs_track_column+1] = "'"+g["dateSet"][:10]
                full_gs[row+jolly][gs_track_column+3] = "=HYPERLINK(\"" + cd.get_ghost_link(g["href"]) + "\"; \"Sì\")" # Ghost info, taken from chadsoft, mettere
                full_gs[row+jolly][gs_track_column+5] = ""
                full_gs[row+jolly][gs_track_column+7] = cd.get_vehicle(g["vehicleId"])
                full_gs[row+jolly][gs_track_column+8] = cd.get_driver(g["driverId"])
                full_gs[row+jolly][gs_track_column+9] = cd.get_controller(g["controller"])



            shifted_LM = cd_LM + datetime.timedelta(minutes=30)
            full_gs[row][gs.LAST_MODIFIED_COLUMN] = shifted_LM.isoformat()

            if from_last_gs_update >= gs.NUM_ROWS_PARTIAL_UPDATE:
                from_last_gs_update = 0
                gs.set_all_values(wks, full_gs)
                full_gs = gs.get_all_values(wks)
                if debug: self.display_msg.emit(f"[SUCCESSFUL] UPDATED {gs.NUM_ROWS_PARTIAL_UPDATE} ROWS OF GOOGLE SHEETS, PROCEEDING WITH THE NEXT BLOCK...")

        gs.set_all_values(wks, full_gs)

    def update_unrestricteds_and_checks(self, wks: gspread.worksheet.Worksheet = None, debug: bool = True) -> None:
        if wks == None: 
            wks = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME, True)
        full_gs = gs.get_all_values(wks)

        # After everything, check the unresctricted
        names = [i[0] for i in full_gs[2:]]
        row = 1
        for name in names:
            if self.isInterruptionRequested(): return
            row += 1
            current_row = full_gs[row]

            complete_norm = True
            complete_unr = True

            for trackId, categories in gs.RT_CATEGORIES.items():
                if self.isInterruptionRequested(): return
                track_has_sc_glitch = False
                for i in range(len(categories) - 1):
                    try:
                        this_gs_time = current_row[gs.get_track_column(trackId, categories[i])]
                        this_time = gs.get_timedelta_from_timestring(this_gs_time)
                    except:
                        if categories[i] in [0, 2, -1]: complete_norm = False
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
                        if debug: self.display_msg.emit(f"[UNRESTRICTED] Better time in worst category found at row {row}:")

                if not track_has_sc_glitch: complete_unr = False

            if complete_norm: complete_unr = True
            full_gs[row][gs.CHECK_FULL_3LAP_NORMAL_COLUMN] = complete_norm
            full_gs[row][gs.CHECK_FULL_3LAP_UNRESTRICTED_COLUMN] = complete_unr

            if debug:
                if complete_norm: self.display_msg.emit(f"[3LAP NORMAL]       is complete: {complete_norm} at row {row}")
                if complete_unr:  self.display_msg.emit(f"[3LAP UNRESTRICTED] is complete: {complete_unr} at row {row}")

        gs.set_all_values(wks, full_gs)

    def update_everything(self) -> None:
        wks, feedback = gs.get_worksheet(SERVICE_KEY_FILENAME, GOOGLE_SHEET_KEY, WORKSHEET_NAME)
        if feedback:
            self.display_msg.emit(feedback)
        self.update_3laps(wks)
        self.update_unrestricteds_and_checks(wks)

    def run(self):
        if self.isInterruptionRequested(): return
        if self.mode == 0:
            self.update_everything()
        elif self.mode == 1:
            self.update_3laps()
        elif self.mode == 2:
            self.update_unrestricteds_and_checks()


