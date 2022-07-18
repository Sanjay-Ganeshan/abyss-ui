import asyncio
import genshin
from .auth import load_auth_cookies
import pickle
import os
import typing as T

MYDIR = os.path.dirname(os.path.abspath(__file__))
UID = 617449812

def get_cache_location(uid: int):
    return os.path.join(MYDIR, f"character_data_{uid}.pkl")

async def get_character_data(uid: int) -> genshin.models.GenshinUserStats:
    all_cookies = load_auth_cookies()
    useful_cookies = ["ltoken", "ltuid", "mi18nLang", "_ga", "_MHYUUID"]
    trimmed_cookies = {name: all_cookies[name] for name in all_cookies if name in useful_cookies}
    trimmed_cookies["account_id"] = trimmed_cookies["ltuid"]
    client = genshin.Client(trimmed_cookies, uid=uid)

    data = await client.get_genshin_user(uid)
    return data

async def dump_character_data(uid: int):
    character_data = await get_character_data(uid)
    with open(get_cache_location(uid), "wb") as f:
        pickle.dump(character_data, f)

def sync_dump_character_data(uid: int):
    asyncio.run(dump_character_data(uid))

def read_character_data(uid: int) -> genshin.models.GenshinUserStats:
    if not os.path.isfile(get_cache_location(uid)):
        sync_dump_character_data(uid)

    with open(get_cache_location(uid), "rb") as f:
        return T.cast(genshin.models.GenshinUserStats, pickle.load(f))

def uncache(uid: int) -> None:
    cache_location = get_cache_location(uid)
    if os.path.isfile(cache_location):
        os.remove(cache_location)
