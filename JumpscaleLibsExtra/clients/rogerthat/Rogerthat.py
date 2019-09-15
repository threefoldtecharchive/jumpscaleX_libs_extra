from Jumpscale import j

import urllib.request
import urllib.error
import urllib.parse

JSConfigClient = j.baseclasses.object_config


class Rogerthat(JSConfigClient):
    _SCHEMATEXT = """
    @url = jumpscale.rogerthat.client
    name** = "" (S)
    api_key_ = "" (S)
    """

    STATUS_RECEIVED = 1
    STATUS_ACKED = 2

    FLAG_ALLOW_DISMISS = 1
    FLAG_SHARED_MEMBERS = 16
    FLAG_AUTO_SEAL = 64

    ALERT_FLAG_SILENT = 1
    ALERT_FLAG_VIBRATE = 2
    ALERT_FLAG_RING_5 = 4
    ALERT_FLAG_RING_15 = 8
    ALERT_FLAG_RING_30 = 16
    ALERT_FLAG_RING_60 = 32
    ALERT_FLAG_INTERVAL_5 = 64
    ALERT_FLAG_INTERVAL_15 = 128
    ALERT_FLAG_INTERVAL_30 = 256
    ALERT_FLAG_INTERVAL_60 = 512
    ALERT_FLAG_INTERVAL_300 = 1024
    ALERT_FLAG_INTERVAL_900 = 2048
    ALERT_FLAG_INTERVAL_3600 = 4096

    FLAG_WAIT_FOR_NEXT_MESSAGE = 1

    def _init(self, **kwargs):
        self._api_key = self.api_key_
        self._url = "https://rogerth.at/api/1"

    def _raw_request(self, method, params):
        data = {"id": j.data.idgenerator.generateGUID(), "method": method, "params": params}
        json_data = j.data.serializers.json.dumps(data)
        headers = {"Content-Type": "application/json-rpc; charset=utf-8", "X-Nuntiuz-API-key": self._api_key}
        request = urllib.request.Request(self._url, json_data, headers)
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            result = j.data.serializers.json.loads(response.read())
            return result
        else:
            self._log_error("Server error when executing send_message")
            return False

    def checkFlag(self, flags, flag):
        return flags & flag == flag

    def send_message(
        self,
        message,
        members=None,
        flags=0,
        parent_message_key=None,
        answers=None,
        dismiss_button_ui_flags=0,
        alert_flags=0,
        branding=None,
        tag=None,
        context=None,
        ui_flags=None,
    ):
        members = members or list()
        answers = answers or list()
        params = {"message": message, "members": members, "flags": flags}
        params["parent_message_key"] = parent_message_key
        params["answers"] = answers or []
        params["dismiss_button_ui_flags"] = dismiss_button_ui_flags
        params["alert_flags"] = alert_flags
        params["branding"] = branding
        params["tag"] = tag
        params["context"] = context
        if ui_flags is not None:
            params["ui_flags"] = ui_flags
        return self._raw_request("messaging.send", params)

    def send_broadcast(
        self,
        broadcast_type,
        message,
        flags=0,
        parent_message_key=None,
        answers=None,
        dismiss_button_ui_flags=0,
        alert_flags=0,
        branding=None,
        tag=None,
        context=None,
    ):
        params = {"message": message, "flags": flags}
        params["parent_message_key"] = parent_message_key
        params["answers"] = answers or []
        params["dismiss_button_ui_flags"] = dismiss_button_ui_flags
        params["alert_flags"] = alert_flags
        params["branding"] = branding
        params["tag"] = tag
        params["context"] = context
        params["broadcast_type"] = broadcast_type
        return self._raw_request("messaging.broadcast", params)

    def retreive_users(self):
        params = {"service_identity": "+default+", "cursor": None}
        friends = list()
        while True:
            results = self._raw_request("friend.list", params)["result"]
            friends.extend(results["friends"])
            if results["friends"] and results["cursor"]:
                params["cursor"] = results["cursor"]
            else:
                break

        return friends
