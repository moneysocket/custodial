#!/usr/bin/env python3
# Copyright (c) 2021 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php

from sqlalchemy import create_engine
from config import read_config

config = read_config()
uri = "sqlite:////" + config['Db']['DatabaseFile']
engine = create_engine(uri, echo=True)
con = engine.raw_connection()
for line in con.iterdump():
    print(line)

