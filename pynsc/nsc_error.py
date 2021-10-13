from __future__ import annotations

#import collections.abc
from datetime import date
#import glob
#import os
import pandas as pd
#from pathlib import Path
import re
#import sqlalchemy
#import urllib
import yaml
from typing import Union

__version__ = "0.0.1"

class NSCError(Exception):
    pass

class NSCConfigurationError(Exception):
    pass


# For testing purposes only
if __name__ == "__main__":
    testsource: str = "ccdw"


