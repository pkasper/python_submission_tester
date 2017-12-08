from CONFIG import *

import argparse
import os
import sys
import re
import testcase
import numpy as np
import pandas as pd
from tabulate import tabulate

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--submission", "-s", help='Directory to the submissions')
    arg_parser.add_argument("--testcase", "-t", help='Path to the testcase folder')
    command_line_args = vars(arg_parser.parse_args())

    submission_dir = SUBMISSION_DIR + command_line_args['submission'] + "/"
    testcase_dir = TESTCASE_DIR + command_line_args['testcase'] + "/"
    if not os.path.isdir(submission_dir):
        print("Submission directory does not exist")
        exit(-1)
    if not os.path.isdir(testcase_dir):
        print("Testcase directory does not exist")
        exit(-1)

    tests = {}

    palme_submissions = os.listdir(submission_dir)


    for palme_submission in palme_submissions:
        matr_match = re.match(string=palme_submission, pattern="Matrikelnummer_(?P<matr>[0-9]*)_")
        mat_nr = matr_match.group("matr")
        last_submission = list(os.listdir(submission_dir + palme_submission))[-1]

        submission_path = submission_dir + palme_submission + "/" + last_submission
        tests[mat_nr] = testcase.Testcase(mat_nr, submission_path, testcase_dir)

    total_results = dict()

    for mat_nr, test in sorted(tests.items()):
        #print("Starting tests for {mat_nr}".format(mat_nr=mat_nr))
        total_results[mat_nr] = test.run()
        #print("Completed tests for {mat_nr}".format(mat_nr=mat_nr))

    total_results = total_results

    results_df = pd.DataFrame.from_dict(total_results).transpose()
    results_df['rate'] = results_df.mean(axis=1)

    print(tabulate(results_df, headers="keys", tablefmt="grid"))