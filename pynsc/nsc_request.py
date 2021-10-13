from __future__ import annotations

#import collections.abc
import datetime
from itertools import groupby 
#import glob
#import os
import pandas as pd
from pathlib import Path
import re
#import urllib
import yaml
from typing import Union

#__version__ = "0.0.1"

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

    __current_day__ = None
    __current_month__ = None
    __current_year__ = None

    def __init__(self, 
                 outputPath: str = '',
                 filename: str = '',
                 inquiryType: str = '', 
                 search: str = '', 
                 enrolledStudents: bool = None, 
                 config: dict = None) -> int:
        '''
        The constructor for NSCRequest class.

        Returns: 0 for success or error value

        Parameters:
            df (pandas.Dataframe):  Default=None. The data to output to an NSC 
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

                                    This can come from a YAML formatted file 
                                    named config.yml in the current directory.
        '''
        __current_date__ = datetime.date.today()

        self.__current_day__ = __current_date__.day
        self.__current_month__ = __current_date__.month
        self.__current_year__ = __current_date__.year

        if config:
            self.__config__ = config.copy()
        else:
            with open("config.yml","r") as ymlfile:
                cfg_l = yaml.load(ymlfile, Loader=yaml.FullLoader)

                if cfg_l["config"]["location"] == "self":
                    self.__config__ = cfg_l.copy()
                else:
                    with open(cfg_l["config"]["location"] + "config.yml","r") as ymlfile2:
                        self.__config__ = yaml.load(ymlfile2, Loader=yaml.FullLoader)

        self.fice = self.__config__['school']['fice']
        self.branch = self.__config__['school']['branch']
        self.name = self.__config__['school']['name']

        self.inquiryType = 'PA' if inquiryType=='' else inquiryType
        self.enrolledStudents = enrolledStudents

        if search=='':
            self.search = datetime.datetime.now().strftime('%Y%m%d')
        else:
            # TODO Need to add logic to determine if YYYY, YYYYMM, or YYYYMMDD were provided
            self.search = search

        if outputPath != "":
            self.outputPath = Path(outputPath)
            if ~self.outputPath.exists():
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

    def create_request( self, df: pd.Dataframe = pd.DataFrame()):
        if df.empty:
            print("ERROR")
            return(-1)

        if any([item not in df.columns for item in ["FirstName","MiddleInitial","LastName","Suffix","DOB"]]):
            print("ERROR")
            return(-11)

        if ('SSN' in df.columns) and (self.inquiryType != "PA" or (self.inquiryType == "PA" and self.enrolledStudents == True)):
            print(f"WARNING: SSN provided but ignored - inquiry({self.inquiryType}), enrolled({self.enrolledStudents})")

        # # If search is just YYYY, set to YYYY0101, if just YYYYMM, set to YYYYMM01.
        # if (nchar(search) == 4) {
        #     search %<>% paste0("0101")
        #     warning(paste("search changed to", search))
        # } else if (nchar(search) == 6) {
        #     search %<>% paste0("01")
        #     warning(paste("search changed to", search))
        # } else if (nchar(search) == 7) {
        #     search <- str_c( substr(search, 1, 4),
        #                     substr(search, 6, 7),
        #                     paste0("01") )
        #     warning(paste("search changed to", search))
        # }

        # nscFile <- file.path(path,fn)

        # # Ensure DOB is a date formatted as YYYYMMDD

        r = pd.DataFrame(index=df.index)
        r.reset_index(inplace=True)

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

        # Need to look at the first row's value to see if this column contains dates or strings
        if type(df.DOB[0]) == datetime.date:
            r.loc[:,"DOB"] = df.loc[:,"DOB"].apply(lambda x: x.strftime("%Y%m%d"))
        else:
            r.loc[:,"DOB"] = df.loc[:,"DOB"]

        # # Check if the following optional fields are provided:
        # #     SearchBeginDate, ReturnRequestField
        if "ReturnRequestField" not in df.columns:
            print("WARNING - ReturnRequestField not provided - you may have difficulty matching return records")

        if "SearchBeginDate" not in df.columns:
            print(f"WARNING - SearchBeginDate not provided - defaulting to {self.search}")
            r.loc[:,"SearchBeginDate"] = self.search
        else:
            if type(df.loc[:,"SearchBeginDate"][0]) == datetime.date:
                r.loc[:,"SearchBeginDate"] = df.loc[:,"SearchBeginDate"].apply(lambda x: x.strftime("%Y%m%d"))
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
        self.t = f"T1\t{r.shape[0]}\n"

    def to_file(self,
                outputPath: str = "",
                filename: str = ""):

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

    testdf = pd.DataFrame({'FirstName':['FN1','FN2','FN3 This is really long and should be truncated'],
                           'MiddleInitial':['M','M','M'],
                           'LastName':['LN1','LN2 This is really long and should be truncated','LN3, Jr'],
                           'Suffix':['','Jr.',''],
                           'DOB':['20000101','20000202','20000303'],
                           'ReturnRequestField':['ID1.2020FA','ID2.2020FA','ID3.2020SP'],
                           'SearchBeginDate':[datetime.date(2020,8,15),datetime.date(2020,8,15),datetime.date(2020,1,10)]
                           })
    testdf.loc[testdf.loc[:,"LastName"].str.contains(', Jr'),"Suffix"] = 'Jr'
    testdf.loc[:,"LastName"] = testdf.loc[:,"LastName"].str.replace('.*, Jr','',regex=True)


    nscr.create_request(testdf)
    nscr.to_file()
