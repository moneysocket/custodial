# Copyright (c) 2021 Jarret Dyrbye
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php

import requests
import json


class TerminusRpc():
    def __init__(self, config):
        self.host = config['Terminus']['RpcHost']
        self.port = int(config['Terminus']['RpcPort'])
        self.url = "http://%s:%d" % (self.host, self.port)

    def call(self, args):
        cmd = args[0]
        cmd_args = args[1:]
        payload = {
            "method": cmd,
            "params": cmd_args,
            "jsonrpc": "2.0",
            "id": 0,
        }
        response = requests.post(self.url, json=payload).json()
        j = response['result']
        try:
            return json.loads(j)
        except:
            return None
