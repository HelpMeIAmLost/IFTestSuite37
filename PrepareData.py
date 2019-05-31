# coding: utf-8

from common_util import *

import numpy as np
import argparse
import sys

MIN_PYTHON = (3, 7)

# Column header indices
target_module_col = 0
in_out_col = 1
source_module_col = 2
source_signal_col = 3
raw_target_signal_col = 4
raw_data_type_col = 5
destination_module_col = 6
destination_signal_col = 7
fixed_data_type_col = 8
fixed_target_signal_col = 9
raw_array_size_col = 10
module_signal_col = 11
fixed_array_size_col = 12
# The following data frame columns are for function calls only
fixed_source_signame_col = 13
source_module_signal_col = 14

#             Sheet name , Use cols , Skip rows
#             [0]        , [1]      , [2]
data_range = ['IF Information', 'A:M', OFF]
module = {'CAN_VP': ['CANRx_', 'IPCRx_', 'LOCALCAN_', 'CANG4_', 'IPC_'],
          'CTL': ['Ctl_'],
          'Others': ['Feat_']}
CAN_VP = {'CAN', 'VP', 'DebugCAN'}
CTL = {'EGI', 'TCU_CVT', 'TCU_Shift', 'VDC'}
skip_list = {'RTE', 'FWBSW', 'NVMBSW', 'CONST', 'FMWF',
             'Ground', 'SWBSW', 'SSM', 'Input_Getway',
             'RTE_Gateway', 'FMWR1'}

unwantedString = {'nan', '-', '', 'パラ', 'OFF', 'ON'}


def getModPosKey(df, row, col):
    index = df.iat[row, col]
    if index in CAN_VP:
        return 'CAN_VP'
    elif index in CTL:
        return 'CTL'
    else:
        return 'Others'


def create_function_name(df, row, posKey, posVal, varName, name, insideVarName):
    index_only = True
    # Check if the signal is a map/table
    if str(df.iat[row, fixed_array_size_col]).find('][') != -1:
        array_size = '-1'
    else:
        if insideVarName.find('[') == -1:
            index_only = False

        check_insideVarName = '( {}'.format(insideVarName)
        if check_insideVarName.find('( t_') == -1:
            array_size = str(df.iat[row, fixed_array_size_col]).replace('[', '')
            array_size = array_size.replace(']', '')
        else:
            array_size = '1'

    string = '{}{}{}'.format(name, module[posKey][posVal] if posKey == 'CAN_VP' else '', varName)

    state = df.iat[row, in_out_col]
    if state == "IN":
        if array_size == 'nan' or array_size == '1':
            if name == 'Rte_Read_RP_':
                string = string + '( &' + insideVarName + ' );'
            else:
                string = string + '( ' + insideVarName + ' );'
            return string
        elif array_size == '-1':
            string = string + '( ' + insideVarName + ' );'
            return string
        else:
            if name == 'Rte_Read_RP_' and index_only:
                string = string + '( &' + insideVarName + ' );'
            else:
                string = string + '_Arr' + array_size + '( ' + insideVarName + ' );'
            return string
    else:
        if array_size == 'nan' or array_size == '1':
            if name == 'Rte_Read_RP_':
                string = string + '( &' + insideVarName + ' );'
            else:
                string = string + '( ' + insideVarName + ' );'
            return string
        else:
            # if name == 'Rte_Read_RP_':
            #     string = string + '( &' + insideVarName + ' );'
            # else:
            #     string = string + '_Arr' + array_size + '( ' + insideVarName + ' );'
            if index_only:
                string = string + '( &' + insideVarName + ' );'
            else:
                string = string + '_Arr' + array_size + '( ' + insideVarName + ' );'
            return string


def create_function_calls(cdl_data_frame):
    # Data Manipulation
    function_call_list = []
    target_module_list = []
    # target_module = 'target_module'
    source_signame = 'source_signame'
    fixed_source_signame = 'fixed_source_signame'
    source_module_signal = 'source_module_signal'
    # Function call creation
    rte_read = "Rte_Read_RP_"
    rte_write = "Rte_Write_PP_"

    print('Creating a list of RTE functions calls per module..')
    function_call_data_frame = cdl_data_frame
    # # Convert target_model_name text to lowercase
    # function_call_data_frame['target_model_name'] = function_call_data_frame.target_model_name.astype(str).str.lower()

    # Remove () and other unwanted text in the source_modname column
    function_call_data_frame['source_modname'] = reg_replace(function_call_data_frame, 'source_modname', r'[\(\)]', '')
    for i in unwantedString:
        function_call_data_frame['source_modname'] = replace(function_call_data_frame, 'source_modname', i, '')

    # Create a new column with just the signal name
    function_call_data_frame[fixed_source_signame] = reg_replace(
        function_call_data_frame, source_signame, r'\[(.*){1,3}\]\[(.*){1,3}\]|\[(.*){1,3}\]', '')
    function_call_data_frame[fixed_source_signame] = reg_replace(
        function_call_data_frame, fixed_source_signame, r'^(\d+)|([\u4e00-\u9fff]+)|([\u3040-\u309Fー]+)|([\u30A0-\u30FF]+)|(-)$', '')
    # Remove unwanted text in the new column fixed_source_signame
    for i in unwantedString:
        function_call_data_frame[fixed_source_signame] = replace(function_call_data_frame, fixed_source_signame, i, '')

    function_call_data_frame[source_module_signal] = function_call_data_frame['source_modname'] + '_' + \
        function_call_data_frame[fixed_source_signame]

    for row in range(function_call_data_frame.shape[0]):
        # Skip modules in skip_list
        if function_call_data_frame.iat[row, source_module_col] in skip_list:
            continue
        target_module = function_call_data_frame.iat[row, target_module_col]
        state = function_call_data_frame.iat[row, in_out_col]
        input_from = function_call_data_frame.iat[row, source_module_col]
        input_signal_name = function_call_data_frame.iat[row, source_signal_col]
        raw_target_signal_name = function_call_data_frame.iat[row, raw_target_signal_col]
        # raw_data_type = function_call_data_frame.iat[row, raw_data_type_col]
        output_to = function_call_data_frame.iat[row, destination_module_col] \
            if function_call_data_frame.iat[row, destination_module_col] != 'DebugCAN' else 'DBG'
        destination_signal_name = function_call_data_frame.iat[row, destination_signal_col]
        fixed_data_type = function_call_data_frame.iat[row, fixed_data_type_col]
        signal_name = function_call_data_frame.iat[row, fixed_target_signal_col]
        raw_array_size = function_call_data_frame.iat[row, raw_array_size_col]
        module_signal = function_call_data_frame.iat[row, module_signal_col]
        # fixed_array_size = function_call_data_frame.iat[row, fixed_array_size_col]
        fixed_source_signame = function_call_data_frame.iat[row, fixed_source_signame_col]
        source_module_signal = function_call_data_frame.iat[row, source_module_signal_col]
        if state == "IN":
            if signal_name != '' and fixed_source_signame != '':
                # Check if the input signal is from CAN or VP
                posKey = getModPosKey(function_call_data_frame, row, source_module_col)

                is_array = False
                array_check = False
                if str(raw_array_size).find('[') != -1:
                    is_array = True

                    check_raw_array_size = function_call_data_frame.iat[row - 1, raw_array_size_col]
                    check_signal_name = function_call_data_frame.iat[row - 1, fixed_target_signal_col]
                    if signal_name != check_signal_name and str(check_raw_array_size).find('[') != -1:
                        array_check = True
                else:  # Check the data before if it is an array signal
                    check_raw_array_size = function_call_data_frame.iat[row - 1, raw_array_size_col]
                    if str(check_raw_array_size).find('[') != -1:
                        array_check = True

                if array_check:
                    array_input_from = function_call_data_frame.iat[row - 1, source_module_col]
                    array_posKey = getModPosKey(function_call_data_frame, row - 1, source_module_col)
                    array_module_signal = function_call_data_frame.iat[row - 1, module_signal_col]
                    array_signal_name = function_call_data_frame.iat[row - 1, fixed_target_signal_col]

                    if array_input_from == 'CAN':  # CAN
                        function_call_list.append(create_function_name(
                            function_call_data_frame, row - 1, array_posKey, 0, array_module_signal, rte_write,
                            '{}_{}'.format('PreCAN', array_signal_name)))
                        target_module_list.append('PreCAN')
                    elif array_input_from == 'VP':  # IPC
                        function_call_list.append(create_function_name(
                            function_call_data_frame, row - 1, array_posKey, 1, array_module_signal, rte_write,
                            '{}_{}'.format('PreIPC', array_signal_name)))
                        target_module_list.append('PreIPC')

                if posKey == 'CAN_VP':
                    db_connection = create_connection('interface.db')
                    can_signal_info = execute_sql(db_connection, '''SELECT * FROM external_signals
                    WHERE link=?''', ('{}_{}'.format(input_from, input_signal_name),), select=True, just_one=True
                                                  )
                    if can_signal_info is not None:
                        if input_from == "CAN":  # CAN
                            # Rte_Read from CANRx interface signal
                            function_call_list.append(create_function_name(
                                function_call_data_frame, row, posKey, 0, module_signal, rte_read, module_signal))
                            target_module_list.append(target_module)

                            if can_signal_info[4] == 1 or can_signal_info[4] == 2:
                                posKey_index = 2
                            elif can_signal_info[4] == 3 or can_signal_info[4] == 4:
                                posKey_index = 3
                            else:
                                # invalid CAN channel
                                continue
                            CAN_module = 'PreCAN'
                            message_id = can_signal_info[0][:6]
                            message_name = '{}_{}'.format(message_id, can_signal_info[0])
                        else:  # IPC
                            # Rte_Read from IPCRx interface signal
                            function_call_list.append(create_function_name(
                                function_call_data_frame, row, posKey, 1, module_signal, rte_read, module_signal))
                            target_module_list.append(target_module)

                            posKey_index = 4
                            CAN_module = 'PreIPC'
                            message_id = 'IPC{}'.format(can_signal_info[0][3:6])
                            message_name = '{}_IPC{}'.format(message_id, can_signal_info[0][3:])

                        # Optional, declare a local variable for data conversion
                        convert_it = False
                        temp_variable = ''
                        if str(can_signal_info[8]).find('.') != -1 and fixed_data_type == 'float32':
                            temp_variable = 't_{}_{}'.format(message_id, signal_name)
                            if str(can_signal_info[10]).find('-') != -1:
                                if can_signal_info[7] <= 8:
                                    function_call_list.append('sint8 {};'.format(temp_variable))
                                elif can_signal_info[7] <= 16:
                                    function_call_list.append('sint16 {};'.format(temp_variable))
                                elif can_signal_info[7] <= 32:
                                    function_call_list.append('sint32 {};'.format(temp_variable))
                            else:
                                if can_signal_info[7] <= 8:
                                    function_call_list.append('uint8 {};'.format(temp_variable))
                                elif can_signal_info[7] <= 16:
                                    function_call_list.append('uint16 {};'.format(temp_variable))
                                elif can_signal_info[7] <= 32:
                                    function_call_list.append('uint32 {};'.format(temp_variable))
                            target_module_list.append(CAN_module)
                            convert_it = True

                        # Rte_Read from CAN/IPC
                        function_call_list.append(
                            create_function_name(
                                function_call_data_frame, row, posKey, posKey_index,
                                message_name,
                                rte_read,
                                temp_variable if convert_it else '{}_{}'.format(CAN_module, raw_target_signal_name)
                            )
                        )
                        target_module_list.append(CAN_module)

                        # Optional data conversion
                        if convert_it:
                            function_call_list.append('{}_{} = ((float32)({}) * {}) + ({});'.format(
                                CAN_module,
                                raw_target_signal_name,
                                temp_variable,
                                can_signal_info[8],
                                float(can_signal_info[9])
                            ))
                            target_module_list.append(CAN_module)

                        # Rte_Write to RTE interface signal
                        if not is_array:
                            if input_from == "CAN":  # CAN
                                function_call_list.append(create_function_name(
                                    function_call_data_frame, row, posKey, 0, module_signal, rte_write,
                                    '{}_{}'.format(CAN_module, signal_name)))
                                target_module_list.append(CAN_module)
                            else:  # IPC
                                function_call_list.append(create_function_name(
                                    function_call_data_frame, row, posKey, 1, module_signal, rte_write,
                                    '{}_{}'.format(CAN_module, signal_name)))
                                target_module_list.append(CAN_module)

                    db_connection.close()
                else:
                    # Rte_Read from interface signal
                    function_call_list.append(create_function_name(
                        function_call_data_frame, row, posKey, 0, source_module_signal, rte_read, module_signal))
                    target_module_list.append(target_module)
            else:
                print('Module: {} - Input Signal: {} - Output Signal: {}'.format(
                    target_module,
                    signal_name if signal_name != '' else 'None',
                    fixed_source_signame if fixed_source_signame != '' else 'None')
                )
        else:
            if signal_name != '' and destination_signal_name != '':
                # Get module classification
                posKey = getModPosKey(function_call_data_frame, row, source_module_col)

                # Rte_Write to interface signal
                function_call_list.append(create_function_name(
                    function_call_data_frame, row, posKey, 0, module_signal, rte_write, module_signal))
                target_module_list.append(target_module)

                # Preserve module classification for later use
                old_posKey = posKey

                posKey = getModPosKey(function_call_data_frame, row, destination_module_col)
                if posKey == 'CAN_VP':
                    db_connection = create_connection('interface.db')
                    can_signal_info = execute_sql(db_connection, '''SELECT * FROM external_signals
                    WHERE link=?''', ('{}_{}'.format(output_to, destination_signal_name),), select=True, just_one=True
                                                  )
                    if can_signal_info is not None:
                        if output_to == 'CAN' or output_to == 'DBG':  # CAN or DebugCAN
                            message_name = '{}_{}'.format(can_signal_info[0][:6], can_signal_info[0])
                            if can_signal_info[4] == 1 or can_signal_info[4] == 2:
                                # LOCALCAN
                                posKey_index = 2
                            elif can_signal_info[4] == 3 or can_signal_info[4] == 4:
                                # CANG4
                                posKey_index = 3
                            else:
                                # Invalid CAN channel
                                continue
                            CAN_module = 'PostCAN'
                            message_id = can_signal_info[0][:6]
                            message_name = '{}_{}'.format(message_id, can_signal_info[0])
                        else:  # VP
                            # IPC
                            posKey_index = 4
                            CAN_module = 'PostIPC'
                            message_id = 'IPC{}'.format(can_signal_info[0][3:6])
                            message_name = '{}_IPC{}'.format(message_id, can_signal_info[0][3:])

                        # Optional, declare a local variable for data conversion
                        convert_it = False
                        temp_data_type = ''
                        temp_variable = ''
                        if str(can_signal_info[8]).find('.') != -1 and fixed_data_type == 'float32':
                            temp_variable = 't_{}'.format(signal_name)
                            if str(can_signal_info[10]).find('-') != -1:
                                if can_signal_info[7] <= 8:
                                    temp_data_type = 'sint8'
                                    function_call_list.append('{} {};'.format(temp_data_type, temp_variable))
                                elif can_signal_info[7] <= 16:
                                    temp_data_type = 'sint16'
                                    function_call_list.append('{} {};'.format(temp_data_type, temp_variable))
                                elif can_signal_info[7] <= 32:
                                    temp_data_type = 'sint32'
                                    function_call_list.append('{} {};'.format(temp_data_type, temp_variable))
                            else:
                                if can_signal_info[7] <= 8:
                                    temp_data_type = 'uint8'
                                    function_call_list.append('{} {};'.format(temp_data_type, temp_variable))
                                elif can_signal_info[7] <= 16:
                                    temp_data_type = 'uint16'
                                    function_call_list.append('{} {};'.format(temp_data_type, temp_variable))
                                elif can_signal_info[7] <= 32:
                                    temp_data_type = 'uint32'
                                    function_call_list.append('{} {};'.format(temp_data_type, temp_variable))
                            target_module_list.append(CAN_module)
                            convert_it = True

                        # Rte_Read from interface signal
                        function_call_list.append(
                            create_function_name(
                                function_call_data_frame, row, old_posKey, 0,
                                module_signal,
                                rte_read,
                                '{}{}'.format(CAN_module, module_signal[len(target_module):])
                            )
                        )
                        target_module_list.append(CAN_module)

                        # Optional data conversion
                        if convert_it:
                            function_call_list.append(
                                '{} = ({})((({}_{} / {}) - ({})) + ({}_{} >= 0.0 ? 0.5 : -0.5));'.format(
                                    temp_variable,
                                    temp_data_type,
                                    CAN_module,
                                    raw_target_signal_name,
                                    can_signal_info[8],
                                    float(can_signal_info[9]),
                                    CAN_module,
                                    raw_target_signal_name
                                )
                            )
                            target_module_list.append(CAN_module)

                            # Rte_Write to CAN/VP signal
                            function_call_list.append(create_function_name(
                                function_call_data_frame, row, posKey, posKey_index,
                                message_name,
                                rte_write,
                                temp_variable))
                        else:
                            # Rte_Write to CAN/VP signal
                            function_call_list.append(create_function_name(
                                function_call_data_frame, row, posKey, posKey_index,
                                message_name,
                                rte_write,
                                '{}_{}'.format(CAN_module, raw_target_signal_name)))
                        target_module_list.append(CAN_module)

                    db_connection.close()
            else:
                print('Module: {} - Input Signal: {} - Output Signal: {}'.format(
                    target_module,
                    signal_name if signal_name != '' else 'None',
                    destination_signal_name if destination_signal_name != '' else 'None')
                )

    function_call_data_frame = pd.DataFrame({'TargetModule': target_module_list, 'FunctionCalls': function_call_list})
    function_call_data_frame.drop_duplicates(keep='first', inplace=True)

    write_to_excel(function_call_data_frame, 'RTEFunctionCalls.xlsx', 'RTE Function Calls')
    print('Done!')


def create_global_declarations(cdl_data_frame):
    # For global declarations
    declarations_module_list = []
    declarations_list = []

    print('Creating a list of global declarations per module..')
    global_declarations_data_frame = cdl_data_frame
    for row in range(global_declarations_data_frame.shape[0]):
        declarations_module_list.append(global_declarations_data_frame.iat[row, target_module_col])
        module_signal = str(global_declarations_data_frame.iat[row, module_signal_col])
        declarations_list.append('{} {}{};'.format(
            global_declarations_data_frame.iat[row, fixed_data_type_col],
            module_signal,
            global_declarations_data_frame.iat[row, fixed_array_size_col]
            if global_declarations_data_frame.iat[row, fixed_array_size_col] != '[1]' else '')
        )
        # Input from CAN or VP
        if global_declarations_data_frame.iat[row, in_out_col] == 'IN' and \
            (global_declarations_data_frame.iat[row, source_module_col] == 'CAN' or
             global_declarations_data_frame.iat[row, source_module_col] == 'VP'):
            if global_declarations_data_frame.iat[row, source_module_col] == 'CAN':
                CAN_module = 'PreCAN'
            else:
                CAN_module = 'PreIPC'

            declarations_module_list.append(CAN_module)
            declarations_list.append('{} {}{};'.format(
                global_declarations_data_frame.iat[row, fixed_data_type_col],
                '{}_{}'.format(CAN_module, global_declarations_data_frame.iat[row, fixed_target_signal_col]),
                global_declarations_data_frame.iat[row, fixed_array_size_col]
                if global_declarations_data_frame.iat[row, fixed_array_size_col] != '[1]' else '')
            )
        # Output to CAN, DebugCAN or VP
        if global_declarations_data_frame.iat[row, in_out_col] == 'OUT' and \
            (global_declarations_data_frame.iat[row, destination_module_col] == 'CAN' or
             global_declarations_data_frame.iat[row, destination_module_col] == 'DebugCAN' or
             global_declarations_data_frame.iat[row, destination_module_col] == 'VP'):
            if global_declarations_data_frame.iat[row, destination_module_col] == 'CAN' or \
                    global_declarations_data_frame.iat[row, destination_module_col] == 'DebugCAN':
                CAN_module = 'PostCAN'
            else:
                CAN_module = 'PostIPC'

            declarations_module_list.append(CAN_module)
            declarations_list.append('{} {}{};'.format(
                global_declarations_data_frame.iat[row, fixed_data_type_col],
                '{}{}'.format(CAN_module,
                              module_signal[len(global_declarations_data_frame.iat[row, target_module_col]):]
                              ),
                global_declarations_data_frame.iat[row, fixed_array_size_col]
                if global_declarations_data_frame.iat[row, fixed_array_size_col] != '[1]' else '')
            )

    declarations_data_frame = pd.DataFrame({'TargetModule': declarations_module_list,
                                            'Declarations': declarations_list})
    declarations_data_frame.drop_duplicates(inplace=True)
    write_to_excel(declarations_data_frame, 'GlobalDeclarationsList.xlsx', 'Global Declarations')
    print('Done!')


def create_interface_database(cdl_data_frame):
    # create a database connection
    conn = create_connection("interface.db")
    if conn is not None:
        print('Updating the interface database..')
        interface_data_frame = cdl_data_frame
        # Drop tables first, if they exist
        sql_statement = '''DROP TABLE IF EXISTS error_array;'''
        execute_sql(conn, sql_statement)
        sql_statement = '''DROP TABLE IF EXISTS internal_signals;'''
        execute_sql(conn, sql_statement)
        sql_statement = ''' DROP TABLE IF EXISTS external_signals; '''
        execute_sql(conn, sql_statement)
        sql_statement = ''' DROP TABLE IF EXISTS io_pairing; '''
        execute_sql(conn, sql_statement)

        # Error array
        sql_statement = '''CREATE TABLE IF NOT EXISTS error_array (
            error_code integer NOT NULL,
            name text NOT NULL,
            description text NOT NULL
        );'''
        execute_sql(conn, sql_statement)

        # APP
        sql_statement = '''CREATE TABLE IF NOT EXISTS internal_signals (
            module text NOT NULL, 
            name text NOT NULL, 
            address integer NOT NULL, 
            link text PRIMARY KEY NOT NULL, 
            data_type text, 
            data_size integer, 
            array_size text, 
            cycle_ms integer
        );'''
        execute_sql(conn, sql_statement)

        # CAN, IPC, etc.
        sql_statement = '''CREATE TABLE IF NOT EXISTS external_signals (
                                            name TEXT NOT NULL,
                                            node TEXT NOT NULL,
                                            link TEXT PRIMARY KEY NOT NULL,
                                            id INTEGER NOT NULL,
                                            ch INTEGER NOT NULL,
                                            byte INTEGER NOT NULL,
                                            bit INTEGER NOT NULL,
                                            length INTEGER NOT NULL,
                                            factor NUMERIC,
                                            offset NUMERIC,
                                            min NUMERIC,
                                            max NUMERIC,
                                            cycle_ms INTEGER
                                        );'''
        execute_sql(conn, sql_statement)

        # Input-output pairing
        sql_statement = '''CREATE TABLE IF NOT EXISTS io_pairing (
            id integer NOT NULL PRIMARY KEY,
            source_module text NOT NULL, 
            source_signal text NOT NULL, 
            destination_module text NOT NULL, 
            destination_signal text NOT NULL,
            status text,
            result text,
            notes text
        );'''
        execute_sql(conn, sql_statement)

        # Start updating interface.db
        # For IOList.xlsx
        source_module = []
        source_signal = []
        destination_module = []
        destination_signal = []
        io_test_status = []
        io_test_result = []
        io_notes = []
        # For ExternalSignals.xlsx
        ext_name = []
        ext_node = []
        ext_link = []
        ext_id = []
        ext_ch = []
        ext_byte = []
        ext_bit = []
        ext_length = []
        ext_factor = []
        ext_offset = []
        ext_min = []
        ext_max = []
        ext_cycle_ms = []

        # interface DB -> error_array
        error_array_data_frame = pd.DataFrame({'error_code': ["0", "16", "17",
                                                              "18", "32", "33",
                                                              "34", "35", "36",
                                                              "37", "38", "39",
                                                              "40", "41", "42",
                                                              "48", "49", "50"],
                                               'name': ["ERR_CMD_SYNCH", "ERR_CMD_BUSY", "ERR_DAQ_ACTIVE",
                                                        "ERR_PGM_ACTIVE", "ERR_CMD_UNKNOWN", "ERR_CMD_SYNTAX",
                                                        "ERR_OUT_OF_RANGE", "ERR_WRITE_PROTECTED", "ERR_ACCESS_DENIED",
                                                        "ERR_ACCESS_LOCKED", "ERR_PAGE_NOT_VALID", "ERR_MODE_NOT_VALID",
                                                        "ERR_SEGMENT_NOT_VALID", "ERR_SEQUENCE", "ERR_DAQ_CONFIG",
                                                        "ERR_MEMORY_OVERFLOW", "ERR_GENERIC", "ERR_VERIFY"],
                                               'description': ["Command processor synchronization",
                                                               "Command was not executed",
                                                               "Command rejected because DAQ is running",
                                                               "Command rejected because PGM is running",
                                                               "Unknown command or not implemented optional command",
                                                               "Command syntax invalid",
                                                               "Command syntax valid but command parameter(s) "
                                                               "out of range",
                                                               "The memory location is write protected",
                                                               "The memory location is not accessible",
                                                               "Access denied Seed & Key is required",
                                                               "Selected page not available",
                                                               "Selected page mode not available",
                                                               "Selected segment not valid",
                                                               "Sequence error",
                                                               "DAQ configuration not valid",
                                                               "Memory overflow error",
                                                               "Generic error",
                                                               "The slave internal program verify routine detects "
                                                               "an error"]
                                               })
        # Append to error_array table
        print('Updating error_array table of interface database')
        error_array_data_frame.to_sql('error_array', conn, if_exists='append', index=False)
        # interface DB -> internal_signals table
        sql_internal_signal = '''INSERT INTO internal_signals (
        module, name, address, link, data_type, data_size, array_size, cycle_ms
        ) VALUES (?,?,?,?,?,?,?,?);'''
        data_size = {'boolean': 1, 'sint8': 1, 'uint8': 1, 'uint16': 2, 'uint32': 4, 'float32': 4}
        print('Updating internal_signals table of interface database')
        for row in range(interface_data_frame.shape[0]):
            # Append to internal_signals table
            internal_signal_data = (
                interface_data_frame.iat[row, target_module_col],
                interface_data_frame.iat[row, raw_target_signal_col],
                0,
                interface_data_frame.iat[row, module_signal_col],
                interface_data_frame.iat[row, fixed_data_type_col],
                data_size[interface_data_frame.iat[row, fixed_data_type_col]],
                interface_data_frame.iat[row, fixed_array_size_col],
                0
            )
            execute_sql(conn, sql_internal_signal, internal_signal_data)

            # For IOList.xlsx
            # Check if the model signal is an array/map/table but is not described in the signal's name
            if str(interface_data_frame.iat[row, raw_target_signal_col]).find('[') == -1 \
                    and interface_data_frame.iat[row, raw_array_size_col] != '':
                model_signal = interface_data_frame.iat[row, raw_target_signal_col] + \
                               interface_data_frame.iat[row, raw_array_size_col]
            else:
                model_signal = interface_data_frame.iat[row, raw_target_signal_col]
            source_module.append(interface_data_frame.iat[row, source_module_col]
                                 if interface_data_frame.iat[row, in_out_col] == 'IN'
                                 else interface_data_frame.iat[row, target_module_col])
            source_signal.append(interface_data_frame.iat[row, source_signal_col]
                                 if interface_data_frame.iat[row, in_out_col] == 'IN'
                                 else model_signal)
            destination_module.append(interface_data_frame.iat[row, target_module_col]
                                      if interface_data_frame.iat[row, in_out_col] == 'IN'
                                      else interface_data_frame.iat[row, destination_module_col])
            destination_signal.append(model_signal if interface_data_frame.iat[row, in_out_col] == 'IN'
                                      else interface_data_frame.iat[row, destination_signal_col])
            io_test_status.append('Pending')
            io_test_result.append('N/A')
            io_notes.append('')

            # For external signals
            if interface_data_frame.iat[row, in_out_col] == 'IN':
                if interface_data_frame.iat[row, source_module_col] == 'CAN' \
                        or interface_data_frame.iat[row, source_module_col] == 'VP':
                    try:
                        under_loc = str(interface_data_frame.iat[row, source_signal_col]).find('_')

                        if under_loc != -1:
                            test_id = int(interface_data_frame.iat[row, source_signal_col][under_loc - 3:under_loc], 16)
                            ext_name.append(interface_data_frame.iat[row, source_signal_col])
                            ext_node.append(interface_data_frame.iat[row, source_module_col]
                                            if interface_data_frame.iat[row, source_module_col] != 'DebugCAN' else 'DBG')
                            ext_link.append('{}_{}'.format(interface_data_frame.iat[row, source_module_col]
                                            if interface_data_frame.iat[row, source_module_col] != 'DebugCAN' else 'DBG',
                                                           interface_data_frame.iat[row, source_signal_col])
                                            )
                            ext_id.append(test_id)
                            ext_ch.append(0)
                            ext_byte.append(int(interface_data_frame.iat[row, source_signal_col][under_loc + 1:under_loc + 2]))
                            ext_bit.append(int(interface_data_frame.iat[row, source_signal_col][under_loc + 3:under_loc + 4]))
                            ext_length.append(0)
                            ext_factor.append(0)
                            ext_offset.append(0)
                            ext_min.append(0)
                            ext_max.append(0)
                            ext_cycle_ms.append(0)

                    except ValueError:
                        pass
            else:
                if interface_data_frame.iat[row, destination_module_col] == 'CAN' \
                    or interface_data_frame.iat[row, destination_module_col] == 'VP' \
                        or interface_data_frame.iat[row, destination_module_col] == 'DebugCAN':
                    try:
                        under_loc = str(interface_data_frame.iat[row, destination_signal_col]).find('_')

                        if under_loc != -1:
                            test_id = int(interface_data_frame.iat[row, destination_signal_col][under_loc - 3:under_loc], 16)
                            ext_name.append(interface_data_frame.iat[row, destination_signal_col])
                            ext_node.append(interface_data_frame.iat[row, destination_module_col]
                                            if interface_data_frame.iat[row, destination_module_col] != 'DebugCAN'
                                            else 'DBG')
                            ext_link.append('{}_{}'.format(interface_data_frame.iat[row, destination_module_col]
                                            if interface_data_frame.iat[row, destination_module_col] != 'DebugCAN' else 'DBG',
                                                           interface_data_frame.iat[row, destination_signal_col])
                                            )
                            ext_id.append(test_id)
                            ext_ch.append(0)
                            ext_byte.append(int(interface_data_frame.iat[row, destination_signal_col]
                                                [under_loc + 1:under_loc + 2]))
                            ext_bit.append(int(interface_data_frame.iat[row, destination_signal_col]
                                               [under_loc + 3:under_loc + 4]))
                            ext_length.append(0)
                            ext_factor.append(0)
                            ext_offset.append(0)
                            ext_min.append(0)
                            ext_max.append(0)
                            ext_cycle_ms.append(0)

                    except ValueError:
                        pass

        # For io_pairing table, duplicates need to be removed
        interface_data_frame = pd.DataFrame({'source_module': source_module, 'source_signal': source_signal,
                                             'destination_module': destination_module,
                                             'destination_signal': destination_signal,
                                             'status': io_test_status, 'result': io_test_result})
        interface_data_frame.drop_duplicates(inplace=True)
        # Append to io_pairing table
        print('Updating io_pairing table of interface database')
        interface_data_frame.to_sql('io_pairing', conn, if_exists='append', index=False)

        # For external signals
        print('Updating the external_signals table of interface database')
        interface_data_frame = pd.DataFrame({'name': ext_name, 'node': ext_node,
                                             'link': ext_link, 'id': ext_id,
                                             'ch': ext_ch, 'byte': ext_byte,
                                             'bit': ext_bit, 'length': ext_length,
                                             'factor': ext_factor, 'offset': ext_offset,
                                             'min': ext_min, 'max': ext_max,
                                             'cycle_ms': ext_cycle_ms}
                                            )
        interface_data_frame.sort_values(by='link', ascending=True, inplace=True)
        interface_data_frame.drop_duplicates(inplace=True)
        interface_data_frame.to_sql('external_signals', conn, if_exists='append', index=False)

        # Commit changes to database and disconnect from it
        commit_disconnect_database(conn)
        print('Done!')
    else:
        print("Error! Cannot create the database connection.")


def update_external_signals(variant, dbc_folder):
    external_signal_address_count = 0
    db_connection = create_connection("interface.db")
    if db_connection is not None:
        print('Updating external signal information')
        # Sorting link names will group VP signals from others
        sql_select = '''SELECT * FROM external_signals ORDER BY link;'''
        rows, external_signals_count = execute_sql(db_connection, sql_select, select=True, count=True)

        if variant == 'GC7' or variant == 'RE7':
            variant_index = 0
        else:
            # HR3
            variant_index = 1
        # DBC list for CAN
        #          CAN 1   CAN 2   CAN 3   CAN 4
        # GC7/RE7    *       *       *      *
        # HR3        *       *       *      *
        dbc_list = [
            ['LOCAL1', 'LOCAL2', 'SA', 'PU'],
            ['LOCAL1', 'LOCAL2', 'LOCAL', 'MAIN']
        ]

        signal_attributes = []
        for row in rows:
            signal_found = False
            can_ch = 0
            if row[1] == 'CAN' or row[1] == 'DBG':
                for dbc_name in dbc_list[variant_index]:
                    can_ch += 1
                    signal_found, signal_attributes = search_signal_in_dbc(row[0], variant,
                                                                           dbc_folder, dbc_name)
                    if signal_found:
                        break
            else:
                signal_found, signal_attributes = search_signal_in_dbc(row[0], variant,
                                                                       dbc_folder, 'IPC')
            if signal_found:
                sql_update_external_signal = '''UPDATE external_signals
                          SET node = ?, ch = ?, length = ?, factor = ?, offset = ?, min = ?, max = ?, cycle_ms = ?
                          WHERE link = ?;'''
                external_signal_data = (signal_attributes[0],
                                        can_ch,
                                        signal_attributes[1][3][
                                            signal_attributes[1][3].find('|')+1:signal_attributes[1][3].find('@')
                                        ],
                                        signal_attributes[1][4][1:signal_attributes[1][4].find(',')],
                                        signal_attributes[1][4][signal_attributes[1][4].find(',') + 1:-1],
                                        signal_attributes[1][5][1:signal_attributes[1][5].find('|')],
                                        signal_attributes[1][5][signal_attributes[1][5].find('|') + 1:-1],
                                        signal_attributes[2],
                                        row[2])
                execute_sql(db_connection, sql_update_external_signal, external_signal_data)
                external_signal_address_count += 1
            else:
                pass
        db_connection.commit()
        print('Done!')
        print('Signal information  of {} of {} external signals were updated'.format(external_signal_address_count,
                                                                                     external_signals_count))
    else:
        print("Error! Cannot create the database connection.", flush=True)

    return external_signal_address_count


def search_signal_in_dbc(signal_name, variant, dbc_folder, dbc_name):
    signal_found = False
    signal_attributes = []
    for root, dirs, files in os.walk(dbc_folder):
        if root.find(variant) != -1:
            for file in files:
                if file.endswith(".dbc") and file.find(dbc_name) != -1:
                    current_dbc_file = open(os.path.join(root, file), 'r')
                    message_header_found = False
                    node_name = ''
                    can_id = ''
                    for line in current_dbc_file:
                        # BO_ nnnn EYEnnn: n XXX
                        if line.find('BO_ ') == 0 and not signal_found:
                            # Extract the message name
                            message_name = line.split()[2][:-1]
                            # Extract the node in the signal name
                            node_in_signal_name = message_name[:-3]
                            node_name = line.split()[4]
                            if node_name == 'EYE' and node_in_signal_name != 'EYE':
                                continue
                            else:
                                can_id = line.split()[1]
                                message_header_found = True
                        if message_header_found and not signal_found:
                            if line.find(' SG_ ') == 0:
                                # Extract signal name from the list of signals under the same message
                                dbc_signal_name = line.split()[1]
                                # Look for this signal name in the external_signals table
                                if signal_name == dbc_signal_name:
                                    signal_attributes.append(node_name)
                                    signal_attributes.append(line.split())
                                    signal_found = True
                            elif line == '\n':
                                message_header_found = False
                        # Search for message cycle
                        if signal_found and line.find('BA_ \"GenMsgCycleTime\" BO_ {}'.format(can_id)) != -1:
                            signal_attributes.append(line.split()[4][:-1])
                            break
                    current_dbc_file.close()
                else:
                    continue

                if signal_found:
                    break
            if signal_found:
                break
        else:
            continue

    return signal_found, signal_attributes


def create_data_list(input_file, variant, dbc_folder):
    """ create multiple data lists for all interface, internal and external signals, I/O pairing, global declarations,
    and function calls

    :return: None
    """
    #             Sheet name , Use cols                , Skip rows
    #             [0]        , [1]                     , [2]
    input_data = ['Interface', 'C, D, F, G, K, L, M, N', 12]

    signal_name = 'signal_name'
    data_type = 'data_type'
    array_size = 'array_size'
    fixed_array_size = 'fixed_array_size'
    module_signal = 'module_signal'

    print('Creating data frame from {}'.format(input_file))
    cdl_data_frame = read_excel_file(input_file, input_data)
    print('Validating interface signal information from the input file')
    print('{} rows found'.format(len(cdl_data_frame.index)))
    # Rename column headers
    cdl_data_frame.rename(columns={'対象モデル': 'target_model_name'}, inplace=True)
    cdl_data_frame.rename(columns={'SigName(MDL)': 'model_signal_name'}, inplace=True)
    cdl_data_frame.rename(columns={'入力元': 'source_modname'}, inplace=True)
    cdl_data_frame.rename(columns={'SigName(CAN/LIN/MDL)': 'source_signame'}, inplace=True)
    cdl_data_frame.rename(columns={'型[配列サイズ]': 'raw_data_type'}, inplace=True)
    cdl_data_frame.rename(columns={'出力先': 'destination_modname'}, inplace=True)
    cdl_data_frame.rename(columns={'SigName(CAN/LIN/MDL).1': 'destination_signame'}, inplace=True)
    # Create column data_type from raw_data_type column and remove unwanted strings, arrays and values
    cdl_data_frame[data_type] = reg_replace(
        cdl_data_frame, 'raw_data_type', r'\[(.*){1,3}\]\[(.*){1,3}\]|\[(.*){1,3}\]', '')
    cdl_data_frame['raw_data_type'] = replace(cdl_data_frame, 'raw_data_type', 'single[５]', 'single[5]')
    cdl_data_frame['raw_data_type'] = replace(cdl_data_frame, 'raw_data_type', 'single [5]', 'single[5]')
    # Replace incorrect data type by 'float32'
    replace_string = {'UINT8', 'single', ' single', 'single ', 'Single'}
    for i in replace_string:
        cdl_data_frame[data_type] = replace(cdl_data_frame, data_type, i, 'float32')
    # Replace incorrect data type by 'uint8'
    replace_string = {'unit8', 'uchar8', 'int'}
    for i in replace_string:
        cdl_data_frame[data_type] = replace(cdl_data_frame, data_type, i, 'uint8')
    # Replace incorrect data type by 'sint8'
    replace_string = {'int8'}
    for i in replace_string:
        cdl_data_frame[data_type] = replace(cdl_data_frame, data_type, i, 'sint8')

    # Input_Carpara -> Input_CarPara
    cdl_data_frame['source_modname'] = replace(cdl_data_frame, 'source_modname', 'Input_Carpara', 'Input_CarPara')
    # FC_common -> FC_Common
    cdl_data_frame['source_modname'] = replace(cdl_data_frame, 'source_modname', 'FC_common', 'FC_Common')
    # INPUT_COMMON -> Input_Common
    cdl_data_frame['source_modname'] = replace(cdl_data_frame, 'source_modname', 'INPUT_COMMON', 'Input_Common')
    # INPUT_FS -> Input_FS
    cdl_data_frame['source_modname'] = replace(cdl_data_frame, 'source_modname', 'INPUT_FS', 'Input_FS')
    # f_fail_Detect_State -> f_Fail_Detect_State
    cdl_data_frame['source_signame'] = replace(cdl_data_frame, 'source_signame', 'f_fail_Detect_State',
                                               'f_Fail_Detect_State')
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'f_fail_Detect_State',
                                                  'f_Fail_Detect_State')
    # Gdel -> GDel
    cdl_data_frame['destination_signame'] = replace(cdl_data_frame, 'destination_signame', 'Gdel', 'GDel')
    # 2 destination signals in one row -> np.nan
    cdl_data_frame['destination_signame'] = replace(cdl_data_frame, 'destination_signame',
                                                    'EYE22C_4_5_REQ_FMW\nEYE221_4_5_REQ_FMW', np.nan)
    # LCT_Yaw_Rad -> LCT_Yaw_rad
    cdl_data_frame['source_signame'] = replace(cdl_data_frame, 'source_signame', 'LCT_Yaw_Rad', 'LCT_Yaw_rad')
    # VspdCan -> VSpdCan
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'VspdCan', 'VSpdCan')
    # TOLLGATEWarn -> TollgateWarn
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'TOLLGATEWarn', 'TollgateWarn')
    # Unnecessary text
    # HALTフラグ -> np.nan
    cdl_data_frame['source_signame'] = replace(cdl_data_frame, 'source_signame', 'HALTフラグ', np.nan)
    # FSモデルに出力追加の予定 -> np.nan
    cdl_data_frame['source_signame'] = replace(cdl_data_frame, 'source_signame', 'FSモデルに出力追加の予定', np.nan)
    # 車種パラに追加予定-> np.nan
    cdl_data_frame['source_signame'] = replace(cdl_data_frame, 'source_signame', '車種パラに追加予定', np.nan)
    print('Removed \'HALTフラグ\', \'FSモデルに出力追加の予定\' and \'車種パラに追加予定\' in source signal name')

    # Remove nasty spaces!!!
    cdl_data_frame['target_model_name'] = cdl_data_frame['target_model_name'].str.strip()
    cdl_data_frame['IN/OUT'] = cdl_data_frame['IN/OUT'].str.strip()
    cdl_data_frame['source_modname'] = cdl_data_frame['source_modname'].str.strip()
    cdl_data_frame['source_signame'] = cdl_data_frame['source_signame'].str.strip()
    cdl_data_frame['model_signal_name'] = cdl_data_frame['model_signal_name'].str.strip()
    cdl_data_frame['raw_data_type'] = cdl_data_frame['raw_data_type'].str.strip()
    cdl_data_frame['destination_modname'] = cdl_data_frame['destination_modname'].str.strip()
    cdl_data_frame['destination_signame'] = cdl_data_frame['destination_signame'].str.strip()
    cdl_data_frame['data_type'] = cdl_data_frame['data_type'].str.strip()

    cdl_data_frame['raw_data_type'] = cdl_data_frame['raw_data_type'].str.replace(' ', '')
    cdl_data_frame['model_signal_name'] = cdl_data_frame['model_signal_name'].str.replace(' ', '')

    # Extract just the signal name from model_signal_name and remove [] and ()
    cdl_data_frame[signal_name] = reg_replace(
        cdl_data_frame, 'model_signal_name', r'\[(.*){1,3}\]\[(.*){1,3}\]|\[(.*){1,3}\]', '')
    cdl_data_frame[signal_name] = reg_replace(
        cdl_data_frame, signal_name, r'\((.*){1,3}\)', '')
    
    # Replace (bit0), etc. with [0], etc.
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'DoorState(bit0)', 'DoorState[0]')
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'DoorState(bit1)', 'DoorState[1]')
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'DoorState(bit2)', 'DoorState[2]')
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'DoorState(bit3)', 'DoorState[3]')
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'DoorGepSheat(bit0)', 'DoorGepSheat[0]')
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'DoorGepSheat(bit1)', 'DoorGepSheat[1]')
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'DoorGepSheat(bit2)', 'DoorGepSheat[2]')
    cdl_data_frame['model_signal_name'] = replace(cdl_data_frame, 'model_signal_name', 'DoorGepSheat(bit3)', 'DoorGepSheat[3]')

    is_doorstate = cdl_data_frame['signal_name'] == 'DoorState'
    for row in cdl_data_frame[is_doorstate].index:
        cdl_data_frame.iat[row, raw_data_type_col] = '{}[4]'.format(cdl_data_frame.iat[row, raw_data_type_col])
    is_doorgepsheat = cdl_data_frame['signal_name'] == 'DoorGepSheat'
    for row in cdl_data_frame[is_doorgepsheat].index:
        cdl_data_frame.iat[row, raw_data_type_col] = '{}[4]'.format(cdl_data_frame.iat[row, raw_data_type_col])

    print('Replaced (bit0), (bit1), (bit2) and (bit3) with array index [0]. [1]. [2] and [3]')

    # Remove CONST input signals
    invalid1 = cdl_data_frame['source_modname'] == 'CONST'
    cdl_data_frame = cdl_data_frame.drop(cdl_data_frame[invalid1].index)
    print('Removed rows with CONST input. {} rows remain'.format(len(cdl_data_frame.index)))

    invalid1 = cdl_data_frame.raw_data_type.str.find('+') != -1
    invalid2 = cdl_data_frame['raw_data_type'] == '-'
    invalid3 = cdl_data_frame['raw_data_type'] == 'ー'
    invalid4 = cdl_data_frame['raw_data_type'] == '―'
    invalid5 = pd.isna(cdl_data_frame['raw_data_type'])
    invalid6 = cdl_data_frame['raw_data_type'] == '[2]'
    cdl_data_frame = cdl_data_frame.drop(
        cdl_data_frame[(invalid1 | invalid2 | invalid3 | invalid4 | invalid5 | invalid6)].index
    )
    print('Removed rows with \'+\', \'-\', \'ー\' or no data type described. {} rows remain'.format(
        len(cdl_data_frame.index)))
    # Remove invalid signals for input
    invalid1 = cdl_data_frame['IN/OUT'] == 'IN'
    invalid2 = cdl_data_frame.source_modname.str.find('+') != -1
    invalid3 = cdl_data_frame['source_modname'] == '-'
    invalid4 = cdl_data_frame['source_modname'] == 'ー'
    invalid5 = cdl_data_frame['source_modname'] == '―'
    invalid6 = pd.isna(cdl_data_frame['source_modname'])
    cdl_data_frame = cdl_data_frame.drop(
        cdl_data_frame[invalid1 & (invalid2 | invalid3 | invalid4 | invalid5 | invalid6)].index
    )
    print('Removed rows with \'+\', \'-\', \'ー\' or no source module described. {} rows remain'.format(
        len(cdl_data_frame.index)))
    invalid1 = cdl_data_frame['IN/OUT'] == 'IN'
    invalid2 = cdl_data_frame.source_signame.str.find('+') != -1
    invalid3 = cdl_data_frame['source_signame'] == '-'
    invalid4 = cdl_data_frame['source_signame'] == 'ー'
    invalid5 = cdl_data_frame['source_signame'] == '―'
    invalid6 = pd.isna(cdl_data_frame['source_signame'])
    invalid7 = cdl_data_frame.source_signame.str.find(',') != -1
    cdl_data_frame = cdl_data_frame.drop(
        cdl_data_frame[invalid1 & (invalid2 | invalid3 | invalid4 | invalid5 | invalid6 | invalid7)].index
    )
    print('Removed rows with \'+\', \'-\', \'ー\' or no source signal name described. {} rows remain'.format(
        len(cdl_data_frame.index)))

    # Remove invalid signals for output
    invalid1 = cdl_data_frame['IN/OUT'] == 'OUT'
    invalid2 = cdl_data_frame.destination_modname.str.find('+') != -1
    invalid3 = cdl_data_frame['destination_modname'] == '-'
    invalid4 = cdl_data_frame['destination_modname'] == 'ー'
    invalid5 = cdl_data_frame['destination_modname'] == '―'
    invalid6 = pd.isna(cdl_data_frame['destination_modname'])
    invalid7 = cdl_data_frame.destination_modname.str.find(',') != -1
    cdl_data_frame = cdl_data_frame.drop(
        cdl_data_frame[invalid1 & (invalid2 | invalid3 | invalid4 | invalid5 | invalid6 | invalid7)].index
    )
    print('Removed rows with \'+\', \'-\', \'ー\' or no destination module described. {} rows remain'.format(
        len(cdl_data_frame.index)))
    invalid1 = cdl_data_frame['IN/OUT'] == 'OUT'
    invalid2 = cdl_data_frame.destination_signame.str.find('+') != -1
    invalid3 = cdl_data_frame['destination_signame'] == '-'
    invalid4 = cdl_data_frame['destination_signame'] == 'ー'
    invalid5 = cdl_data_frame['destination_signame'] == '―'
    invalid6 = pd.isna(cdl_data_frame['destination_signame'])
    invalid7 = cdl_data_frame.destination_signame.str.find(',') != -1
    cdl_data_frame = cdl_data_frame.drop(
        cdl_data_frame[invalid1 & (invalid2 | invalid3 | invalid4 | invalid5 | invalid6 | invalid7)].index
    )
    print(
        'Removed rows with \'+\', \'-\', \'ー\' or no destination signal name described. {} rows remain'.format(
            len(cdl_data_frame.index))
    )

    # Extract array size from raw_data_type
    cdl_data_frame[array_size] = reg_replace(
        cdl_data_frame, 'raw_data_type', r'^\w*\d{0,2}[^\[]|(\[\D+\]|\[\D+\]\[\D+\])', '')

    # Create global signal name for declarations in stubs
    cdl_data_frame[module_signal] = cdl_data_frame['target_model_name'] + '_' + cdl_data_frame[signal_name]

    # Fix the array size of the signals
    array_size_list = {}
    temp_inout_o = ''
    temp_module_o = ''
    temp_module_signal_o = ''
    temp_array_size_o = ''
    signal_count = 0
    signal_count_o = 0
    acquired = False
    first_pass = True
    cdl_data_frame.sort_values(['target_model_name', 'IN/OUT', module_signal], inplace=True)
    for row in range(cdl_data_frame.shape[0]):
        temp_inout = cdl_data_frame.iat[row, in_out_col]
        if temp_inout == 'IN':
            temp_module = cdl_data_frame.iat[row, source_module_col]
        else:
            temp_module = cdl_data_frame.iat[row, destination_module_col]
        temp_module_signal = cdl_data_frame.iat[row, module_signal_col]
        temp_array_size = cdl_data_frame.iat[row, raw_array_size_col]
        if not first_pass:
            # Input, from same source, to same signal
            if temp_inout == temp_inout_o and temp_module == temp_module_o and \
                    temp_module_signal == temp_module_signal_o:
                # Map/table
                if temp_array_size.find('][') != -1:
                    if not acquired:
                        array_size_list[temp_module_signal] = temp_array_size
                        acquired = True
                    else:
                        pass
                else:
                    if temp_array_size != '':
                        signal_count += 1
                    else:
                        pass
            else:
                if temp_module_signal_o not in array_size_list \
                        or (array_size_list[temp_module_signal_o].find('][') == -1
                            and signal_count_o + 1 > int(array_size_list[temp_module_signal_o][1:-1])):
                    array_size_list[temp_module_signal_o] = '[{}]'.format(signal_count_o + 1) \
                        if temp_array_size_o == '' or int(temp_array_size_o[1:2]) < signal_count_o + 1 \
                        else temp_array_size_o
                else:
                    pass
                signal_count = 0
                acquired = False
        else:
            first_pass = False
        temp_inout_o = temp_inout
        temp_module_o = temp_module
        temp_module_signal_o = temp_module_signal
        temp_array_size_o = temp_array_size
        signal_count_o = signal_count
    # For the last entry in array_size_list
    if temp_module_signal_o not in array_size_list \
            or (array_size_list[temp_module_signal_o].find('][') == -1
                and signal_count_o + 1 > int(array_size_list[temp_module_signal_o][1:-1])):
        array_size_list[temp_module_signal_o] = '[{}]'.format(signal_count_o + 1) \
            if temp_array_size_o == '' or int(temp_array_size_o[1:2]) < signal_count_o + 1 \
            else temp_array_size_o

    # Update the array size of each module signal
    cdl_data_frame[fixed_array_size] = cdl_data_frame[array_size]
    for row in range(cdl_data_frame.shape[0]):
        cdl_data_frame.iat[row, fixed_array_size_col] = array_size_list[cdl_data_frame.iat[row, module_signal_col]]
    # Save the updated interface list to an Excel file
    print('Generating output an Excel file for the interface signal information. Please wait..')
    write_to_excel(cdl_data_frame, 'InterfaceList.xlsx', 'IF Information')
    print('Done!')

    create_interface_database(cdl_data_frame)
    # Check if CAN signal information have been updated in the database
    if update_external_signals(variant, dbc_folder) == 0:
        # CAN channel information is necessary for CANG4, LOCALCAN and IPC classification
        print('External signals information were not updated! Aborting test..', flush=True)
        sys.exit()
    create_function_calls(cdl_data_frame)
    create_global_declarations(cdl_data_frame)
    print('Done preparing interface I/O data for testing')


if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required. Please check your Python version.\n" % MIN_PYTHON)

debug = False
parser = argparse.ArgumentParser()
if debug:
    parser.add_argument('-i', dest='input_file', default='【SASB連-2018-21】外部IF定義書_20181228リリース.xlsx')
    parser.add_argument('-v', dest='variant', help='set to GC7, for debugging', default='GC7')
else:
    parser.add_argument('input_file', help='IF specification file')
    parser.add_argument("variant", help='variant to be tested', choices=['GC7', 'HR3'])
parser.add_argument('-d', dest="dbc_folder", help='path of the DBC folders for each variant, default is DBC/',
                    default='DBC/')
args = parser.parse_args()

if not os.path.exists(args.input_file):
    print('{} not found!'.format(args.input_file), flush=True)
elif not os.path.exists(args.dbc_folder):
    print('DBC folder not found!', flush=True)
else:
    create_data_list(args.input_file, args.variant, args.dbc_folder)
