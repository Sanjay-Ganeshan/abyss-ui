import os
import json
import typing as T

mydir = os.path.dirname(os.path.abspath(__file__))
image_dir = os.path.join(mydir, "images")
character_image_dir = os.path.join(image_dir, "characters")
element_image_dir = os.path.join(image_dir, "elements")

def get_backup_path(uid_or_profile: T.Union[str, int]) -> str:
    if isinstance(uid_or_profile, str):
        uid = PROFILES[uid_or_profile.lower()]
    else:
        uid = uid_or_profile
    return os.path.join(mydir, "save", f"teams_{uid}.json")

PROFILES: T.Dict[str, int] = {
    "aether": 612471351,
    "julie": 617449812,
}

def get_element_image(el_name: str) -> str:
    short_form = {long[0]: long for long in ["anemo", "cryo", "electro", "geo", "hydro", "pyro"]}
    el_name = short_form.get(el_name, el_name)
    return os.path.join(element_image_dir, f"{el_name}.png")

def get_blank_image() -> str:
    return os.path.join(image_dir, "blank.png")


def get_backup(uid_or_profile: T.Union[str, int]):
    backup_path = get_backup_path(uid_or_profile)
    if os.path.exists(backup_path):
        with open(backup_path, "r") as f:
            contents = f.read()
        
        try:
            return json.loads(contents)
        except json.JSONDecodeError:
            os.remove(backup_path)
    
    return [
        [[], []],
        [[], []],
        [[], []],
        [[], []]
    ]


def save_backup(backup, uid_or_profile: T.Union[str, int]) -> None:
    contents = json.dumps(backup, indent=4)
    with open(get_backup_path(uid_or_profile), "w") as f:
        f.write(contents)
