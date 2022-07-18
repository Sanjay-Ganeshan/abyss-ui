from ast import arg
import kivy
import os
import typing as T

import argparse
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image, AsyncImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.properties import NumericProperty, BooleanProperty, StringProperty

from .data_io import get_blank_image, get_backup, save_backup, get_element_image, PROFILES
from .character_info_reader import list_characters, get_character_image
from .fetch_genshin_data import uncache

LINKED_FLOORS = [[0, 1, 2, 3]]
FLOOR_ELEMS = [
    ["cgp", "a"],
    ["pe", "cgh"],
    ["pg", "hc"],
    ["p", ""]
]

not_allowed = []


def batch(lst: T.List[str], batch_size: int, add_defaults: bool = False) -> T.Iterable[T.List[str]]:
    for start_ix in range(0, len(lst), batch_size):
        sublst = lst[start_ix:start_ix+batch_size]
        while add_defaults and len(sublst) < batch_size:
            sublst.append("")
        yield sublst


class CharacterPickerImage(Image):
    usable = BooleanProperty(True)
    character_name = StringProperty("")
    position_id = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs, keep_ratio=True, allow_stretch=True)
        self.bind(usable=self.on_usable_changed, character_name = self.on_character_name_changed)
        self.on_usable_changed(False, self.usable)
        self.on_character_name_changed(None, self.character_name)
    
    def on_usable_changed(self, old_val, new_val):
        if self.usable:
            self.color = (1.0, 1.0, 1.0, 1.0)
        else:
            self.color = (0.5, 0.5, 0.5, 1.0)
        
    def on_character_name_changed(self, old_val, new_val):
        if len(self.character_name) > 0:
            self.source = get_character_image(self.character_name)
        else:
            self.source = get_blank_image()
    
    def is_empty(self):
        return len(self.character_name) == 0

class ElementList(BoxLayout):
    needed_elements = StringProperty("")
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.image_order = "aceghp"
        self.elements = {
            name: Image(source=get_element_image(name), keep_ratio=True, allow_stretch=True) for name in self.image_order
        }
        for each_element in self.image_order:
            self.add_widget(self.elements[each_element])
        self.bind(needed_elements=self.on_elems_changed)
        self.on_elems_changed("", self.needed_elements)
        
    
    def on_elems_changed(self, old_val, new_val):
        for each_name in self.elements:
            if each_name in new_val:
                self.elements[each_name].color = (1.0, 1.0, 1.0, 1.0)
            else:
                self.elements[each_name].color = (0.0, 0.0, 0.0, 1.0)
        


class AbyssChamber(BoxLayout):
    is_left = BooleanProperty(False)
    floor = NumericProperty(9)
    elements_needed = StringProperty("")
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.party_layout = BoxLayout(orientation='horizontal', spacing=10)
        self.party_images = [
            CharacterPickerImage(
                usable=True,
                character_name="",
                position_id=f"floor-{self.floor}-{1 if self.is_left else 2}-{i}"
            )
            for i in range(4)
        ]
        self.elements = ElementList(size_hint=(1.0, 0.2))
        self.elements.needed_elements = self.elements_needed
        self.bind(elements_needed=self.on_elems_changed)
        self.on_elems_changed("", self.elements_needed)
        for each_img in self.party_images:
            self.party_layout.add_widget(each_img)
        self.add_widget(self.elements)
        self.add_widget(self.party_layout)

    def on_elems_changed(self, old, new):
        self.elements.needed_elements = self.elements_needed

    def pop_team_member(self, ix: int):
        mems = self.get_team_members()
        mems.pop(ix)
        self.set_team_members(mems)

    def add_to_team(self, char_name: str):
        self.set_team_members(self.get_team_members() + [char_name])

    def is_full(self):
        return len(self.get_team_members()) == 4

    def set_team_members(self, char_names):
        assert len(char_names) <= 4
        assert len(set(char_names)) == len(char_names)
        for i in range(4):
            self.party_images[i].character_name = "" if len(char_names) <= i else char_names[i]

    def get_team_members(self):
        return [each_img.character_name for each_img in self.party_images if len(each_img.character_name) > 0]


class AbyssFloor(BoxLayout):
    floor = NumericProperty(9)

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.label = Label(text=f"Floor {self.floor}", size_hint=(1.0, 0.2))
        self.left_team = AbyssChamber(is_left=True, floor=self.floor)
        self.right_team = AbyssChamber(is_left=False, floor=self.floor)
        self.both_teams = BoxLayout(orientation='horizontal', spacing=30)
        self.both_teams.add_widget(self.left_team)
        self.both_teams.add_widget(self.right_team)
        self.add_widget(self.label)
        self.add_widget(self.both_teams)
    
    def get_chamber(self, chamber: int):
        assert chamber == 1 or chamber == 2
        if chamber == 1:
            return self.left_team
        else:
            return self.right_team




class MyApp(App):
    def __init__(self, uid_or_profile: T.Union[str, int], **kwargs):
        super().__init__(**kwargs)

        self.uid_or_profile = uid_or_profile
        self.player_uid = PROFILES.get(self.uid_or_profile, self.uid_or_profile)

        self.character_list = BoxLayout(orientation='vertical', spacing=3)
        self.character_list_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        self.character_list_scroll.add_widget(self.character_list)
        self.left_and_right = BoxLayout(orientation='horizontal')
        self.left_and_right.add_widget(self.character_list_scroll)
        
        character_names = list_characters(self.player_uid)
        assert len(set(character_names)) == len(character_names)
        self.character_picker_images = []
        batch_size = 6
        for batch_ix, character_batch in enumerate(batch(character_names, batch_size, add_defaults=True)):
            box = BoxLayout(orientation='horizontal', spacing=3)
            self.character_list.add_widget(box)
            for within_batch_ix, char_name in enumerate(character_batch):
                uid = f"list-{batch_ix * batch_size + within_batch_ix}"
                picker = CharacterPickerImage(usable=len(char_name) > 0, character_name=char_name, position_id=uid)
                self.character_picker_images.append(picker)
                picker.bind(on_touch_down=self.on_touch_list_image)
                box.add_widget(picker)

        self.floors = [AbyssFloor(floor=n) for n in range(9,13)]
        self.floors_view = BoxLayout(orientation='vertical')
        for floor_ix, each_floor in enumerate(self.floors):
            for chamber_ix, each_chamber in enumerate([1, 2]):
                the_chamber = each_floor.get_chamber(each_chamber)
                the_chamber.elements_needed = FLOOR_ELEMS[floor_ix][chamber_ix]
                for each_pos in range(4):
                    each_floor.label.bind(on_touch_down = self.on_touch_floor_label)
                    the_chamber.party_images[each_pos].bind(on_touch_down=self.on_touch_chamber_image)
            self.floors_view.add_widget(each_floor)
        self.left_and_right.add_widget(self.floors_view)
        self.to_populate = None
        self.load()
        self.bind(on_stop=self.dump)
        
    def dump(self, *args):
        save_backup(
            [[each_floor.get_chamber(1).get_team_members(), each_floor.get_chamber(2).get_team_members()] for each_floor in self.floors],
            self.uid_or_profile
        )
    
    def load(self, *args):
        for floor_ix, each_floor in enumerate(get_backup(self.uid_or_profile)):
            chamber1, chamber2 = each_floor
            self.floors[floor_ix].get_chamber(1).set_team_members(chamber1)
            self.floors[floor_ix].get_chamber(2).set_team_members(chamber2)



    def get_character_image(self, uid):
        if uid.startswith('list'):
            return self.character_picker_images[int(uid.split('-')[1])]
        elif uid.startswith('floor'):
            floor, chamber, pos = map(int, uid.split('-')[1:])
            return self.floors[floor - 9].get_chamber(chamber).party_images[pos]
        else:
            raise Exception("unexpected uid: " + uid)    

    def get_chamber(self, uid):
        if uid.startswith('floor'):
            floor, chamber, pos = map(int, uid.split('-')[1:])
            return self.floors[floor - 9].get_chamber(chamber), pos
        else:
            raise Exception("unexpected uid: " + uid)
    
    def get_floor(self, uid):
        if uid.startswith('floor'):
            floor, chamber, pos = map(int, uid.split('-')[1:])
            return self.floors[floor - 9]
        else:
            raise Exception("unexpected uid: " + uid)

    def on_touch_list_image(self, char_img, touch):
        if char_img.collide_point(*touch.pos):
            if char_img.usable:
                if self.to_populate is not None:
                    chamber, pos_ix = self.get_chamber(self.to_populate)
                    if not chamber.is_full():
                        chamber.add_to_team(char_img.character_name)
                        char_img.usable = False
                    if chamber.is_full():
                        self.to_populate = None
    
    def on_touch_floor_label(self, lbl, touch):
        if lbl.collide_point(*touch.pos):
            self.to_populate = f"floor-{int(lbl.text.split()[1])}-1-0"
            if self.get_floor(self.to_populate).left_team.is_full():
                self.to_populate = f"floor-{int(lbl.text.split()[1])}-2-0"
            self.refresh_usable_for_floor()

    def on_touch_chamber_image(self, char_img, touch):
        if char_img.collide_point(*touch.pos):
            chamber, pos_ix = self.get_chamber(char_img.position_id)
            if char_img.is_empty():
                self.to_populate = char_img.position_id
            else:
                self.to_populate = char_img.position_id
                for each_char in self.character_picker_images:
                    if not each_char.is_empty() and each_char.character_name == char_img.character_name:
                        each_char.usable = True
                        break
                chamber.pop_team_member(pos_ix)
            self.refresh_usable_for_floor()

    def refresh_usable_for_floor(self):
        used_chars = set()
        if self.to_populate is not None:
            floor_ix = self.get_floor(self.to_populate).floor - 9

            joint_chambers = LINKED_FLOORS
            for join in joint_chambers:
                if floor_ix in join:
                    for each_floor in join:
                        used_chars.update(
                            set(self.floors[each_floor].get_chamber(1).get_team_members())
                        )
                        used_chars.update(
                            set(self.floors[each_floor].get_chamber(2).get_team_members())
                        )
            
        for each_char in self.character_picker_images:
            each_char.usable = (not each_char.is_empty()) and (each_char.character_name not in used_chars) and (not each_char.character_name.lower() in not_allowed)

            
        

            

    def build(self):
        return self.left_and_right

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", choices=list(PROFILES.keys()))
    parser.add_argument(
        "links",
        nargs='+', 
        help = (
            "each is like 01 and means characters cannot be "
            "shared between these floors. all of 0123 should be present"
        )
    )
    parser.add_argument("--uncache", action="store_true", default=False)
    args = parser.parse_args()

    LINKED_FLOORS.clear()
    seen = set()
    for each_link in args.links:
        to_link = list(map(int, each_link))
        for each_floor in to_link:
            assert each_floor in {0, 1, 2, 3} and each_floor not in seen
            seen.add(each_floor)
        LINKED_FLOORS.append(to_link)
    if args.uncache:
        uncache(PROFILES[args.profile])

    the_app: MyApp = MyApp(uid_or_profile=args.profile)
    the_app.run()


if __name__ == "__main__":
    main()
        