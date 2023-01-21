# Imports
import os
from datetime import datetime
import array as arr
# Local Imports
import func.main as fMain
import func.anilist_request as fReq

fMain.logString("Imported func.anilist_getMedia", "")

# Main Function
def getMediaEntries(mediaType, paramvals):
    # Vars and Objects
    userMal = None
    filepath = str(paramvals['root'])
    entryLog = str(paramvals['log'])
    accessToken = str(paramvals['access_tkn'])
    userID = int(paramvals['user_id'])
    useOAuth = bool(paramvals['use_auth'])
    isSepNsfw = bool(paramvals['sep_nsfw'])
    isClearFile = bool(paramvals['clear_files'])
    if paramvals['user_mal']:
        userMal = str(paramvals['user_mal'])

    returnMedia = {}
    entryID = [] # List of IDs, to prevent duplicates
    jsonToDump = [] # List of Json dict object of results
    jsonToDumpNsfw = [] # List of Json dict object of results, 18+ entries
    isAdult = False # Bool for 'isAdult' flag from Anilist
    isExportMal = True # Export to MAL backup.
    nsfwToggle = 0 # 0=main, 1=nsfw. For arrays toggle
    source = "anilist_get" + mediaType
    fMain.logString("All vars are initiated", source)

    if not userMal:
        isExportMal = False
        fMain.logString("Skipping MAL export.", source)
    else:
        fMain.logString(f"MAL Username: {userMal}", source)

    # Declare filepaths
    if mediaType == "ANIME":
        outputMedia = os.path.join(filepath, "output", "anime_" + datetime.now().strftime("%Y-%m-%d") + ".json")
        xmlMedia = os.path.join(filepath, "output", "anime_" + datetime.now().strftime("%Y-%m-%d") + ".xml")
        outputMedia18 = os.path.join(filepath, "output", "nsfw_anime_" + datetime.now().strftime("%Y-%m-%d") + ".json")
        xmlMedia18 = os.path.join(filepath, "output", "nsfw_anime_" + datetime.now().strftime("%Y-%m-%d") + ".xml")
    else:
        outputMedia = os.path.join(filepath, "output", "manga_" + datetime.now().strftime("%Y-%m-%d") + ".json")
        xmlMedia = os.path.join(filepath, "output", "manga_" + datetime.now().strftime("%Y-%m-%d") + ".xml")
        outputMedia18 = os.path.join(filepath, "output", "nsfw_manga_" + datetime.now().strftime("%Y-%m-%d") + ".json")
        xmlMedia18 = os.path.join(filepath, "output", "nsfw_manga_" + datetime.now().strftime("%Y-%m-%d") + ".xml")
    
    # Clear files if already existing
    fMain.logString(f"Will clear output files: {isClearFile}")
    if isClearFile:
        try:
            fMain.logString("Deleting output files..")
            fMain.deleteFile(outputMedia)
            fMain.deleteFile(xmlMedia)
            fMain.deleteFile(outputMedia18)
            fMain.deleteFile(xmlMedia18)
            fMain.logString("Done deleting output files!")
        except Exception as e:
            fMain.logString(f"Clear File error: {e}", source)

    # Check if not existing
    if not (os.path.exists(outputMedia)):
        # Get JSON object
        if useOAuth:
            jsonMedia = fReq.anilist_userlist(accessToken, userID, mediaType)
        else:
            jsonMedia = fReq.anilist_userlist_public(userID, mediaType)

        # Check if not null
        if jsonMedia is not None:
            listMedia = jsonMedia["data"]["MediaListCollection"]["lists"]

            # Create vars
            # Count Manga entries
            cTotal = arr.array('i', [0, 0])
            cWatch = arr.array('i', [0, 0])
            cComplete = arr.array('i', [0, 0])
            cHold = arr.array('i', [0, 0])
            cDrop = arr.array('i', [0, 0])
            cPtw = arr.array('i', [0, 0])

            # Start generating JSON and XML..
            fMain.logString("Generating export files..", source)

            # Log duplicate entries
            fMain.logFile(entryLog, f'{mediaType} Entries')
            entryID.clear() # Clear list

            # Iterate over the MediaCollection List
            for anime in listMedia:
                # Get entries
                animeInfo = anime["entries"]
                # Iterate over the anime information, inside the entries
                for entry in animeInfo:
                    # Get Anilist ID
                    anilistID = entry["media"]["id"]
                    # Get Anilist Status
                    AnilistStatus = fMain.validateStr(entry["status"])
                    # Get isAdult flag
                    isAdult = bool(entry["media"]["isAdult"])

                    # Check if already exists
                    if anilistID in entryID:
                        fMain.logFile(entryLog, f'Skipped: {str(anilistID)}, Duplicate {mediaType} entry.')
                        continue
                    else:
                        entryID.append(anilistID)

                    # Write to json file
                    if isAdult and isSepNsfw:
                        jsonToDumpNsfw.append(fMain.entry_json(entry, mediaType))
                    else:
                        jsonToDump.append(fMain.entry_json(entry, mediaType))

                    # Write to MAL Xml File
                    malID = fMain.validateInt(entry["media"]["idMal"])
                    if malID != '0' and isExportMal:
                        # Get XML strings
                        xmltoWrite = fMain.entry_xmlstr(mediaType, malID, entry, str(AnilistStatus))
                        # Write to xml file
                        if isAdult and isSepNsfw:
                            nsfwToggle = 1
                            fMain.write_append(xmlMedia18, xmltoWrite)
                        else:
                            nsfwToggle = 0
                            fMain.write_append(xmlMedia, xmltoWrite)
                        
                        # Add count
                        cTotal[nsfwToggle] += 1
                        if (AnilistStatus == "COMPLETED"):
                            cComplete[nsfwToggle] += 1
                        elif (AnilistStatus == "PAUSED"):
                            cHold[nsfwToggle] += 1
                        elif (AnilistStatus == "CURRENT"):
                            cWatch[nsfwToggle] += 1
                        elif (AnilistStatus == "DROPPED"):
                            cDrop[nsfwToggle] += 1
                        elif (AnilistStatus == "PLANNING"):
                            cPtw[nsfwToggle] += 1
                        elif (AnilistStatus == "REPEATING"):
                            cWatch[nsfwToggle] += 1

            # Dump JSON to file..
            if (fMain.dumpToJson(jsonToDump, outputMedia)):
                fMain.logString("Succesfully created json file!", source)
            else:
                fMain.logString("Error with creating json file!", source)
            fMain.logString(f"Done with {mediaType} JSON file..", source)

            # Dump JSON (nsfw) to file..
            if isSepNsfw:
                if (fMain.dumpToJson(jsonToDumpNsfw, outputMedia18)):
                    fMain.logString("Succesfully created json file!", source)
                else:
                    fMain.logString("Error with creating json file!", source)
                fMain.logString(f"Done with {mediaType} JSON file..", source)
            
            # Write to MAL xml file
            if isExportMal:
                fMain.logString(f"Finalizing {mediaType} XML file..", source)
                malprepend = ""
                malprepend18 = ""

                mediastring = ""
                mediaexport = '0'
                mediawatchread = ""
                if mediaType == "ANIME":
                    mediastring = "anime"
                    mediaexport = '1'
                    mediawatchread = "watch"
                else:
                    mediastring = "manga"
                    mediaexport = '2'
                    mediawatchread = "read"

                fMain.write_append(xmlMedia, f'</my{mediastring}list>')
                if isSepNsfw:
                    fMain.write_append(xmlMedia18, f'</my{mediastring}list>')

                # Total counts for MAL
                fMain.logString(f"Prepend 'myinfo' to {mediaType} XML file..", source)
                malprepend = f'<?xml version="1.0" encoding="UTF-8" ?>\n<my{mediastring}list>\n'
                malprepend += '\t<myinfo>\n'
                malprepend += '\t\t' + fMain.toMalval('', 'user_id') + '\n'
                malprepend += '\t\t' + fMain.toMalval(userMal, 'user_name') + '\n'
                malprepend += '\t\t' + fMain.toMalval(mediaexport, 'user_export_type') + '\n'

                malprepend18 = malprepend # Same prepend values as 'main'
                # Count for 'main'
                malprepend += '\t\t' + fMain.toMalval(str(cTotal[0]), f'user_total_{mediastring}') + '\n'
                malprepend += '\t\t' + fMain.toMalval(str(cWatch[0]), f'user_total_{mediawatchread}ing') + '\n'
                malprepend += '\t\t' + fMain.toMalval(str(cComplete[0]), 'user_total_completed') + '\n'
                malprepend += '\t\t' + fMain.toMalval(str(cHold[0]), 'user_total_onhold') + '\n'
                malprepend += '\t\t' + fMain.toMalval(str(cDrop[0]), 'user_total_dropped') + '\n'
                malprepend += '\t\t' + fMain.toMalval(str(cPtw[0]), f'user_total_planto{mediawatchread}') + '\n'
                # Count for 'nsfw'
                if isSepNsfw:
                    malprepend18 += '\t\t' + fMain.toMalval(str(cTotal[1]), f'user_total_{mediastring}') + '\n'
                    malprepend18 += '\t\t' + fMain.toMalval(str(cWatch[1]), f'user_total_{mediawatchread}ing') + '\n'
                    malprepend18 += '\t\t' + fMain.toMalval(str(cComplete[1]), 'user_total_completed') + '\n'
                    malprepend18 += '\t\t' + fMain.toMalval(str(cHold[1]), 'user_total_onhold') + '\n'
                    malprepend18 += '\t\t' + fMain.toMalval(str(cDrop[1]), 'user_total_dropped') + '\n'
                    malprepend18 += '\t\t' + fMain.toMalval(str(cPtw[1]), f'user_total_planto{mediawatchread}') + '\n'

                malprepend += '\t</myinfo>\n'
                malprepend18 += '\t</myinfo>\n'

                fMain.line_prepender(xmlMedia, malprepend)
                if isSepNsfw:
                    fMain.line_prepender(xmlMedia18, malprepend18)
                fMain.logString(f"Done with {mediaType} XML file..", source)

            # Done anime/manga
            fMain.logString("Done! File generated: " + outputMedia, source)
            if isExportMal:
                fMain.logString("Done! File generated: " + xmlMedia, source)
            if isSepNsfw:
                fMain.logString("Done! File generated: " + outputMedia18, source)
                if isExportMal:
                    fMain.logString("Done! File generated: " + xmlMedia18, source)

    # Already existing!
    else:
        fMain.logString(f"{mediaType} file already exist!: " + outputMedia, source)
    
    returnMedia = {'main':outputMedia, 'nsfw':outputMedia18}
    return returnMedia
