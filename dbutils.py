import json

jsons = ["settings", "stakeouts"]


def _read(file):
    with open(f'{file}.json') as file:
        return json.load(file)


def _write(file, data):
    with open(f'{file}.json', 'w') as file:
        json.dump(data, file, indent=4)


def initialize():
    try:
        file = open("settings.json")
        file.close()
    except FileNotFoundError:
        bottoken = input("Please input the bot token: ")
        data = {
            "bottoken": bottoken,
            "prefix": "!",
            "logchannel": "",
            "stakeout": "",
            "keys": (),
            "limit": 50
        }
        _write("settings", data)

    try:
        file = open("stakeouts.json")
        file.close()
    except FileNotFoundError:
        data = {
            "users": {},
            "factions": {},
            "companies": {}
        }
        _write("stakeouts", data)


def read(file):
    if file in jsons:
        return _read(file)
    else:
        raise ValueError("Illegal File Name")


def write(file, data):
    if file in jsons:
        _write(file, data)
    else:
        raise ValueError("Illegal File Name")


def get(file, key):
    if file in jsons:
        data = _read(file)
    else:
        raise ValueError("Illegal File Name")

    try:
        return data[key]
    except KeyError:
        return None


def update(file, key, value):
    if file in jsons:
        data = _read(file)
    else:
        raise ValueError("Illegal File Name")

    data[key] = value
    _write(file, data)
