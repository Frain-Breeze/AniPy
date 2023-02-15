# imports
import os
import argparse
# Local Imports
import func.main as fMain
import func.anilist_request as fReq
from func.anilist_getMedia import getMediaEntries
import func.trim_list as fTrim
import func.getNotOnTachi as fNotOnTachi

# App Properties
appVersion = '1.20'
appMode = 'AniPy (Advanced)'
# Declare variables
fMain.logger("Define Filepaths..")
# Paths for Files
PROJECT_PATH = os.path.dirname(os.path.realpath(__file__)) #os.path.dirname(sys.executable)
fMain.logger("Current path: " + PROJECT_PATH)
# Filepaths
anilistConfig = os.path.join(PROJECT_PATH, "anilistConfig.json")
entryLog = os.path.join(PROJECT_PATH, "output", "entries.log") # Log entries

# Create 'output' directory
if not os.path.exists('output'):
    os.makedirs('output')

parser = argparse.ArgumentParser(description='AniPy parameters and flags')

# Required params
# Optional params
parser.add_argument('-user', type=str, help='Anilist Username')
parser.add_argument('-mal', type=str, help='MAL Username') 
parser.add_argument('-tachi', type=str, help='Tachiyomi legacy backup')
# Flags
parser.add_argument('--a', action='store_true', help='Use Authenticated mode. Disregard `user` parameter.')
parser.add_argument('--t', action='store_true', help='Trim generated files.')
parser.add_argument('--n', action='store_true', help='Separate NSFW entries on output files.')
parser.add_argument('--c', action='store_true', help='Clear existing output files.')
parser.add_argument('--m', action='store_true', help='Use Anilist as MAL username, if MAL username is not provided.')

# Parse args
args = parser.parse_args()

# Vars for Authentication
ANICLIENT = ""
ANISECRET = ""
useOAuth = False
accessToken = ""
# User vars
userID = 0
userAnilist = None
userMal = None
isSepNsfw = False # Separate nsfw entries on output
isClearFile = False # Clear existing output files
# Output file names
outputAnime = []
outputManga = []

# Check boolean flags
if (args.n): # Separate NSFW Entries
    isSepNsfw = True
if (args.c):
    isClearFile = True

# Check parameters
if args.user is not None:
    userAnilist = str(args.user)

if args.mal is not None:
    userMal = str(args.mal)

if not userMal or userMal.isspace():
    if (args.m):
        if userAnilist and not userAnilist.isspace():
            userMal = userAnilist

if not userMal or userMal.isspace():
    fMain.logger("No MAL username provided! Certain features will not work.")

# Check if using authentication
if (args.a):
    useOAuth, ANICLIENT, ANISECRET, REDIRECT_URL = fReq.setup_config(anilistConfig)

    if not useOAuth:
      accessToken = ""
    
    if useOAuth:
      code = fReq.request_pubcode(ANICLIENT, REDIRECT_URL)
      accessToken = fReq.request_accesstkn(ANICLIENT, ANISECRET, REDIRECT_URL, code)

    if accessToken:
      useOAuth = True
      fMain.logger("Has access token!")
    else:
      useOAuth = False
      fMain.logger("Cannot Authenticate! Will use Public List.")
    
# Check whether authenticated, or use public Username
if not useOAuth:
    fMain.logger("Fetch user ID using Anilist username..")
    accessToken = ""
    if userAnilist:
        userID = fReq.anilist_getUserID(userAnilist) # Fetch UserID using username. Public mode.
    else:
        fMain.logger("No Anilist username provided!")
else:
    fMain.logger("Getting User ID, from Authenticated user..")
    userID = fReq.anilist_getUserID_auth(accessToken)

# Default to Public mode if user ID is invalid
if userID is not None:
    if (userID < 1):
        fMain.logger(f'Invalid user ID: {userID}!')
else:
    userID = -1
    fMain.logger("User Id cannot be fetched!")

# Display User Info
if userAnilist and userID > 0:
    fMain.logger(f"User: {str(userAnilist)} ({str(userID)})")
else:
    fMain.logger(f"User: {str(userAnilist)}")

# Delete prev files
fMain.deleteFile(entryLog)

# Initiate parameter values
paramvals = {
    'root': PROJECT_PATH,
    'log': entryLog,
    'access_tkn': accessToken,
    'user_anilist': userAnilist,
    'user_mal': userMal,
    'user_id': userID,
    'use_auth': useOAuth,
    'sep_nsfw': isSepNsfw,
    'clear_files': isClearFile
}

# Request anime list
outputAnime = getMediaEntries("ANIME", paramvals)

# Request manga list
outputManga = getMediaEntries("MANGA", paramvals)

# Trim List
if args.t:
    fTrim.trim_results(PROJECT_PATH, outputAnime.get('main'), outputManga.get('main'), False)
    if isSepNsfw:
        fTrim.trim_results(PROJECT_PATH, outputAnime.get('nsfw'), outputManga.get('nsfw'), True)

# Get Entries not on Tachi
tempTachi = str(args.tachi)
if tempTachi:
    fNotOnTachi.getNotOnTachi(outputManga.get('main'), tempTachi, False)
    if isSepNsfw:
        fNotOnTachi.getNotOnTachi(outputManga.get('nsfw'), tempTachi, True)

#fMain.inputX("Press <Enter> to exit..", "")
