import genshin
from load_char_data import load_character_data
import typing as T
from genshin.models import Character, GenshinUserStats, Artifact


def get_build_level(char: Character) -> T.Tuple[int, int, int, int]:
    artifact_total_level = sum([each_artifact.level for each_artifact in char.artifacts])
    weapon_level = char.weapon.level
    char_level = min(80, char.level) * 2

    build_level = artifact_total_level + weapon_level + char_level
    return build_level, char_level, weapon_level, artifact_total_level


def main():
    char_data: GenshinUserStats = load_character_data()

    chars: T.List[Character] = sorted(char_data.characters, key=get_build_level, reverse=True)
    for each_character in chars:
        build_level, char_level, weapon_level, artifact_total_level = get_build_level(each_character)
        if build_level != 350:
            info = []
            if char_level < 160:
                info.append("LVL")
            if artifact_total_level < 100:
                info.append("ART")
            if weapon_level < 90:
                info.append("WEP")
            print(each_character.name, build_level, ",".join(info))


if __name__ == "__main__":
    main()