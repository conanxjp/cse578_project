"""
All constants configuration for the project is here
"""
import os
from pathlib import Path




###################################################
#   file system configuration                     #
###################################################
ROOT_PATH = os.path.abspath(os.path.join(__file__ ,"../../../.."))
DATA_PATH = "/data/yelp_dataset/"
# paths for preprocess
BUSINESS  = "business.json"
REVIEW    = "review.json"
USER      = "user.json"
CHECKIN   = "checkin.json"
STATE     = "state2abb.json"
CITY      = "us-cities.json"
ZIP_CODE  = "zip-code.xml"
CATEGORY  = "categories_new.txt"
# paths for prepareReviews
DICT      = "glove.6B.300d.txt"
# path for hunspell configurations
HUNSPELL_PATH = "/usr/share/hunspell/"
HUNSPELL_DICT = ["en_US.dic", "en_US.aff"]
