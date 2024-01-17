import datetime
import pandas as pd
from pathlib import Path
import yaml
from numpy import datetime64 as numpy_datetime64

class NSCRequest(object):
    """
    NSC data request class.
    """

    fice: str = '',
    branch: str = ''
    name: str = ''
    inquiryType: str = ''
    search: datetime.date = None
    enrolledStudents: bool = False
    outputPath: str = '.'
    filename: str = ''

    _current_day__ = None
    _current_month__ = None
    _current_year__ = None

    def __init__(self, 
                 outputPath: str = '',
                 filename: str = '',
                 inquiryType: str = '', 
                 search: str = '', 
                 enrolledStudents: bool = None, 
                 config: dict = None,
                 config_file: str = ''):
        '''
        The constructor for NSCRequest class.

        Returns: 0 for success or error value

        Parameters:
            df (pandas.DataFrame):  Default=None. The data to output to an NSC 
                                    request file.
            inquiryType (str):      Default=None. The type of inquiry to create 
                                    (can be one of SE or PA). This is the same
                                    as the inquiryType property.
            search (str):           Default=Today's date. The default search 
                                    date to use if it is not included in the 
                                    dataframe. This is specified as a string 
                                    and can be just the year (YYYY), year 
                                    and month (YYYYMM), or the full date as
                                    year, month, day (YYYYMMDD). If the day
                                    or month are not specified, "01" is used.
                                    This is the same as the search property.
            enrolledStudents (bool):Default=False for SE and True for PA 
                                    requests. Signify that SSN is included for 
                                    a PA request. Not valid for SE requests.
                                    This is the same as the enrolledStudents
                                    property.
            outputPath (str):       Default=Current directory. The path for 
                                    the resulting output file. This is the same
                                    as the outputPath property. It can also be
                                    specified on the createFile method.
            filename (str):         Default=<school's fice code>_<inquiryType>_<search>.txt.
                                    The name of the resulting file. This is 
                                    the same as the filename property. It can 
                                    also be specified on the createFile method.
            config (dict):          A dictionary containing (at least) the 
                                    following:

                                    {
                                        "school" : {
                                            "fice" : "<school's fice code>",
                                            "branch" : "<school's branch code>",
                                            "name" : "<school's full name>"
                                        }
                                    }

                                    Can also include any of the parameters.
                                    The following is an example with all 
                                    parameters specified:

                                    {
                                        "school" : {
                                            "fice" : "999999",
                                            "branch" : "00",
                                            "name" : "My Local School"
                                        },
                                        "nscrequest" : {
                                            "inquiryType" : "PA",
                                            "search" : date(today),
                                            "enrolledStudents" : False,
                                            "outputPath" : "."
                                        }
                                    }

            config_file (str):      A filename, including path, to a YAML formatted file. If
                                    config and config_file are both specified, config will be used.
        '''
        _current_date = datetime.date.today()

        self._current_day__ = _current_date.day
        self._current_month__ = _current_date.month
        self._current_year__ = _current_date.year

        if config:
            self._config = config.copy()
        else:
            if config_file:
                with open(config_file,"r") as ymlfile:
                    cfg_l = yaml.load(ymlfile, Loader=yaml.FullLoader)

                    if ("config" not in cfg_l or ("config" in cfg_l and "location" not in cfg_l["config"])) or cfg_l["config"]["location"] == "self":
                        self._config = cfg_l.copy()
                    else:
                        with open(cfg_l["config"]["location"] + "config.yml","r") as ymlfile2:
                            self._config = yaml.load(ymlfile2, Loader=yaml.FullLoader)
            else:
                print("ERROR: No config or config_file was provided")
                return

        if config or config_file:
            self.fice = self._config['school']['fice']
            self.branch = self._config['school']['branch']
            self.name = self._config['school']['name']

        self.inquiryType = 'PA' if inquiryType=='' else inquiryType
        self.enrolledStudents = enrolledStudents

        if search=='':
            self.search = datetime.datetime.now().strftime('%Y%m%d')
        else:
            if len(search) == 4: # if YYYY
                self.search = f'{search}0101'
                print(f'Added month and day to search: {self.search}')
            elif len(search) == 6: # if YYYYMM
                self.search = f'{search}01'
                print(f'Added day to search: {self.search}')
            elif len(search) == 7 and search.contains('-'): # if YYYY-MM
                self.search = f'{search[:4]}{search[5:6]}01'
                print(f"Removed '-' and day to search: {self.search}")
            elif len(search) == 10 and search.contains('-'): # if YYYY-MM-DD
                self.search = search.replace('-','')
            else:
                self.search = search

        if outputPath != "":
            self.outputPath = Path(outputPath)
            if not self.outputPath.exists():
                print(f"WARNING - Path does not exist [{outputPath}]")
        else:
            self.outputPath = Path('.')
            print(f'WARNING: Path set to {self.outputPath}')

        if filename=="":
            self.filename = f"{self.fice}-{self.branch}_{self.inquiryType}_{self.search}.csv"
            if (self.outputPath / self.filename).exists():
                print(f"WARNING: File [{self.outputPath / self.filename}] will be overwritten")
        else:
            self.filename = filename

        return

    def create_request(self, df: pd.DataFrame = pd.DataFrame()) -> int:
        if df.empty:
            # print("ERROR: Dataframe is empty")
            raise ValueError("Dataframe is empty")

        if any([item not in df.columns for item in ["FirstName","MiddleInitial","LastName","Suffix","DOB"]]):
            # identify this column is missing from the list
            missing = [item for item in ["FirstName","MiddleInitial","LastName","Suffix","DOB"] if item not in df.columns]
            # print(f"ERROR: Missing one of the required columns: {missing}")
            raise ValueError(f"ERROR: Missing one of the required columns: {missing}")

        if ('SSN' in df.columns) and (self.inquiryType != "PA" or (self.inquiryType == "PA" and self.enrolledStudents == True)):
            print(f"WARNING: SSN provided but ignored - inquiry({self.inquiryType}), enrolled({self.enrolledStudents})")

        # nscFile <- file.path(path,fn)

        r = pd.DataFrame(index=df.index)
        # r.reset_index(inplace=True)

        if self.inquiryType == 'PA' and self.enrolledStudents == False and 'SSN' in df.columns:
            r.loc[:,'SSN'] = df.loc[:,'SSN']
        else:
            r.loc[:,'SSN'] = ""

        r.loc[:,"FirstName"] = df.loc[:,"FirstName"].str[:20].str.strip().str.encode('ascii','ignore').str.decode('ascii')

        if "MiddleInitial" in df.columns:
            r.loc[:,"MiddleInitial"] = df.loc[:,"MiddleInitial"].str[:1].str.strip().str.encode('ascii','ignore').str.decode('ascii')
        else:
            r.loc[:,"MiddleInitial"] = ""

        r.loc[:,"LastName"] = df.loc[:,"LastName"].str[:20].str.strip().str.encode('ascii','ignore').str.decode('ascii')

        if "Suffix" in df.columns:
            r.loc[:,"Suffix"] = df.loc[:,"Suffix"].str[:5].str.strip().str.encode('ascii','ignore').str.decode('ascii')
        else:
            r.loc[:,"Suffix"] = ""

        # Ensure DOB is a date formatted as YYYYMMDD
        def cvtdate(x):
            try:
                return(x.strftime('%Y%m%d'))
            except:
                return(np.nan)

        if isinstance(df["DOB"].values[0], datetime.date) or isinstance(df["DOB"].values[0], datetime.datetime) or isinstance(df["DOB"].values[0], numpy_datetime64):
            r.loc[:,"DOB"] = df.loc[:,"DOB"].apply(cvtdate)
        else:
            try:
                _ = pd.to_datetime(df["DOB"], format="%Y%m%d")
            except:
                # print("ERROR: DOB does not contain dates as strings in the format YYYYMMDD")
                raise ValueError("ERROR: DOB does not contain dates as strings in the format YYYYMMDD")

            r.loc[:,"DOB"] = df.loc[:,"DOB"]

        # # Check if the following optional fields are provided:
        # #     SearchBeginDate, ReturnRequestField
        if "ReturnRequestField" not in df.columns:
            print("WARNING - ReturnRequestField not provided - you may have difficulty matching return records")

        if "SearchBeginDate" not in df.columns:
            print(f"WARNING - SearchBeginDate not provided - defaulting to {self.search}")
            r.loc[:,"SearchBeginDate"] = self.search
        else:
            if isinstance(df["SearchBeginDate"].values[0], datetime.date) or isinstance(df["SearchBeginDate"].values[0], datetime.datetime) or isinstance(df["SearchBeginDate"].values[0], numpy_datetime64):
                r.loc[:,"SearchBeginDate"] = df.loc[:,"SearchBeginDate"].apply(cvtdate)
            else:
                r.loc[:,"SearchBeginDate"] = df.loc[:,"SearchBeginDate"]

        r.loc[:,"RecordType"] = "D1"
        r.loc[:,"Blank"] = ""

        r.loc[:,"SchoolCode"] = self.fice
        r.loc[:,"BranchCode"] = self.branch

        if "ReturnRequestField" in df.columns:
            r.loc[:,"ReturnRequestField"] = df.loc[:,"ReturnRequestField"].str[:50].str.strip()
        else:
            r.loc[:,"ReturnRequestField"] = ""

        self.r = r.loc[r.loc[:,"FirstName"].notna(),["RecordType","SSN","FirstName","MiddleInitial","LastName","Suffix","DOB","SearchBeginDate","Blank","SchoolCode","BranchCode","ReturnRequestField"]]
        self.h = f"H1\t{self.fice}\t{self.branch}\t{self.name[:40].strip()}\t{datetime.datetime.now().strftime('%Y%m%d')}\t{self.inquiryType}\tI\n"
        self.t = f"T1\t{r.shape[0]+2}\n"

        return(self)

    def to_file(self,
                outputPath: str = "",
                filename: str = "") -> None:

        loc_op = Path(self.outputPath if outputPath=='' else outputPath)
        loc_fn = Path(self.filename if filename=='' else filename)

        with open(loc_op / loc_fn, 'w') as tsvfile:
            tsvfile.write(self.h)
        self.r.to_csv(loc_op / loc_fn, sep='\t', na_rep='', header=False, index=False, mode='a')
        with open(loc_op / loc_fn, 'a') as tsvfile:
            tsvfile.write(self.t)

# For testing purposes only
if __name__ == "__main__":
    testsource: str = "ccdw"

    nsc_config = {
                    "school" : {
                        "fice" : "999999",
                        "branch" : "00",
                        "name" : "MySchool"
                    }
                 }
                 
    nscr = NSCRequest( outputPath="",
                       filename="",
                       inquiryType="SE",
                       #search="",
                       enrolledStudents=True,
                       config=nsc_config
                       )

    nsc2 = NSCRequest( inquiryType="SE",
                       #search="",
                       enrolledStudents=True,
                       config_file="studentclearinghouse\\config.yml"
                       )

    testdf = pd.DataFrame({'FirstName':['FN1','FN2','FN3 This is really long and should be truncated'],
                           'MiddleInitial':['M','M','M'],
                           'LastName':['LN1','LN2 This is really long and should be truncated','LN3, Jr'],
                           'Suffix':['','Jr.',''],
                           'DOB':['20000101','20000202','20000303'],
                           'ReturnRequestField':['ID1.2020FA','ID2.2020FA','ID3.2020SP'],
                           'SearchBeginDate':[datetime.date(2020,8,15),datetime.date(2020,8,15),datetime.date(2020,1,10)]
                           })
    testdf['DOB'] = pd.to_datetime(testdf['DOB'], format="%Y%m%d")
    testdf.loc[testdf.loc[:,"LastName"].str.contains(', Jr'),"Suffix"] = 'Jr'
    testdf.loc[:,"LastName"] = testdf.loc[:,"LastName"].str.replace('.*, Jr','',regex=True)


    nscr.create_request(testdf)
    # nscr.to_file()

    nscr.create_request(testdf.drop(columns=['ReturnRequestField']))
    nscr.create_request(testdf.drop(columns=['FirstName']))

    nsc2.create_request(testdf)
    nsc2.to_file()

