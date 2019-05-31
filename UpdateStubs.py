# coding: utf-8

from common_util import *
from pathlib import Path

import os
import argparse
import sys

MIN_PYTHON = (3, 7)

data_handler = {'declarations': ['GlobalDeclarationsList.xlsx', 'Global Declarations', 'A:B', OFF],
                'functions': ['RTEFunctionCalls.xlsx', 'RTE Function Calls', 'A:B', OFF]}


def filter_data(stubs_folder):
    for root, dirs, files in os.walk(Path(stubs_folder)):
        for file in files:
            if file.endswith('.c'):
                module_name = file[:-2].lower()
                filename = os.path.join(root, file)

                declarations_data_frame = read_excel_file(data_handler['declarations'][0],
                                                          data_handler['declarations'][1:4])
                declarations_data_frame['TargetModule'] = declarations_data_frame.TargetModule.astype(str).str.lower()
                declarations_filtered_data = declarations_data_frame[
                    declarations_data_frame['TargetModule'] == module_name
                ]

                if len(declarations_filtered_data.head(1)) == 0:
                    print('No global declarations for {}'.format(file[:-2]))
                else:
                    string = '<< Start of include and declaration area >>'
                    column_name = 'Declarations'
                    skip_count = 2
                    if module_name == 'acc_main' or module_name == 'acc_50ms':
                        skip_count += 3
                    spaces = ''

                    success = insert_lines_of_code('declarations', filename, declarations_filtered_data[column_name],
                                                   string, skip_count, spaces)

                    if success:
                        print('Finished inserting global declarations for {}'.format(file[:-2]))
                    else:
                        print('Failed to insert global declarations for {}'.format(file[:-2]))

                functions_data_frame = read_excel_file(data_handler['functions'][0], data_handler['functions'][1:4])
                functions_data_frame['TargetModule'] = functions_data_frame.TargetModule.astype(str).str.lower()
                functions_filtered_data = functions_data_frame[functions_data_frame['TargetModule'] == module_name]

                if len(functions_filtered_data.head(1)) == 0:
                    print('No RTE read/write calls for {}'.format(file[:-2]))
                else:
                    string = '<< Start of runnable implementation >>'
                    column_name = 'FunctionCalls'
                    skip_count = 3
                    if module_name == 'acc_main' or module_name == 'acc_50ms':
                        skip_count += 3
                    spaces = '  '

                    success = insert_lines_of_code('functions', filename, functions_filtered_data[column_name],
                                                   string, skip_count, spaces)
                    if success:
                        print('Finished inserting RTE read and write function calls for {}'.format(file[:-2]))
                    else:
                        print('Failed to insert RTE read and write function calls for {}'.format(file[:-2]))


if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required. Please check your Python version.\n" % MIN_PYTHON)

# Read arguments
parser = argparse.ArgumentParser()
parser.add_argument('-s', dest='stubs_folder', help='stubs folder', default='Stubs/')
args = parser.parse_args()

if not os.path.exists(args.stubs_folder):
    print('{} not found!'.format(args.stubs_folder))
    print('Please make sure {} is in the script folder!'.format(args.stubs_folder))
elif not os.path.exists(data_handler['declarations'][0]):
    print('{} not found!'.format(data_handler['declarations'][0]))
    print('Please run the PrepareData script first!')
elif not os.path.exists(data_handler['functions'][0]):
    print('{} not found!'.format(data_handler['functions'][0]))
    print('Please run the PrepareData script first!')
else:
    filter_data(args.stubs_folder)
