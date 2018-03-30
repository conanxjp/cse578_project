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
CATEGORY  = "categories.txt"
# paths for prepareReviews
DICT      = "glove.42B.300d.txt"
