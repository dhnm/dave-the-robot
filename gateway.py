# Imports
import websocket
import requests
import json
from functools import partial


class Gateway:
    valid_roles = {
        "comsci": "759478263193665596",
        "secres": "759478760159838219",
        "sofeng": "759479401229320223",
        "gameng": "759479206320406598"
    }

    def __init__(self, *args, base_url, bot_token, server_id, channel_id):
        self.base_url = base_url
        self.bot_token = bot_token
        self.server_id = server_id
        self.channel_id = channel_id
        self.headers = {
            "Authorization": "Bot " + bot_token
        }

    def send_message(self, content, tts=False):
        requests.post(
            f"{self.base_url}/channels/{self.channel_id}/messages",
            headers=self.headers,
            json={"content": content, "tts": tts}
        )

    # for modifying both nickname and roles
    def modify_member(self, user_id, *args, nickname=None, roles=None):
        if nickname or roles:
            data = {}

            if nickname:
                data["nick"] = nickname
            else:
                data["roles"] = roles

            url = f"{self.base_url}/guilds/{self.server_id}/members/{user_id}"
            requests.patch(
                url,
                headers=self.headers,
                json=data
            )

    # remove existing roles and add the new role if it exists
    def assign_unique_role(self, user_id, name, new_role, current_roles=[]):
        if self.valid_roles.get(new_role.lower()):

            if self.valid_roles[new_role.lower()] in (role.lower() for role in current_roles):
                return

            existing_unique_roles = set(
                current_roles) & set(self.valid_roles.keys())
            if existing_unique_roles:
                for role in existing_unique_roles:
                    current_roles.remove(role)

            current_roles.append(self.valid_roles[new_role.lower()])

            self.modify_member(user_id, roles=current_roles)
            self.send_message(f"Set {name}'s role to {new_role}.")

        else:
            print("Invalid role.")

    def set_nickname(self, user_id, name, new_nickname):
        if name == new_nickname:
            return
        try:
            self.modify_member(user_id, nickname=new_nickname)
            self.send_message(
                f"Hello {new_nickname}! Your name change was successful.")
        except:
            print(
                f"ERROR: Unsuccessful name change from {name} to {new_nickname}.")

    # Event handlers
    def on_close(self, ws):
        print("\n\n******* CLOSE *******")

    def on_error(self, ws, error):
        print("\n\n####### ERROR #######")
        print(error)

    def on_message(self, ws, message):
        print("\n\n$$$$$$ MESSAGE $$$$$$")
        message_json = json.loads(message)

        # print("debug message: ", message_json.get("t"))

        # filter events in channel_id
        if (isinstance(message_json.get("d"), dict) and
                message_json["d"].get("channel_id") == self.channel_id):

            payload = message_json["d"]

            # new messages
            if message_json.get("t") == "MESSAGE_CREATE" and isinstance(payload.get("content"), str):

                author_id = payload["author"]["id"]

                if payload["content"] == "!help" or payload["content"] == "!field" or payload["content"] == "!name":

                    self.send_message(f"Hello <@{author_id}>! Assign yourself a role based on your field of study. Type one of the following and hit Enter:\n```!field ComSci\n!field SecRes\n!field SofEng\n!field GamEng```\nTo set your name for this server, use the following format:\n```!name Myname```\nTo display this message again, send `!help`.")

                else:
                    split_message = payload["content"].split()
                    if len(split_message) > 1:
                        if split_message[0] == "!field":
                            self.assign_unique_role(
                                payload["author"]["id"],
                                payload["member"].get(
                                    "nick") or payload["author"]["username"],
                                split_message[1],
                                payload["member"].get("roles")
                            )
                        elif split_message[0] == "!name":
                            split_message.pop(0)

                            self.set_nickname(
                                payload["author"]["id"],
                                payload["member"].get(
                                    "nick") or payload["author"]["username"],
                                " ".join(split_message)
                            )

    def on_open(self, ws):
        print("\n\n******* OPEN ********")

        # identify structure
        # https://discord.com/developers/docs/topics/gateway#identify
        p_identify = {
            # opcodes
            # https://discord.com/developers/docs/topics/opcodes-and-status-codes
            'op': 2,
            'd': {
                'token': self.bot_token,
                'properties': {
                    '$os': 'linux',
                    '$browser': 'dave_the_robot',
                    '$device': 'dave_the_robot'
                },
                "compress": False,
                "large_threshold": 250,
                "presence": {
                    # status, eg. "Playing Among Us"
                    # "game": {
                    #     "name": "Among Us",
                    #     "type": 0
                    # },
                    "status": "online",
                    "since": None,
                    "afk": False
                },
                # intents
                # https://discord.com/developers/docs/topics/gateway#gateway-intents
                # intents calculator
                # https://ziad87.net/intents/
                # TODO: Detect new arrivals, check GUILD_MEMBER_* permissions
                # TODO: then change intents to 514
                "intents": 512
            }
        }

        ws.send(json.dumps(p_identify))

    def start(self):
        # Get gateway url
        gateway_response = requests.get(self.base_url + "/gateway")
        gateway_json = gateway_response.json()
        gateway_url = gateway_json["url"] + "/?v=6&encoding=json"
        print("Connection URL: " + gateway_url)

        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(
            gateway_url,
            on_message=partial(Gateway.on_message, self),
            on_error=partial(Gateway.on_error, self),
            on_close=partial(Gateway.on_close, self)
        )
        ws.on_open = partial(Gateway.on_open, self)
        ws.run_forever()
