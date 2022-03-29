# -*- coding: utf-8 -*-
import logging
import logging.handlers
from configparser import ConfigParser
import os
from datetime import date

config = ConfigParser()
config.read('Base_setting.cfg')

start_date = date.today().strftime("%Y%m%d")
base_path = config['PATH']['Base_Path']

if os.path.basename(os.getcwd()) != base_path:
    pass
else:
    base_path = os.getcwd()
log_path = os.path.join(base_path,config['PATH']['Log_Path'])
if not os.path.exists(log_path):
    os.mkdir(log_path)

logger = logging.getLogger('kiwoom_agent')
formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s]%(asctime)s>%(message)s')
loggerLevel = logging.DEBUG
filename = os.path.join(log_path,start_date+'.txt')

filehandler = logging.FileHandler(filename)
streamhandler = logging.StreamHandler()

filehandler.setFormatter(formatter)
streamhandler.setFormatter(formatter)

logger.addHandler(filehandler)
logger.addHandler(streamhandler)
logger.setLevel(loggerLevel)
