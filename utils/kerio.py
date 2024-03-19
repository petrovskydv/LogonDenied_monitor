import logging

import requests
import urllib3

urllib3.disable_warnings()


class Kerio:
    def __init__(self, server, username, password):
        self.server = server
        self.username = username
        self.password = password
        self.token = None
        self.session = None

    def _call_method(self, method, params):
        data = {"method": method, "id": 1, "jsonrpc": "2.0"}
        if params:
            data['params'] = params

        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers = {'X-Token': self.token}
        response = self.session.post(url=f'{self.server}/admin/api/jsonrpc/', headers=headers, json=data, verify=False)
        response.raise_for_status()
        return response.json()

    def login(self):
        self.session = requests.Session()
        params = {
            "userName": self.username, "password": self.password,
            "application": {"vendor": "", "name": "LogonDenied monitor", "version": "1.1.0"}
        }
        response = self._call_method("Session.login", params)
        self.token = response["result"]["token"]

    def close(self):
        self._call_method("Session.logout", {})

    def save_addresses(self, addresses):
        params = {'groups': addresses}
        self._call_method("IpAddressGroups.create", params)
        params = {
            'commandList': [
                {'method': "IpAddressGroups.apply"},
                {'method': "Session.getConfigTimestamp"}
            ]
        }
        response = self._call_method("Batch.run", params)
        clientTimestampList = response['result'][1]['result']
        self._call_method("Session.confirmConfig", clientTimestampList)


def format_host_for_kerio(group_id, group_name, host, description):
    template = {
        'groupId': group_id,
        'groupName': group_name,
        'host': host,
        'type': "Host",
        'description': description,
        'enabled': True
    }
    return template
