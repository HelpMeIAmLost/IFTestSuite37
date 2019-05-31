IFTestSuite ReadMe
This package contains:
  IFTestSuite37
    |- Build
    |- DBC
      |- GC7_RE7
        IPC.dbc
        LOCAL1_CAN.dbc
        LOCAL2_CAN.dbc
        PU_bus.dbc
        SA_bus.dbc
      |- HR3
        IPC.dbc
        LOCAL_CAN.dbc
        LOCAL1_CAN.dbc
        LOCAL2_CAN.dbc
        MAIN_CAN.dbc
    |- Stubs
    common_util.py
    InterfaceTestMT.py
    PostFlashPreTestCheck.py
    PrepareData.py
    readme.txt
    requirements.txt
    UpdateStubs.py

Requirements
---
  * Python 3.7
  * Python libraries in requirements.txt
  * Interface specification file in Excel
  * DBC files and folders in the following structure:
    DBC
      |- GC7_RE7
        IPC.dbc
        LOCAL1_CAN.dbc
        LOCAL2_CAN.dbc
        PU_bus.dbc
        SA_bus.dbc
      |- HR3
        IPC.dbc
        LOCAL_CAN.dbc
        LOCAL1_CAN.dbc
        LOCAL2_CAN.dbc
        MAIN_CAN.dbc
  * Stub files and folder in the following structure:
    Stubs
      ACC_10ms.c
      ACC_50ms.c
      :
      VPTempCtrl.c
  * Map file and folder in the following structure:
    Build
      application.map

Procedure
---
1. Update the stubs and create the database
  a. PrepareData.py - extracts and validates interface signals from the interface specification, create a list of global declarations, RTE function calls and update the interface database for testing
    Syntax:
      py PrepareData.py <interface specification> <variant> [-d <DBC folder path>]

    Arguments:
      interface specification : required, interface specification file from Subaru
      variant                 : required, variant to test
      -d                      : optional, path of the DBC file and folder structure as described in the Requirements section, default is 'DBC/'

    Examples:
      py PrepareData.py 【SASB連-2018-21】外部IF定義書_20181228リリース.xlsx GC7
      py PrepareData.py 【SASB連-2018-21】外部IF定義書_20181228リリース.xlsx HR3 -d DBCs_are_here/

    Output:
      GlobalDeclarationsList.xlsx - a list of global variable declarations that will be used for testing
      interface.db - a database for interface test items and input and output signal information
      InterfaceList.xlsx - a validated list of input/output interface signals
      RTEFunctionCalls.xlsx - a list of function calls to RTE APIs and data conversion lines, if necessary

  b. UpdateStubs.py - updates the stubs by inserting the global declarations and RTE function calls in their respective modules
    Syntax:
      py UpdateStubs.py [-s <stub folder path>]

    Arguments:
      -s : optional, path of the stub files relative to the script folder, default is 'Stubs/'

    Examples:
      py UpdateStubs.py
      py UpdateStubs.py -s stubs_are_here/

    Output:
      The updated stub files inside the Stubs/ folder. Note that not all stub files will be updated, only those that have interface input/output signals.

2. Copy the updated stubs to the SVS350 application folder

3. Build the application software with the same variant used with PrepareData.py

4. After a successful build, copy the application.map file to the Build/ folder of the IFTestSuite

5. Perform post-flash and pre-test checks
  Syntax:
    py PostFlashPreTestCheck.py <variant> [-m <map folder path>] [-d <DBC folder path>]

  Arguments:
    variant : required, variant to test
    -m      : optional, path of the application.map file relative to the script folder, default is 'Build/'
    -d      : optional, path of the DBC file and folder structure as described in the Requirements section, default is 'DBC/'

  Examples:
    py PostFlashPreTestCheck.py GC7
    py PostFlashPreTestCheck.py GC7 -m map_is_here/
    py PostFlashPreTestCheck.py GC7 -d DBCs_are_here/
    py PostFlashPreTestCheck.py GC7 -m map_is_here/ -d DBCs_are_here/

  Output:
    SVS350_<variant>_CANTx_Checklist.xlsx - a list of CAN messages transmitted by SVS350 through each CAN channel, including information if they were transmitted or not during testing

5. Perform interface tests using the same variant used with PrepareData.py
  Syntax:
    py InterfaceTestMT.py <variant> [-r <number of retries>] [-u no] [-m <map folder path>] [-d <DBC folder path>]

  Arguments:
    variant : required, variant to test
    -r      : optional, number of retries to perform for failed test items, default is 0
    -u no   : optional, do not update the addresses of application signals, default is '-u yes'
    -m      : optional, path of the application.map file relative to the script folder, default is 'Build/'
    -d      : optional, path of the DBC file and folder structure as described in the Requirements section, default is 'DBC/'

  Examples:
    py InterfaceTestMT.py GC7
    py InterfaceTestMT.py GC7 -r 1 -u no
    py InterfaceTestMT.py GC7 -m map_is_here/ -d DBCs_are_here/
    py InterfaceTestMT.py GC7 -r 2 -m map_is_here/

  Output:
    CAN1.asc, CAN2.asc, CAN3.asc and CAN4.asc - CAN stream logged during testing
    XCP.asc - XCP stream logged during testing
    output_<module name>.txt - a log of the test results per module
    run.log - script execution log file