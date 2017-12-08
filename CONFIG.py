import os

DATA_DIR = "DATA/"
TESTCASE_DIR = DATA_DIR + "TESTCASE/"
SUBMISSION_DIR = DATA_DIR + "SUBMISSION/"

TEMP_DIR = DATA_DIR + "TEMP/"

TESTCASE_FILE = "test.py"


for dir in [DATA_DIR, TESTCASE_DIR, SUBMISSION_DIR, TEMP_DIR]:
    if not os.path.exists(dir):
        os.makedirs(dir)
