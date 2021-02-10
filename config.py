# Copyright (c) 2021 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php

import os
import sys

from configparser import ConfigParser

def read_config():
    CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".moneysocket-custodial")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "moneysocket-custodial.conf")
    if not os.path.exists(CONFIG_FILE):
        sys.exit("*** could not find %s" % CONFIG_FILE)
    config = ConfigParser()
    config.read(CONFIG_FILE)
    return config
