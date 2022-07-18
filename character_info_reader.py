import os
import json
import requests
from .fetch_genshin_data import read_character_data
from genshin.models import GenshinUserStats, Character
import typing as T

mydir = os.path.dirname(os.path.abspath(__file__))
char_image_cache_dir = os.path.join(mydir, "images", "characters")

cached_reads: T.Dict[int, GenshinUserStats] = {}
name2char: T.Dict[str, Character] = {}

def char_order(c: Character):
    return (c.rarity * -1, c.level * -1, c.id)

def _cache_user_data(uid: int) -> None:
    if uid not in cached_reads:
        data: GenshinUserStats = read_character_data(uid)
        cached_reads[uid] = data
        for each_char in data.characters:
            name2char[each_char.name] = each_char

def list_characters(uid: int):
    _cache_user_data(uid)
    data: GenshinUserStats = cached_reads[uid]

    char_names = [
        char.name for char in sorted(
            data.characters,
            key=char_order
        )
    ]

    return char_names

def get_character_image(char_name: str) -> str:
    char_id = name2char[char_name].id
    cache_fname = f"{char_id}.png"
    cache_fpath = os.path.join(char_image_cache_dir, cache_fname)
    if not os.path.isfile(cache_fpath):
        url = name2char[char_name].icon
        response = requests.get(url)
        with open(cache_fpath, "wb") as f:
            f.write(response.content)
    return cache_fpath