from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.list import ThreeLineAvatarIconListItem,TwoLineAvatarIconListItem,OneLineAvatarIconListItem,ImageLeftWidget,IconRightWidget
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.uix.label import Label
from kivy.properties import StringProperty
from kivy.core.text import Label as CoreLabel
from kivy.core.text.markup import MarkupLabel
from kivymd.toast import toast
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarActionButton
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivymd.uix.filemanager import MDFileManager
from kivy.core.window import Window
from kivymd.uix.imagelist.imagelist import SmartTileImage
from kivymd.uix.toolbar import MDActionBottomAppBarButton
from kivy.utils import platform
from kivy.core.window import Window
from plyer.facades import orientation

from database import Database
import datetime
import os

db = Database()

if platform == "win":
    Window.size = (360,740)

# Classes of widgets
class StartScreen(Screen):
    pass

class CreatorScreen(Screen):
    pass

class PlayScreen(Screen):
    pass

class ReturnScreen(Screen):
    pass

class AddBitScreen(Screen):
    pass

class MassUploadScreen(Screen):

    def get_bulk(self):

        text_field = self.ids.set_bulk
        got_text = text_field.text

        try:
            if len(got_text) > 0:
                if ":" and "," in got_text:
                    lines = got_text.split("\n")
                    for line in lines:
                        parts = line.split(":")
                        set_name = parts[0].strip()
                        words = parts[1].strip()
                        words = [word.strip() for word in words.split(",") if len(word.strip()) > 0]

                        if len(set_name)>0:
                            # Validation with the database
                            if not MyApp.set_name_validation(self, set_name):
                                db.insert_set(set_name, "", len(words))
                                [db.insert_words(word, set_name) for word in words]
                            else:
                                text_field.hint_text = "The name of the set is not unique"
                                text_field.hint_text_color_normal = "red"

                else:
                    text_field.hint_text = "Follow pattern -> set name: some word, some word"
                    text_field.hint_text_color_normal = "red"
            else:
                pass
        except Exception as e:
            text_field.text = "Something is wrong. Try again."
            print(e)

    def export(self):

        text_field = self.ids.set_bulk
        sets = db.get_sets()

        big_string = ""

        for set in sets:
            words = ", ".join([w[0] for w in db.get_words(set[0])])

            big_string += f"{set[0]}:{words}\n"

        text_field.text = big_string
        Clipboard.copy(big_string)

        MDSnackbar(
            MDLabel(
                text="Copied",
                theme_text_color="Custom",
                text_color="white",
            ),
            y=dp(20),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.3,
            md_bg_color="lightblue",
            duration=2,
        ).open()

class BitCreatorScreen(Screen):
    pass

class DialogSet(MDBoxLayout):
    dialog_type = StringProperty('default')

    def __init__(self, **kwargs):
        super(DialogSet, self).__init__(**kwargs)

class DialogCheckbox(MDBoxLayout):
    pass


class SetItem(ThreeLineAvatarIconListItem):
    dialog = None

    def delete_set(self, set_item):
        '''Delete the set'''
        set_item = set_item[0]
        db.delete_set(set_item.text)

        self.parent.remove_widget(set_item)
        self.dialog.dismiss()
        self.dialog = None

    def show_alert_dialog(self):
        set_item = [child for child in self.parent.children]
        if not self.dialog:
            self.dialog = MDDialog(
                text="Do you want to delete?",
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda x:self.dialog.dismiss()
                    ),
                    MDFlatButton(
                        text="DELETE",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release= lambda x: self.delete_set(set_item)
                    ),
                ],
                )
            self.dialog.open()

class ListItem(TwoLineAvatarIconListItem):
    '''Custom list item'''

    def __init__(self, pk=None, **kwargs):
        super().__init__(**kwargs)
        # state a pk which we shall use link the list items with the database primary keys
        self.pk = pk

    def delete_item(self, the_list_item):
        '''Delete the set'''
        self.parent.remove_widget(the_list_item)

class ItemConfirm(OneLineAvatarIconListItem):
    divider = None

    def set_icon(self, instance_check):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False

# Main App
class MyApp(MDApp):
    dialog = None
    label = None
    images= None
    words = None
    image_container = None
    text_color = db.cursor.execute("SELECT text_color FROM settings").fetchall()[-1][0]
    init_trigger = db.cursor.execute("SELECT init_trigger FROM settings").fetchall()[-1][0]
    set_name = None

    print(db.cursor.execute("SELECT init_trigger FROM settings").fetchall())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            ext=['.jpg', '.png'],
            preview=True
        )

    def request_android_permissions(self):
        """
        This function requests permission and handles the response via a
        callback.

        The request will produce a popup if permissions have not already been
        been granted, otherwise it will do nothing.
        """
        from android.permissions import request_permissions, Permission

        def callback(permissions, results):
            """
            Defines the callback to be fired when runtime permission
            has been granted or denied. This is not strictly required,
            but added for the sake of completeness.
            """
            if all([res for res in results]):
                print("callback. All permissions granted.")
            else:
                print("callback. Some permissions refused.")

        request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE], callback)


    def build(self):
        self.title = "Baby Words"
        #self.icon = "babywords.png"
        Builder.load_file("stylesheet.kv")
        # Create a screen manager
        sm = ScreenManager()

        # Create screens
        screen_one = StartScreen(name="start_screen")
        screen_two = CreatorScreen(name="creator_screen")
        screen_three = PlayScreen(name="play_screen")
        screen_four = ReturnScreen(name="return_screen")
        # screen_five = SettingsScreen(name="settings_screen")
        screen_six = MassUploadScreen()
        screen_seven = BitCreatorScreen(name="bitcreator_screen")
        screen_eight = AddBitScreen(name="addbit_screen")

        # Add screens to screen manager
        sm.add_widget(screen_one)
        sm.add_widget(screen_two)
        sm.add_widget(screen_three)
        sm.add_widget(screen_four)
        # sm.add_widget(screen_five)
        sm.add_widget(screen_six)
        sm.add_widget(screen_seven)
        sm.add_widget(screen_eight)

        self.theme_cls.primary_palette = "Blue"

        if platform == "android":
            self.request_android_permissions()

        return sm

    def on_start(self):
        self.test_database()
        if self.init_trigger == 0 or self.init_trigger == None:
            self.show_init_dialog()
        else:
            self.load_sets()

    def load_sets(self):
        # Load the saved sets and add them to the MDList widget after init_dialog
        sets = db.get_sets()

        for set in sets:
            words = ", ".join([w[0] for w in db.get_words(set[0])])
            date = self.get_last_time(set[0])

            if date == None:
                date = ""

            if set[2] == "bits":
                color = [0.25, 0.71, 1, 0.8]
                add_text = "Bits: "
            else:
                color = [1,1,1,1]
                add_text = ""

            item = SetItem(text=set[0],
                        secondary_text=f"{add_text}{words}",
                        tertiary_text=f"Last time: {date}",
                        bg_color=color
                           )
            # item.bind(md_bg_color=color)
            self.root.get_screen("start_screen").ids.set_container.add_widget(item)



        if self.dialog:
            self.dialog.dismiss()

        self.change_screen("start_screen")

    def get_last_time(self, name):
        return db.cursor.execute("SELECT last_time_date FROM sets WHERE name=?", (name,)).fetchall()[0][0]

    def show_dialog(self, title, dialog_type, *args):
        if dialog_type == "set":
            helper = "The field is empty or name is no unique"
            hint = "Set name (it must be unique)"
        else:
            helper = ""
            hint = ""

        if self.dialog:
            self.dialog = None

        self.dialog = MDDialog(
                title=f"{title}",
                type="custom",
                content_cls=DialogSet(dialog_type=dialog_type),
                buttons=[
                    MDFlatButton(
                        text="SAVE",
                        theme_text_color="Custom",
                        text_color="orange",
                        on_release=lambda x: self.save(dialog_type)
                    ),
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color="orange",
                        on_release=lambda x: self.close_dialog()
                    )
                ]
            )
        self.dialog.content_cls.ids.set_textfield.helper_text = f"{helper}"
        self.dialog.content_cls.ids.set_textfield.hint_text = f"{hint}"

        self.dialog.content_cls.ids.set_textfield.bind(
            on_text_validate=self.set_error_message,
            on_focus=self.set_error_message,
        )
        self.dialog.open()

    def show_massupload_screen(self):
        # Clean text_field
        text_field = self.root.get_screen("massupload_screen").ids.set_bulk
        text_field.text = ""
        text_field.hint_text = ""

        self.change_screen("massupload_screen")


    def set_error_message(self,*instance_textfield):
        self.dialog.content_cls.ids.set_textfield.error = True

    def save(self, dialog_type):

        text = self.dialog.content_cls.ids.set_textfield.text.strip()

        if self.dialog.content_cls.dialog_type == "set":
            if len(text) < 1 or self.set_name_validation(text):
                self.set_error_message()
            else:
                self.root.get_screen("creator_screen").ids.container.clear_widgets()
                self.root.get_screen("creator_screen").ids.creator_label.text = text
                self.change_screen("creator_screen")

                self.close_dialog()

        elif self.dialog.content_cls.dialog_type == "word":
            self.add_word(text)

        elif self.dialog.content_cls.dialog_type == "bit":
            if len(text) < 1 or self.set_name_validation(text):
                self.set_error_message()
            else:
                self.root.get_screen("bitcreator_screen").ids.container.clear_widgets()
                self.root.get_screen("bitcreator_screen").ids.creator_label.text = text
                self.change_screen("bitcreator_screen")
                self.close_dialog()

        self.dialog.content_cls.ids.set_textfield.text = ""


    def get_setname(self):
        name = self.dialog.content_cls.ids.set_textfield.text.strip()

        if len(name)<1 or self.set_name_validation(name):
            self.set_error_message()
        else:
            self.change_screen("creator_screen")

            self.close_dialog()

    def set_name_validation(self, name):
        sets_name = [element[0] for element in db.is_name_exists()]
        if name in sets_name:
            return True
        else:
            return False

    def update_set_item(self, set_name, date):
        sets = self.root.get_screen("start_screen").ids.set_container.children
        for child in sets:
            if child.text == set_name:
                child.tertiary_text = f"Last time: {date}"

    def play(self,item=None):
        try:
            play_screen = self.root.get_screen("play_screen")
            play_screen.remove_widget(self.image_container)
            self.image_container = None
            play_screen.remove_widget(self.label)
        except:
            pass

        # Settings
        if self.text_color == "Black":
            self.text_color = [0, 0, 0, 1]
        elif self.text_color == "Red":
            self.text_color = [0.8, 0, 0, 1]

        if self.label != None:
            self.root.get_screen("play_screen").ids.rotated_box.clear_widgets()

        self.root.current = "play_screen"

        if item:
            self.set_name = item.text

        # Get the current date and time
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
        db.update_date(self.set_name, formatted_datetime)
        self.update_set_item(self.set_name, formatted_datetime)
        word_set = db.get_words(self.set_name)
        self.words = {w[0]:w[1] for w in word_set}

        first_item = list(self.words.keys())[0]
        image_path = self.words[first_item]

        if 0 < len(first_item) < 11:
            font_size = "110dp"
        elif len(first_item) >= 11:
            font_size = "80dp"

        if image_path != "":
            self.image_container = SmartTileImage(
                source=image_path,
                pos_hint={"center_x": .5, "center_y": .6},
                size_hint=(None, None),
                size=("270dp", "270dp"),
            )
            self.label = Label(
                text=f'{first_item}',
                color=self.text_color,
                bold="True",
                font_size=font_size,
                pos_hint={'center_x': .5, 'center_y': .12}
            )

            self.root.get_screen("play_screen").ids["image_container"] = self.image_container

        else:
            self.label = Label(
                    text=f'{first_item}',
                    color=self.text_color,
                    bold="True",
                    font_size=font_size,
                    pos_hint={'center_x': .5, 'center_y': 0.5}
                )
        if self.image_container:
            self.image_container.bind(on_press=lambda x: self.change_label_text())
            self.root.get_screen("play_screen").ipmds.rotated_box.add_widget(self.image_container)
        self.label.bind(on_touch_down=lambda x,y: self.change_label_text())
        self.root.get_screen("play_screen").ids.rotated_box.add_widget(self.label)

    def change_label_text(self, *args):
        words = list(self.words.keys())
        current_word_index = words.index(self.label.text)
        max_index = len(self.words) - 1

        if current_word_index == max_index:
            self.change_screen("return_screen")
        else:
            word = words[current_word_index+1]
            image_path = self.words[word]
            if image_path != "":
                self.root.get_screen("play_screen").ids["image_container"].source = image_path

            else:
                try:
                    image_container = self.root.get_screen("play_screen").ids["image_container"]
                    self.root.get_screen("play_screen").ids.rotated_box.remove_widget(image_container)
                except KeyError:
                    pass

            self.label.text = word

            if 6 < len(word) < 11:
                self.label.font_size = "110dp"
            elif len(word) >= 11:
                self.label.font_size = "80dp"

    def again(self):
        self.play(item=None)

    def change_screen(self, screen, *args):
        if screen == "addbit_screen":
            img_file = MDIconButton(
                icon="file-image-plus-outline",
                pos_hint={"center_x": .5, "center_y": .5},
                icon_size="128sp")
            img_file.bind(on_release=lambda x: self.file_manager_open())
            rt = self.root.get_screen(screen)
            rt.add_widget(img_file)
            rt.ids["img"] = img_file
            rt.ids.img_textfield.text = ""
            try:
                rt.remove_widget(rt.ids.image)
            except:
                pass


        self.root.current = screen

    def close_dialog(self, *args):
        self.dialog.dismiss()

    def add_word(self, word):
        '''Add word to the list of words'''
        self.root.get_screen("creator_screen").ids.container.add_widget(
            ListItem(text=f"{word}")
        )
    def edit_item(self,set_item, *args):
        # print(self.get_root_window())
        color = set_item.bg_color
        set_name = set_item.text
        words = db.get_words(set_name)

        if color != [0.25, 0.71, 1, 0.8]:
            screen_name = "creator_screen"
            self.change_screen(screen_name)
            screen = self.root.get_screen(screen_name)
            screen.ids.container.clear_widgets()

            screen.ids.creator_label.text = set_name
            for w in words:
                screen.ids.container.add_widget(
                    ListItem(text=f"{w[0]}")
                )
        else:
            screen_name = "bitcreator_screen"
            self.change_screen(screen_name)
            screen = self.root.get_screen(screen_name)
            screen.ids.container.clear_widgets()

            screen.ids.creator_label.text = set_name
            for w in words:
                item_list = ListItem(
                    text=w[0]
                )
                image_for_list = ImageLeftWidget(source=w[1])
                item_list.add_widget(image_for_list)
                screen.ids.container.add_widget(item_list)

        screen.ids.bottom_appbar.action_items = [
                MDActionBottomAppBarButton(icon="arrow-left", on_release=lambda x: self.change_screen("start_screen")),
                MDActionBottomAppBarButton(icon="content-save-all-outline", on_release=lambda x: self.save_set(screen_name,"update"))
        ]


    def show_toast(self, message):
        '''Displays a toast on the screen.'''

        toast(message)

    def save_set(self, screen, *args, **kwargs):

        rt = self.root.get_screen(screen)
        listview = rt.ids.container.children
        name = rt.ids.creator_label.text
        number = len(listview)
        words = [child.text for child in listview[::-1]]

        if "update" in args:
            db.delete_set(name)

        if screen == "bitcreator_screen":
            children =[child.children[1] for child in listview[::-1]]
            grandchildren = [child.children for child in children]
            stype = "bits"
            images = []
            try:
                for grandchild in grandchildren:
                    images.append(grandchild[0].source)
            except:
                images.append("")


        else:
            stype = "words"

        # Delete the old set if it is edited:
        if not self.set_name_validation(name):
            db.delete_set(name)

        db.insert_set(name=name, number=number, settype=stype)

        if stype == "words":
            [db.insert_words(word=word, set_name=name) for word in words]
        else:
            zipped = zip(words, images)
            [db.insert_words(word=element[0], set_name=name, image=element[1]) for element in zipped]


        self.show_toast("Saved")

        # Add a set to the list of start screen
        self.root.get_screen("start_screen").ids.set_container.clear_widgets()
        self.load_sets()
        self.change_screen("start_screen")

    def show_confirmation_dialog(self):

        self.dialog = MDDialog(
            title="Text color",
            type="confirmation",
            items=[
                ItemConfirm(text="Black"),
                ItemConfirm(text="Red"),
            ],
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_press=lambda x: self.change_text_color(self.dialog.items),
                    on_release=lambda x: self.dialog.dismiss()
                ),
            ],
        )
        self.dialog.open()

    def change_text_color(self, items):
        for item in self.dialog.items:
            if item.ids.check.active:
                color = item.text
                print(color)

                self.text_color = color
                db.cursor.execute("INSERT INTO settings(text_color,init_trigger) VALUES(?,?)", (self.text_color, self.init_trigger))
                db.con.commit()



    def open_snackbar(self):
        self.snackbar = MDSnackbar(
                            MDLabel(
                                text="Author: Emilia Jagła",
                                theme_text_color="Custom",
                                text_color="#393231",
                            ),
                            MDLabel(
                                text="Contact: emiliajagla@int.pl",
                                theme_text_color="Custom",
                                text_color="#393231",
                            ),
                            MDSnackbarActionButton(
                                text="OK",
                                theme_text_color="Custom",
                                text_color="#8E353C",
                            ),
                            pos_hint={"center_x": 0.5, "center_y": 0.1},
                            size_hint_x=0.8,
                            md_bg_color="#E8D8D7",
                        )
        self.snackbar.open()

    def show_init_dialog(self):

        if self.dialog:
            self.dialog = None

        self.dialog = MDDialog(
            type="custom",
            content_cls=DialogCheckbox(),
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_press=lambda x: self.check_active(),
                    on_release=lambda x: self.load_sets()
                ),
                MDFlatButton(
                    text="NO",
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x: self.dialog.dismiss()
                ),
            ],
        )
        self.dialog.open()


    def check_active(self):
        values = []
        check1 = self.dialog.content_cls.ids.check1
        check2 = self.dialog.content_cls.ids.check2
        if check1.active:
            values.append("Polish")
            if self.init_trigger == 0 or self.init_trigger == None:
                db.cursor.execute("INSERT INTO settings(text_color, init_trigger) VALUES(?,?)", (self.text_color,1))
                db.con.commit()
                self.init_trigger = 1

        if check2.active:
            values.append("English")
            if self.init_trigger == 0 or self.init_trigger == None:
                db.cursor.execute("INSERT INTO settings(text_color, init_trigger) VALUES(?,?)", (self.text_color,1))
                db.con.commit()
                self.init_trigger = 1

        db.example_sets(values)
        print(db.cursor.execute("SELECT init_trigger FROM settings").fetchall()[-1][0])

    def file_manager_open(self):
        if platform == "android":
            path = "/sdcard/Download/"

        else:
            path = os.path.expanduser("~")+"\\Pictures"
        # self.file_manager.show_disks()
        self.file_manager.show(path)

    def select_path(self, path: str):
        '''
        It will be called when you click on the file name
        or the catalog selection button.

        :param path: path to the selected directory or file;
        '''

        self.exit_manager()

        screen = self.root.get_screen("addbit_screen")
        screen.remove_widget(screen.ids.img)

        image = SmartTileImage(
            source=path,
            pos_hint={"center_x": .5, "center_y": .65},
            size_hint=(None, None),
            size=("320dp", "320dp"),
        )
        screen.add_widget(image)
        screen.ids["image"] = image


    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    def add_bit(self):
        screen = self.root.get_screen("addbit_screen")

        try:
            image_path = screen.ids["image"].source
        except KeyError:
            pass
        word = screen.ids.img_textfield.text.strip()

        if len(word) == 0:
            toast("Empty textfield")
        else:
            creator_screen = self.root.get_screen("bitcreator_screen")
            image_list = creator_screen.ids.container
            item_list = ListItem(
                text=word
            )
            try:
                image_for_list = ImageLeftWidget(source=image_path)
                item_list.add_widget(image_for_list)
            except:
                pass
            image_list.add_widget(item_list)
        self.change_screen("bitcreator_screen")


MyApp().run()
