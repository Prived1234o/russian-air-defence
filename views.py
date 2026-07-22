import arcade
from arcade.gui import UIManager, UITextureButton, UIAnchorLayout, UITextureButtonStyle, UIDropdown, UIOnChangeEvent
from arcade.gui.widgets.buttons import UIFlatButtonStyle
from pyglet.graphics import Batch
from classes import Pvo, PvoTower, PvoRocket, Dron, Refinery, Tank
from math import degrees, atan2, sin, radians
from random import randint, triangular, shuffle, uniform, choice
from constants import (TIME_BETWEEN_DRONS, NEW_DRON_SPEED_MULT, MAX_DRONS, MAX_ROCKETS, NEW_DRON_SPEED_0, STRIKE_COEFF,
                       LOST_ROCKETS_COEFF, MISSED_DRONS_COEFF, DAMAGE_COEFF, INDUSTRY_STRIKE_COEFF, VERSION,
                       TIME_BETWEEN_TEXT,
                       TIME_TO_LAST_TEXT_STAGE, TIME_TO_FIRST_DRON, FLASHING_IMAGE_TIME)
import json
import os
from language import game_controls_text, creator_text, note_text
from classes import bell_sound

style_regular_button: dict[str, UITextureButtonStyle] = {}
dropdown_style = {'normal': UIFlatButtonStyle(
                 font_color=arcade.color.BLACK, bg=arcade.color.WHITE, border=(186, 191, 186, 255), border_width=5),
                 'hover': UIFlatButtonStyle(
                 font_color=arcade.color.BLACK, bg=(226, 226, 226, 255), border=(186, 191, 186, 255), border_width=5)}
dropdown_style['press'] = dropdown_style['hover']

dropdown_active_style = {
    'normal': UIFlatButtonStyle(
        font_color=arcade.color.BLACK, bg=arcade.color.WHITE, border=(186, 191, 186, 255), border_width=3),
    'hover': UIFlatButtonStyle(
        font_color=arcade.color.BLACK, bg=(226, 226, 226, 255), border=(186, 191, 186, 255), border_width=3)}
dropdown_active_style['press'] = dropdown_active_style['hover']

print("Загрузка текстур (2/2).")
button_texture_regular = arcade.load_texture('textures/gui/button regular.png')
button_texture_interact = arcade.load_texture('textures/gui/button interact.png')
empty_texture = arcade.Texture.create_empty(name="empty", size=(1, 1))
# button_texture_disabled = arcade.load_texture('textures/gui/button disabled.png')
# checkbox_texture_on = arcade.load_texture('textures/gui/checkbox on.png')
# checkbox_texture_off = arcade.load_texture('textures/gui/checkbox off.png')

# Сообщения для конечного экрана
# {название: (текстура, отн. ширина (1 = 544p), отн. высота (1 = 360p)}, кол-во позиций для текста,
#                                                                       (только у moskva 24 и tass)
#                            /положение позиций для текста: /    (отн. x, отн. y), (отн. x, отн. y), ...
messages = \
    {'moskva 24 0':   (arcade.load_texture('textures/messages/moskva 24 0.jpg'), 1, 0.8, 3,
                                                                        (0.16, 0.11), (0.315, 0.34), (0.465, 0.57)),
     'moskva 24 1':   (arcade.load_texture('textures/messages/moskva 24 1.jpg'), 1, 0.8, 1, (0.705, 0.185)),
     'moskva 24 2':   (arcade.load_texture('textures/messages/moskva 24 2.jpg'), 1, 0.678, 0),
     'moya moskva 0': (arcade.load_texture('textures/messages/moya moskva 0.jpg'), 1, 0.92),
     'moya moskva 1': (arcade.load_texture('textures/messages/moya moskva 1.jpg'), 1, 1),
     'moya moskva 2': (arcade.load_texture('textures/messages/moya moskva 2.jpg'), 1, 0.94),
     'tass 0':        (arcade.load_texture('textures/messages/tass 0.jpg'), 0.9485, 0.43, 0),
     'tass 1':        (arcade.load_texture('textures/messages/tass 1.jpg'), 1, 0.36, 1, (0.26, 0.415)),
     'tass 2':        (arcade.load_texture('textures/messages/tass 2.jpg'), 0.91, 0.24, 1, (0.48, 0.3675)),
     # 'sobyanin 0':    (arcade.load_texture('textures/messages/sobyanin 0.jpg'), 0.96, 0.422),
     'sobyanin template': (arcade.load_texture('textures/messages/sobyanin template.jpg'), 0.96, 0.422)
     }
Z_images = (
    arcade.load_texture("Z/0.png"),
    arcade.load_texture("Z/1.png"),
    arcade.load_texture("Z/2.png"),
    arcade.load_texture("Z/3.png"),
    arcade.load_texture("Z/4.png"),
    arcade.load_texture("Z/5.png"),
)
previous_image = -1

health_texture = arcade.load_texture('textures/empty health.png')
arcade.load_font('fonts/OpenSans-Regular.ttf')
font_times_new_roman = ("Times New Roman", "Times", "Liberation Serif")
print("Готово!")

prices: dict[str, int] = {'pvo': 1_200_435_200, 'rocket': 9_514_610, 'dron': 18_012_700, 'tank': 730_656_507, 'refinery': 893_980_440_000}
"""
ПВО:            1.200.435.200 рублей\n
Ракета для ПВО:     9.514.610 рублей\n
Беспилотник:       18.012.700 рублей\n
Резервуар:        730.656.507 рублей\n
НПЗ:          893.980.440.000 рублей
"""

with open("settings.json", "r", encoding="utf-8") as settings_f:
    settings = json.load(settings_f)

def screenshot():
    new_screenshot = arcade.get_image(components=3)
    if "screenshots" not in os.listdir():
        os.mkdir("screenshots")
        new_screenshot_num = 0
    else:
        new_screenshot_num = 0
        for old_screenshot in os.listdir("screenshots"):
            if old_screenshot[:10:] == "screenshot" and old_screenshot[-4::] == ".png":
                new_screenshot_num = max(new_screenshot_num, int(old_screenshot[10:-4:]))
        new_screenshot_num += 1
    new_screenshot.save(f'screenshots/screenshot{new_screenshot_num}.png')

class Menu(arcade.View):
    def __init__(self, show_flashing_image: bool = False):
        super().__init__()
        w = self.window.width
        h = self.window.height

        self.time = 0

        # r -- сокращение от relative
        self.r = w / 1536
        # 1536 пикселей -- это ширина окна, с которым я тестировал игру у себя
        # Возможно, это из-за fullscreen=True
        global style_regular_button
        style_regular_button = {
            "normal": UITextureButtonStyle(font_color=arcade.color.BLACK, font_size=15*self.r),
            "hover": UITextureButtonStyle(font_color=arcade.color.BLACK, font_size=15*self.r),
            "press": UITextureButtonStyle(font_color=arcade.color.BLACK, font_size=15*self.r),
            "disabled": UITextureButtonStyle(font_color=arcade.color.TRANSPARENT_BLACK, font_size=15*self.r)}

        self.keybind_button: None | UITextureButton = None

        self.batch = Batch()

        self.title = arcade.Text('российское ПВО', w * 0.5, h * 0.8, color=arcade.color.BLACK, font_size=60*self.r,
                                 align='center', bold=True, anchor_x='center', anchor_y='center', batch=self.batch)
        self.version_text = arcade.Text(VERSION, w * 0.5, h * 0.725, color=arcade.color.BLACK, font_size=20*self.r,
                                        align='center', anchor_x='center', anchor_y='center', batch=self.batch)
        self.game_controls_text = arcade.Text('', w * 0.02, h * 0.7, color=arcade.color.BLACK, font_size=15*self.r,
                                              multiline=True, width=w * 0.28, batch=self.batch)
        self.game_controls_text.text = game_controls_text[settings["language"]]
        self.note_text = arcade.Text(note_text[settings["language"]], w * 0.005, h * 0.04,
                                        color=arcade.color.BLACK, anchor_y='bottom', font_size=12*self.r,
                                        batch=self.batch)
        self.hint_text = arcade.Text("ESC — выход", w / 2, h * 0.035 / 2,
                                     color=arcade.color.BLACK, font_size=12*self.r,
                                     anchor_x="center", anchor_y="center", align="center", batch=self.batch)
        self.future_text = arcade.Text("Скоро здесь что-то будет", w * 0.75, h * 0.7, rotation=60, font_size=30*self.r,
                                       color=arcade.color.DARK_GRAY, batch=self.batch)
        self.creator_text = arcade.Text(creator_text[settings["language"]], w * 0.995, h * 0.04,
                                        color=arcade.color.BLACK, font_size=12*self.r,
                                        anchor_x='right', anchor_y='bottom', batch=self.batch)
        # Кнопка
        self.ui_manager = UIManager()
        anchor = self.ui_manager.add(UIAnchorLayout())

        button_play = anchor.add(UITextureButton(text="Играть", width=w * 0.09, height=w * 0.04,
                                                 texture=button_texture_regular, texture_hovered=button_texture_interact,
                                                 texture_pressed=button_texture_interact, style=style_regular_button),
                                 anchor_x='left', anchor_y='bottom', align_x=w * 0.455, align_y=h * 0.1)
        @button_play.event("on_click")
        def on_click(event):
            game_view = Game()
            game_view.setup()
            self.window.show_view(game_view)

        language_dropdown = self.ui_manager.add(UIDropdown(
            x=w * 0.02, y=h * 0.9, width=w * 0.12, height=w * 0.02,
            default=settings["language"], options=["русский", "русский (Россия)"],
            primary_style=dropdown_style, dropdown_style=dropdown_style, active_style=dropdown_active_style)
        )
        @language_dropdown.event()
        def on_change(event: UIOnChangeEvent):
            if event.old_value == event.new_value:
                return
            settings["language"] = event.new_value
            with open("settings.json", "w+", encoding="utf-8") as settings_f:
                json.dump(settings, settings_f, indent=4, ensure_ascii=False)
            if event.new_value == "русский (Россия)":
                self.window.show_view(Menu(True))
            else:
                self.window.show_view(Menu())

        self.ui_manager.enable()

        self.language_text = arcade.Text("Язык:", language_dropdown.left, language_dropdown.top + h * 0.01,
                                         color=arcade.color.BLACK, font_size=20 * self.r,
                                         anchor_y='bottom', batch=self.batch)

        self.flashing_image = None
        if show_flashing_image:
            global previous_image
            # Это чтобы картинка не повторялась два раза подряд
            image = randint(0, len(Z_images) - 1)
            while image == previous_image:
                image = randint(0, len(Z_images) - 1)

            self.flashing_image = Z_images[image]
            previous_image = image

            arcade.play_sound(bell_sound)

        self.background_color = (232, 232, 232)

    def on_draw(self) -> bool | None:
        self.clear()
        arcade.draw_rect_filled(arcade.LRBT(0, self.window.width, 0, self.window.height * 0.035), arcade.color.WHITE)
        self.batch.draw()
        self.ui_manager.draw()
        if self.flashing_image and self.time <= FLASHING_IMAGE_TIME:
            arcade.draw_texture_rect(self.flashing_image, arcade.LRBT(0, self.window.width, 0, self.window.height),
                                     alpha=int(255 - 255 * self.time / FLASHING_IMAGE_TIME))

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol == arcade.key.ESCAPE:
            self.window.close()

        elif symbol == arcade.key.S:
            screenshot()

    def on_update(self, delta_time: float):
        self.time += delta_time

class Game(arcade.View):
    num_rockets = 0
    num_lost_rockets = 0
    num_launched_rockets = 0
    num_strikes = 0
    num_drons = 0
    num_missed_drons = 0
    num_industry_strikes = 0

    time = 0

    time_since_last_dron = 0
    new_drone_speed = NEW_DRON_SPEED_0

    pvo_list = None
    explosions_list = None
    smoke_list = None
    rocket_list = None
    rocket_collision_list = None
    dron_list = None
    dron_collision_list = None
    oblomki_collision_list = None
    industry_list = None
    misc_list = None

    refinery_health_rect = None
    refinery_health = 0
    pvo_health_rect = None
    pvo_health = 0
    tank1_health_rect = None
    tank1_health = 0
    tank2_health_rect = None
    tank2_health = 0

    score = 0

    end = False
    pause = False

    text_batch = None

    background_image = None

    def __init__(self):
        print("Инициализация игры.")
        super().__init__()
        self.r = self.window.width / 1536

        self.text_batch = Batch()

        # self.fps_text = arcade.Text("", 10, self.window.height * 0.97, color=arcade.color.BLACK, batch=self.text_batch)
        self.rockets_text = arcade.Text("", self.window.width * 0.01, self.window.height * 0.105,
                                        color=arcade.color.BLACK, width=200, font_size=12*self.r,
                                        anchor_y='center', multiline=True, batch=self.text_batch)
        self.time_text = arcade.Text("", self.window.width * 0.5, self.window.height * 0.105,
                                      color=arcade.color.BLACK, font_size=40*self.r,
                                      anchor_x='center', anchor_y='center', batch=self.text_batch)
        self.score_text = arcade.Text("", self.window.width * 0.98, self.window.height * 0.105,
                                      color=arcade.color.BLACK, font_size=25*self.r,
                                      anchor_x='right', anchor_y='center', batch=self.text_batch)
        self.hint_text = arcade.Text("", self.window.width / 2, self.window.height * 0.035 / 2,
                                     color=arcade.color.BLACK, font_size=12*self.r,
                                     anchor_x="center", anchor_y="center", align="center", batch=self.text_batch)

        self.pause_text = arcade.Text("Игра на паузе", self.window.width / 2, self.window.height * 0.76,
                                      color=arcade.color.BLACK, font_size=40*self.r,
                                      anchor_x='center', anchor_y='center', align='center', batch=self.text_batch)
        self.text_hint_rect = arcade.XYWH(self.window.width / 2, self.window.height * 0.76,
                                          self.window.width * 0.4, self.window.height * 0.3)
        self.end_text = arcade.Text("Атака окончена", self.window.width / 2, self.window.height * 0.8,
                                    color=arcade.color.BLACK, font_size=40*self.r,
                                    anchor_x='center', align='center', batch=self.text_batch)
        self.end_text_hint = arcade.Text("Для выхода в меню нажмите E\nДля перезапуска нажмите R",
                                         self.window.width / 2, self.window.height * 0.72,
                                         color=arcade.color.BLACK, font_size=20*self.r,
                                         width=int(self.text_hint_rect.width), multiline=True,
                                         anchor_x='center', align='center', batch=self.text_batch)

        self.background_rect = arcade.XYWH(self.window.width * 0.5, self.window.height * 0.55,
                                           self.window.width, self.window.height)
        print("Готово!")

    def setup(self):
        self.num_lost_rockets = 0
        self.num_launched_rockets = 0
        self.num_strikes = 0
        self.num_missed_drons = 0
        self.num_industry_strikes = 0

        self.num_rockets = 0
        self.num_drons = 0

        self.time = 0

        self.time_since_last_dron = 0
        self.new_drone_speed = Dron.speed

        self.misc_list = arcade.SpriteList()
        self.explosions_list = arcade.SpriteList()
        self.smoke_list = arcade.SpriteList()

        self.pvo_list = arcade.SpriteList()
        self.pvo_list.append(Pvo(self, self.window.width * 0.37, self.window.height * 0.5))
        self.misc_list.append(PvoTower(self, self.window.width * 0.37, self.window.height * 0.335))
        self.pvo_health_rect = arcade.XYWH(self.pvo_list[0].center_x, self.window.height * 0.19,
                                           self.window.width * 0.12, self.window.height * 0.015)
        self.pvo_health = 100

        self.rocket_list = arcade.SpriteList()
        self.rocket_collision_list = arcade.SpriteList()

        self.dron_list = arcade.SpriteList()
        self.dron_collision_list = arcade.SpriteList()
        self.oblomki_collision_list = arcade.SpriteList()

        self.industry_list = arcade.SpriteList()
        self.industry_list.append(Refinery(self, self.window.width * 0.16, self.window.height * 0.323))
        self.refinery_health = 100
        self.refinery_health_rect = arcade.XYWH(self.industry_list[0].center_x, self.window.height * 0.19,
                                                self.window.width * 0.12, self.window.height * 0.015)
        self.industry_list.append(Tank(self, self.window.width * 0.5, self.window.height * 0.26))
        self.tank1_health = 100
        self.tank1_health_rect = arcade.XYWH(self.industry_list[1].center_x, self.window.height * 0.19,
                                             self.window.width * 0.12, self.window.height * 0.015)
        self.industry_list.append(Tank(self, self.window.width * 0.63, self.window.height * 0.26))
        self.tank2_health = 100
        self.tank2_health_rect = arcade.XYWH(self.industry_list[2].center_x, self.window.height * 0.19,
                                             self.window.width * 0.12, self.window.height * 0.015)

        self.pause = False
        self.end = False
        self.pause_text.visible = False
        self.end_text.visible = False
        self.end_text_hint.visible = False
        self.hint_text.text = "ESC — выход    Space — пауза    F — завершить игру    R — перезапуск"

        self.score = 0

        self.background_image = arcade.load_texture(f'textures/background/{randint(1, 4)}.jpg')

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background_image, self.background_rect)

        self.dron_list.draw()
        self.pvo_list.draw()
        self.rocket_list.draw()

        arcade.draw_rect_filled(arcade.LRBT(0, self.window.width, 0, self.window.height * 0.22), (232, 232, 232))
        arcade.draw_rect_filled(arcade.LRBT(0, self.window.width, 0, self.window.height * 0.035), arcade.color.WHITE)
        arcade.draw_rect_filled(arcade.LRBT(0, self.window.width, self.window.height * 0.205, self.window.height * 0.22),
                                (64, 64, 64))

        self.misc_list.draw()
        self.industry_list.draw()
        self.smoke_list.draw()
        self.explosions_list.draw()

        arcade.draw_rect_filled(arcade.LRBT(0, self.window.width, self.window.height * 0.175, self.window.height * 0.205),
                                (80, 80, 80))
        self.draw_health(self.refinery_health, self.refinery_health_rect)
        self.draw_health(self.tank1_health, self.tank1_health_rect)
        self.draw_health(self.tank2_health, self.tank2_health_rect)
        self.draw_health(self.pvo_health, self.pvo_health_rect)

        if self.end or self.pause:
            arcade.draw_rect_filled(self.text_hint_rect, (255, 255, 255, 127))
        self.text_batch.draw()

    def draw_health(self, health: float, health_rect: arcade.Rect):
        empty_health_color = (183, 91, 91)
        filled_health_color = (14, 175, 14)

        arcade.draw_rect_filled(arcade.XYWH(health_rect.center_x, health_rect.center_y,
                                            health_rect.width * 0.98,
                                            health_rect.height * 0.98),
                                empty_health_color)
        if health:
            arcade.draw_rect_filled(arcade.LRBT(health_rect.left,
                                                health_rect.left +
                                                health_rect.width * health / 100,
                                                health_rect.bottom * 1.01,
                                                health_rect.top * 0.99),
                                    filled_health_color)
        arcade.draw_texture_rect(health_texture, health_rect)

    def on_update(self, delta_time: float):
        # self.fps_text.text = f"{1 / delta_time: 0.2f} FPS"

        if self.pause:
            return

        self.time += delta_time

        self.time_since_last_dron += delta_time

        self.rocket_list.update(delta_time)
        self.dron_list.update(delta_time)
        self.industry_list.update(delta_time)
        self.smoke_list.update(delta_time)
        self.pvo_list.update(delta_time)
        self.misc_list.update(delta_time)

        if not self.pvo_list or not self.industry_list and not self.end:
            self.end_game()

        self.num_rockets = 0
        self.num_drons = 0
        for rocket in self.rocket_list:
            if not rocket.exploding:
                self.num_rockets += 1
        for dron in self.dron_list:
            if not dron.exploding:
                self.num_drons += 1
        if (self.time >= TIME_TO_FIRST_DRON and self.time_since_last_dron >= TIME_BETWEEN_DRONS
                and self.num_drons <= MAX_DRONS - 1 and not self.end):
            new_dron = Dron(self, self.window.width + 100,
                            randint(int(self.window.height * 0.4), int(self.window.height * 0.9)), self.new_drone_speed)
            new_dron.set_target(self.industry_list[int(round(triangular(0, len(self.industry_list) - 1, -0.6)))])
            self.dron_list.append(new_dron)
            self.time_since_last_dron = 0
            self.new_drone_speed *= NEW_DRON_SPEED_MULT

        if not self.end:
            self.score = int(self.num_strikes * STRIKE_COEFF - self.num_lost_rockets * LOST_ROCKETS_COEFF
                             - self.num_industry_strikes * INDUSTRY_STRIKE_COEFF - self.num_missed_drons * MISSED_DRONS_COEFF
                             - ((100 - self.pvo_health) + (100 - self.refinery_health) +
                                (200 - self.tank1_health - self.tank2_health)) * DAMAGE_COEFF)

            minutes = int(self.time // 60)
            seconds = int(self.time % 60)
            self.time_text.text = f"{'0' if minutes < 10 else ''}{minutes}:{'0' if seconds < 10 else ''}{seconds}"
            self.score_text.text = f"Счёт: {' ' * (4 - len(str(self.score)))}{self.score}"
            self.rockets_text.text = (f"Запущено ракет: {self.num_launched_rockets}\n"
                                      f"Попадания в дроны: {self.num_strikes}")

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            self.window.close()
        elif symbol == arcade.key.R:
            self.setup()
        elif symbol == arcade.key.E and self.end:
            self.window.show_view(End(self.num_launched_rockets, self.num_strikes,
                                      self.num_missed_drons, self.num_industry_strikes,
                                      self.score, self.time_text.text,
                                      self.pvo_health, self.refinery_health, self.tank1_health, self.tank2_health))
        elif symbol == arcade.key.F:
            self.end_game()

        elif symbol == arcade.key.SPACE and not self.end:
            self.pause = not self.pause
            self.pause_text.visible = self.pause

        elif symbol == arcade.key.S:
            screenshot()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        if self.num_rockets != 0 and not self.end:
            rocket: PvoRocket = self.rocket_list[-1]
            new_rot = degrees(atan2(x - rocket.center_x, y - rocket.center_y))
            rot = rocket.rotation - int(rocket.rotation > 180) * 360
            delta = (new_rot - rot + 180) % 360 - 180
            turning_speed = (1 - (sin(radians(delta - 180)/2))**10) * 500
            rocket.turning_speed = turning_speed

            if -3 <= delta <= 3:
                rocket.turning_right = False
                rocket.turning_left = False
            elif delta > 0:
                rocket.turning_right = True
                rocket.turning_left = False
            elif delta < 0:
                rocket.turning_right = False
                rocket.turning_left = True

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        if not self.pvo_list:
            return
        if self.num_rockets <= MAX_ROCKETS - 1 and not self.pvo_list[0].exploding and not self.end and not self.pause:
            pvo_x = self.pvo_list[0].center_x
            pvo_y = self.pvo_list[0].center_y
            new_rot = degrees(atan2(x - pvo_x, y - pvo_y))
            if -180 <= new_rot < -90:
                new_rot = -90
            elif 90 < new_rot < 180:
                new_rot = 90
            if self.num_rockets != 0:
                self.rocket_list[-1].turning_right = False
                self.rocket_list[-1].turning_left = False
            self.rocket_list.append(PvoRocket(self, pvo_x, pvo_y, rot=new_rot))
            self.num_launched_rockets += 1

    def give_new_target(self) -> None | Tank | Refinery | Pvo:
        if self.industry_list:
            return self.industry_list[randint(0, len(self.industry_list) - 1)]
        return None

    def end_game(self) -> None:
        self.end = True
        self.end_text.visible = True
        self.end_text_hint.visible = True
        self.hint_text.text = "ESC — выход    E — меню    R — перезапуск"
        self.pause_text.visible = False

class End(arcade.View):
    time = 0
    total_price = 0

    new_best_score = False
    new_best_time = False

    def __init__(self, num_launched_rockets: int, num_strikes: int, num_missed_drons: int, num_industry_strikes: int,
                 score: int, time_str: str, pvo_health: int, refinery_health: int, tank1_health: int, tank2_health: int):
        super().__init__()
        w = self.window.width
        h = self.window.height
        self.r = w / 1536

        self.time = -0.5
        self.stage = 0

        player_stats: dict[str, int | str]
        if os.path.exists("player stats.json"):
            with open('player stats.json') as player_stats_file:
                player_stats = json.load(player_stats_file)

                self.score = score
                if score > player_stats['best score']:
                    self.new_best_score = True
                    player_stats['best score'] = score

                self.time_str = time_str
                mins_old, secs_old = map(int, time_str.split(':'))
                mins_new, secs_new = map(int, player_stats['best time'].split(':'))
                if mins_old > mins_new or mins_old == mins_new and secs_old > secs_new:
                    self.new_best_time = True
                    player_stats['best time'] = time_str
        else:
            player_stats = {"best score": score, "best time": time_str}
            self.new_best_time = True
            self.new_best_score = True
        best_score = player_stats['best score']
        best_time = player_stats['best time']
        with open('player stats.json', 'w+', encoding='utf-8') as player_stats_file:
            json.dump(player_stats, player_stats_file, indent=4)

        self.price_rockets = num_launched_rockets * prices['rocket']
        self.price_pvo = int((100 - pvo_health) / 100 * prices['pvo'])
        self.price_refinery = int((100 - refinery_health) / 100 * prices['refinery'])
        self.price_tanks = int((200 - (tank1_health + tank2_health)) / 200 * prices['tank'])

        self.total_price = 0

        ################## Официальные сообщения ##########################
        self.messages_batch = Batch()
        self.messages_rect = arcade.LRBT(0, w * 0.23, 0, h * 0.9)
        self.messages_text = arcade.Text('ОФИЦИАЛЬНЫЕ СООБЩЕНИЯ', self.messages_rect.center_x, h * 0.96,
                                         color=arcade.color.BLACK, font_size=25*self.r,
                                         width=int(self.messages_rect.width), multiline=True,
                                         anchor_x='center', align='center')
        self.messages_list: list[tuple[arcade.Texture, arcade.Rect]] = []
        self.messages_data_list: list[arcade.Text] = []
        self.messages_texts: list[arcade.Text] = []
        self.append_messages_list(num_strikes, num_missed_drons)
        self.messages_visible = False

        ################# ОТЧЁТ ########################
        self.tables_batch = Batch()
        self.report_rect = arcade.LRBT(w * 0.3, w * 0.99, h * 0.4, h * 0.98)
        self.report_text = arcade.Text('ОТЧЁТ', self.report_rect.center_x, h * 0.9,
                                       color=arcade.color.BLACK, font_name=font_times_new_roman,
                                       font_size=40*self.r, width=int(w * 0.2), anchor_x='center')

        # Таблица "Результаты выполнения поставленных задач"
        self.table_drons_title = arcade.Text('Результат выполнения поставленных задач',
                                             w * 0.475, h * 0.82, color=arcade.color.BLACK,
                                             font_size=18*self.r, font_name=font_times_new_roman,
                                             anchor_x='center', align='center', batch=self.tables_batch)
        self.table_drons = ((w * 0.32, h * 0.8), (w * 0.32, h * 0.5),
                            (w * 0.553, h * 0.8), (w * 0.553, h * 0.5),
                            (w * 0.63, h * 0.8), (w * 0.63, h * 0.5),
                            (w * 0.32, h * 0.8), (w * 0.63, h * 0.8),
                            (w * 0.32, h * 0.775), (w * 0.63, h * 0.775),
                            (w * 0.32, h * 0.72), (w * 0.63, h * 0.72),
                            (w * 0.32, h * 0.665), (w * 0.63, h * 0.665),
                            (w * 0.32, h * 0.61), (w * 0.63, h * 0.61),
                            (w * 0.32, h * 0.555), (w * 0.63, h * 0.555),
                            (w * 0.32, h * 0.5), (w * 0.63, h * 0.5))
        self.table_drons_header: list[arcade.Text] = []
        self.table_drons_header.append(arcade.Text('наименование', w * 0.437, h * 0.78, color=arcade.color.BLACK,
                                                   font_name=font_times_new_roman, font_size=12*self.r,
                                                   anchor_x='center', align='center', batch=self.tables_batch))
        self.table_drons_header.append(arcade.Text('значение', w * 0.592, h * 0.78, color=arcade.color.BLACK,
                                                   font_name=font_times_new_roman, font_size=12*self.r,
                                                   anchor_x='center', align='center', batch=self.tables_batch))
        try:
            percentage_text = f'{num_strikes / (num_missed_drons + num_strikes) * 100: 0.2f}%'
        except ZeroDivisionError:
            percentage_text = f'{0: 0.2f}%'
        try:
            rockets_per_dron_text = f'{num_launched_rockets / num_strikes : 0.2f}'
        except ZeroDivisionError:
            rockets_per_dron_text = f'{0: 0.2f}'

        table_drons_contents = (('Сбитых БПЛА',                 f'{num_strikes}'),
                                ('Процент уничтожения БПЛА',    percentage_text),
                                ('Ракет на дрон',               rockets_per_dron_text),
                                ('Попаданий по пром. объектам', f'{num_industry_strikes}'))
        self.table_drons_contents: list[arcade.Text] = []
        line_num = 0
        for line in table_drons_contents:
            new_position_text = arcade.Text(line[0], w * 0.437, h * (0.735 - line_num * 0.055),
                                            color=arcade.color.BLACK, font_size=16*self.r,
                                            font_name=font_times_new_roman,
                                            anchor_x='center', align='center', batch=self.tables_batch)
            new_position_text.visible = False
            new_value_text = arcade.Text(line[1], w * 0.592, h * (0.735 - line_num * 0.055),
                                         color=arcade.color.BLACK, font_size=16*self.r,
                                         font_name=font_times_new_roman,
                                         anchor_x='center', align='center', batch=self.tables_batch)
            new_value_text.visible = False
            self.table_drons_contents.append(new_position_text)
            self.table_drons_contents.append(new_value_text)
            line_num += 1

        # Таблица "Нанесённый ущерб"
        self.table_destruction_title = arcade.Text('Нанесённый ущерб',
                                             w * 0.825, h * 0.82, color=arcade.color.BLACK,
                                             font_size=18*self.r, font_name=font_times_new_roman,
                                             anchor_x='center', align='center', batch=self.tables_batch)
        self.table_destruction = ((w * 0.67, h * 0.8), (w * 0.67, h * 0.5),
                                  (w * 0.84, h * 0.8), (w * 0.84, h * 0.555),
                                  (w * 0.877, h * 0.8), (w * 0.877, h * 0.5),
                                  (w * 0.98, h * 0.8), (w * 0.98, h * 0.5),
                                  (w * 0.67, h * 0.8), (w * 0.98, h * 0.8),
                                  (w * 0.67, h * 0.775), (w * 0.98, h * 0.775),
                                  (w * 0.67, h * 0.72), (w * 0.98, h * 0.72),
                                  (w * 0.67, h * 0.665), (w * 0.98, h * 0.665),
                                  (w * 0.67, h * 0.61), (w * 0.98, h * 0.61),
                                  (w * 0.67, h * 0.555), (w * 0.98, h * 0.555),
                                  (w * 0.67, h * 0.5), (w * 0.98, h * 0.5))
        self.table_destruction_header: list[arcade.Text] = []
        self.table_destruction_header.append(
            arcade.Text('наименование', w * 0.76, h * 0.78, color=arcade.color.BLACK,
                        font_name=font_times_new_roman, font_size=12*self.r,
                        anchor_x='center', align='center', batch=self.tables_batch)
        )
        self.table_destruction_header.append(
            arcade.Text('кол-во', w * 0.859, h * 0.78, color=arcade.color.BLACK,
                        font_name=font_times_new_roman, font_size=12*self.r,
                        anchor_x='center', align='center', batch=self.tables_batch)
        )
        self.table_destruction_header.append(
            arcade.Text('сумма ущерба, руб', w * 0.929, h * 0.78, color=arcade.color.BLACK,
                        font_name=font_times_new_roman, font_size=12*self.r,
                        anchor_x='center', align='center', batch=self.tables_batch)
        )
        table_destruction_contents = ((num_launched_rockets, 'Ракеты для ПВО',
                                                            f'{num_launched_rockets}', f'{self.price_rockets: _}'.replace("_", " ")),
                                      (100 - pvo_health, 'ПВО',
                                                            '1', f'{self.price_pvo:_}'.replace("_", " ")),
                                      (100 - refinery_health, 'НПЗ',
                                                            '1', f'{self.price_refinery:_}'.replace("_", " ")),
                                      (200 - (tank1_health + tank2_health), 'Резервуар',
                                                            '2' if tank1_health < 100 and tank2_health < 100 else '1',
                                                            f'{self.price_tanks:_}'.replace("_", " ")))
        self.table_destruction_contents: list[list[arcade.Text]] = []
        line_num = 0
        for line in table_destruction_contents:
            damage = line[0]
            if damage == 0:
                continue
            new_position_text = arcade.Text(line[1], w * 0.76, h * (0.735 - line_num * 0.055),
                                            color=arcade.color.BLACK, font_size=16*self.r,
                                            font_name=font_times_new_roman,
                                            anchor_x='center', align='center', batch=self.tables_batch)
            new_position_text.visible = False
            new_value1_text = arcade.Text(line[2], w * 0.859, h * (0.735 - line_num * 0.055),
                                          color=arcade.color.BLACK, font_size=16*self.r,
                                          font_name=font_times_new_roman,
                                          anchor_x='center', align='center', batch=self.tables_batch)
            new_value1_text.visible = False
            new_value2_text = arcade.Text(line[3], w * 0.929, h * (0.735 - line_num * 0.055),
                                          color=arcade.color.BLACK, font_size=16*self.r,
                                          font_name=font_times_new_roman,
                                          anchor_x='center', align='center', batch=self.tables_batch)
            new_value2_text.visible = False
            self.table_destruction_contents.append([new_position_text, new_value1_text, new_value2_text])
            line_num += 1

        self.table_destruction_contents.append([arcade.Text('Итого:', w * 0.76, h * 0.515,
                                                             color=arcade.color.BLACK, font_size=16*self.r,
                                                             font_name=font_times_new_roman,
                                                             anchor_x='center', align='center', batch=self.tables_batch),
                                                arcade.Text(f'{self.total_price:_}'.replace('_', ' '), w * 0.929, h * 0.515,
                                                            color=arcade.color.BLACK, font_size=16*self.r,
                                                            font_name=font_times_new_roman,
                                                            anchor_x='center', align='center', batch=self.tables_batch)])

        self.player_stats_batch = Batch()
        # Счёт, Лучший     Время, Лучшее
        self.score_text = arcade.Text(f'Счёт: {score}', w * 0.3, h * 0.34,
                                      color=arcade.color.BLACK, font_size=40*self.r,
                                      anchor_x='left', batch=self.player_stats_batch)
        self.score_text.visible = False
        self.best_score_text = arcade.Text(f'Лучший: {best_score}', w * 0.3, h * 0.30,
                                            color=arcade.color.BLACK, font_size=20*self.r,
                                            anchor_x='left', batch=self.player_stats_batch)
        self.best_score_text.visible = False
        if self.new_best_score:
            self.best_score_text.text += '  Новый рекорд!'
        self.time_text = arcade.Text(f'Время: {time_str}', w * 0.3, h * 0.24,
                                     color=arcade.color.BLACK, font_size=40*self.r,
                                     anchor_x='left', batch=self.player_stats_batch)
        self.time_text.visible = False
        self.best_time_text = arcade.Text(f'Лучшее: {best_time}', w * 0.3, h * 0.20,
                                          color=arcade.color.BLACK, font_size=20*self.r,
                                          anchor_x='left', batch=self.player_stats_batch)
        self.best_time_text.visible = False
        if self.new_best_time:
            self.best_time_text.text += '  Новый рекорд!'

        # Рейтинг едра и Цены на бензин
        rating_rate = -1.5
        fuel_rate = 0
        if tank1_health == 0:
            rating_rate -= 1
            fuel_rate += 2.75
        elif tank1_health < 100:
            rating_rate -= 0.5
            fuel_rate += 1.25
        if tank2_health == 0:
            rating_rate -= 1
            fuel_rate += 2.75
        elif tank2_health < 100:
            rating_rate -= 0.5
            fuel_rate += 1.25

        percent_strikes = float(percentage_text[:-1:])
        rating_rate *= 1.1 - percent_strikes / 100 * 0.15
        rating_rate *= 1.1 ** num_industry_strikes
        rating_rate *= (100 - refinery_health) / 100 * 7 + 1
        if refinery_health == 0:
            rating_rate *= 1.8
        fuel_rate *= (100 - refinery_health) / 100 * 16 + 1
        # Домножаем на рандомный фактор
        rating_rate *= uniform(0.9, 1.1)
        fuel_rate *= uniform(0.9, 1.1)

        # Рейтинг не может упасть на ниже чем 100%, но чтобы было красивше, то 99.99%
        rating_rate = max(-99.99, rating_rate)

        self.rates_batch = Batch()
        self.rates_visible = False
        self.rating_text = arcade.Text('Рейтинг «единой россии»:',
                                       w * 0.55, h * 0.3,
                                       color=arcade.color.BLACK, font_size=20*self.r,
                                       anchor_y='center', anchor_x='left', batch=self.rates_batch)
        self.this_week_text0 = arcade.Text('за эту неделю', self.rating_text.right + w * 0.085, self.rating_text.y,
                                           color=arcade.color.BLACK, font_size=20*self.r,
                                           anchor_y='center', batch=self.rates_batch)
        self.rating_rate_text = arcade.Text(f'{"-" if settings["language"] == "русский" else "+"}{abs(rating_rate): 0.2f}%',
                                            self.this_week_text0.left - w * 0.005, self.this_week_text0.y,
                                            color=(127, 0, 0), font_size=20*self.r,
                                            anchor_y='center', anchor_x='right', batch=self.rates_batch)

        self.fuel_text = arcade.Text('Цены на бензин:',
                                     w * 0.55, h * 0.26,
                                     color=arcade.color.BLACK, font_size=20*self.r,
                                     anchor_y='center', anchor_x='left', batch=self.rates_batch)
        self.this_week_text1 = arcade.Text('за эту неделю', self.fuel_text.right + w * 0.085, self.fuel_text.y,
                                           color=arcade.color.BLACK, font_size=20 * self.r,
                                           anchor_y='center', batch=self.rates_batch)
        self.fuel_rate_text = arcade.Text(f'{"+" if settings["language"] == "русский" else "-"}{fuel_rate: 0.2f}%',
                                          self.this_week_text1.left - w * 0.005, self.this_week_text1.y,
                                          color=(127, 0, 0), font_size=20*self.r,
                                          anchor_y='center', anchor_x='right', batch=self.rates_batch)

        # Кнопки
        self.ui_manager = UIManager()
        anchor = self.ui_manager.add(UIAnchorLayout())
        button_play = anchor.add(
            UITextureButton(text="Заново", width=w * 0.12 , height=w * 0.04,
                            texture=button_texture_regular, texture_hovered=button_texture_interact,
                            texture_pressed=button_texture_interact, texture_disabled=empty_texture,
                            style=style_regular_button),
            anchor_x='left', anchor_y='bottom', align_x=w * 0.3, align_y=h * 0.1
        )
        @button_play.event("on_click")
        def on_click(event):
            new_game = Game()
            new_game.setup()
            self.window.show_view(new_game)
        button_play.disabled = True

        button_menu = anchor.add(
            UITextureButton(text="Меню", width=w * 0.12, height=w * 0.04,
                            texture=button_texture_regular, texture_hovered=button_texture_interact,
                            texture_pressed=button_texture_interact, texture_disabled=empty_texture,
                            style=style_regular_button),
            anchor_x='left', anchor_y='bottom', align_x=w * 0.44, align_y=h * 0.1)
        @button_menu.event("on_click")
        def on_click(event):
            self.window.show_view(Menu())
        button_menu.disabled = True

        button_quit = anchor.add(
            UITextureButton(text="Выход", width=w * 0.12, height=w * 0.04,
                            texture=button_texture_regular, texture_hovered=button_texture_interact,
                            texture_pressed=button_texture_interact, texture_disabled=empty_texture,
                            style=style_regular_button),
            anchor_x='left', anchor_y='bottom', align_x=w * 0.58, align_y=h * 0.1)
        @button_quit.event("on_click")
        def on_click(event):
            self.window.close()
        button_quit.disabled = True

        self.hint_text = arcade.Text("ESC — выйти    Пробел — пропустить", w / 2, 10,
                                     color=arcade.color.BLACK, font_size=12*self.r,
                                     width=100, anchor_x="center", align="center")

        self.ui_manager.enable()
        self.background_color = (232, 232, 232)

    def on_draw(self) -> bool | None:
        self.clear()
        arcade.draw_rect_filled(self.report_rect, arcade.color.WHITE)
        arcade.draw_rect_filled(self.messages_rect, (24, 25, 29))
        arcade.draw_lines(self.table_drons, arcade.color.BLACK, line_width=2)
        arcade.draw_lines(self.table_destruction, arcade.color.BLACK, line_width=2)

        self.report_text.draw()
        self.messages_text.draw()
        self.tables_batch.draw()
        self.player_stats_batch.draw()

        if self.messages_visible:
            for message in self.messages_list:
                arcade.draw_texture_rect(message[0], message[1])
            self.messages_batch.draw()

        if self.rates_visible:
            self.rates_batch.draw()

        arcade.draw_rect_filled(arcade.XYWH(self.window.width / 2, 15, self.window.width, 30), arcade.color.WHITE)
        self.hint_text.draw()

        self.ui_manager.draw()

    def on_update(self, delta_time: float) -> bool | None:
        # Анимация постепенного появления текста и всякого такого
        # (не очень эффективно, наверное)
        self.time += delta_time

        table_destruction_lines = len(self.table_destruction_contents) - 1
        if 0 <= self.stage < 4 and self.time >= TIME_BETWEEN_TEXT:
            self.table_drons_contents[self.stage * 2].visible = True
            self.table_drons_contents[self.stage * 2 + 1].visible = True
            self.stage += 1
            self.time = 0
        if 4 <= self.stage < 4 + table_destruction_lines and self.time >= TIME_BETWEEN_TEXT:
            self.table_destruction_contents[self.stage - 4][0].visible = True
            self.table_destruction_contents[self.stage - 4][1].visible = True
            self.table_destruction_contents[self.stage - 4][2].visible = True
            self.total_price += int(self.table_destruction_contents[self.stage - 4][2].text.replace(' ', ''))
            self.table_destruction_contents[-1][1].text = f'{self.total_price:_}'.replace('_', ' ')
            self.stage += 1
            self.time = 0
        if self.stage == 4 + table_destruction_lines and self.time >= TIME_BETWEEN_TEXT:
            self.score_text.visible = True
            self.stage += 1
            self.time = 0
        if self.stage == 5 + table_destruction_lines and self.time >= TIME_BETWEEN_TEXT:
            self.best_score_text.visible = True
            self.stage += 1
            self.time = 0
        if self.stage == 6 + table_destruction_lines and self.time >= TIME_BETWEEN_TEXT:
            self.time_text.visible = True
            self.stage += 1
            self.time = 0
        if self.stage == 7 + table_destruction_lines and self.time >= TIME_BETWEEN_TEXT:
            self.best_time_text.visible = True
            self.stage += 1
            self.time = 0
        if self.stage == 8 + table_destruction_lines and self.time >= TIME_BETWEEN_TEXT:
            self.messages_visible = True
            self.stage += 1
            self.time = 0
        if self.stage == 9 + table_destruction_lines and self.time >= TIME_BETWEEN_TEXT:
            self.rates_visible = True
            self.stage += 1
            self.time = 0
        if self.stage == 10 + table_destruction_lines and self.time >= TIME_TO_LAST_TEXT_STAGE:
            self.ui_manager.children[0][0].children[0].disabled = False
            self.ui_manager.children[0][0].children[1].disabled = False
            self.ui_manager.children[0][0].children[2].disabled = False
            self.hint_text.text = "ESC — выйти"
            self.time = 0
            self.stage += 1

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if symbol == arcade.key.ESCAPE:
            self.window.close()

        # Для дебага
        # elif symbol == arcade.key.R:
        #     self.window.show_view(End(0, 0, 0, 0, 0, "00:00", 0, 0, 0, 0))

        elif symbol == arcade.key.SPACE:
            for i in range(4):
                self.table_drons_contents[i * 2].visible = True
                self.table_drons_contents[i * 2 + 1].visible = True
            for i in range(len(self.table_destruction_contents) - 1):
                self.table_destruction_contents[i][0].visible = True
                self.table_destruction_contents[i][1].visible = True
                self.table_destruction_contents[i][2].visible = True
            self.total_price = self.price_rockets + self.price_pvo + self.price_refinery + self.price_tanks
            self.table_destruction_contents[-1][1].text = f'{self.total_price:_}'.replace('_', ' ')
            self.score_text.visible = True
            self.best_score_text.visible = True
            self.time_text.visible = True
            self.best_time_text.visible = True
            self.messages_visible = True
            self.rates_visible = True
            self.ui_manager.children[0][0].children[0].disabled = False
            self.ui_manager.children[0][0].children[1].disabled = False
            self.ui_manager.children[0][0].children[2].disabled = False
            self.hint_text.text = "ESC — выйти"
            self.stage = 100

        elif symbol == arcade.key.S:
            screenshot()

    def append_messages_list(self, num_strikes: int, num_missed_drons: int) -> None:
        w = self.window.width
        h = self.window.height

        sobyanin_message_endings = ('Принимаются меры к ликвидации последствий.',
                                    'На месте падения обломков работают специалисты экстренных служб.',
                                    'Экстренные службы работают на месте падения обломков.',
                                    'Специалисты экстренных служб работают на месте падения обломков.')
        try:
            drons = randint(1, num_strikes)
        except ValueError:
            drons = 0
        messages_texts = (f'{drons} БПЛА, летевших на Москву, уничтожены системой ПВО Минобороны. ',
                          f'Сбиты {drons} беспилотников, летевших на Москву. ',
                          f'{drons} БПЛА уничтожены системой ПВО Минобороны. ',
                          f'Системой ПВО Минобороны уничтожены {drons} БПЛА, летевших на Москву. ',
                          f'Атака {drons} БПЛА отражена силами ПВО Минобороны. ')

        sobyanin_end = (f'В общей сложности на подлёте к Москве сбито около {num_strikes} беспилотников. '
                        f'Работа ПВО продолжается.',
                        f'Пожар, возникший в результате попадания БПЛА в МНПЗ, в основном локализован, '
                        f'производится тушение оставшегося очага. На заводе пострадавших нет.')

        messages_sources = ['moya moskva', 'moskva 24', 'sobyanin', 'tass']
        shuffle(messages_sources)
        messages_sources.append('end')

        lowest_bottom = 0
        time = randint(360, 570)
        for source in messages_sources:
            m = False
            comments = False
            delta = randint(3, 15)
            if source == 'moya moskva':
                if num_strikes > 10:
                    message_idx = randint(0, 2)
                else:
                    message_idx = randint(1, 2)
                m = True
                comments = True
            elif source == 'moskva 24':
                if num_strikes > 10:
                    message_idx = randint(0, 2)
                elif num_strikes > 0:
                    message_idx = randint(1, 2)
                else:
                    message_idx = 2
                m = True
                message = messages[f'{source} {message_idx}']
                message_width = 0.22 * message[1]
                message_height = w * 0.1455 * message[2]
                text_fields = message[3]
                if text_fields == 3:
                    third = randint(5, num_strikes - 6)
                    second = randint(5, num_strikes - third - 1)
                    first = num_strikes - third - second
                    drons_each = (first, second, third)
                if text_fields:
                    for text_field in range(text_fields):
                        if text_fields == 3:
                            dron = drons_each[text_field]
                        else:
                            dron = drons
                        self.messages_texts.append(
                            arcade.Text(f'{dron}', x=w * 0.005 + w * message_width * message[4 + text_field][0],
                                        y=h * 0.895 - lowest_bottom - message_height * message[4 + text_field][1],
                                        font_name='OpenSans-Regular', font_size=8.4*self.r, anchor_x='left', anchor_y='top',
                                        batch=self.messages_batch
                                        )
                    )
            elif source == 'tass':
                if num_strikes > 5:
                    message_idx = randint(1, 2)
                    if num_missed_drons > 0:
                        message_idx = randint(0, 2)
                    m = True
                elif num_strikes > 0:
                    message_idx = 1
                    if num_missed_drons > 0:
                        message_idx = randint(0, 1)
                    m = True
                if num_strikes > 0:
                    message = messages[f'{source} {message_idx}']
                    message_width = 0.22 * message[1]
                    message_height = w * 0.1455 * message[2]
                    text_field = message[3]
                    if text_field:
                        self.messages_texts.append(
                            arcade.Text(f'{drons}', x=w * 0.005 + w * message_width * message[4][0],
                                        y=h * 0.895 - lowest_bottom - message_height * message[4][1],
                                        font_name='OpenSans-Regular', font_size=8.4*self.r, anchor_x='left', anchor_y='top',
                                        batch=self.messages_batch
                                        )
                        )

            elif source == 'sobyanin':
                if num_strikes > 0:
                    m = True
                    self.messages_texts.append(
                        arcade.Text(messages_texts[randint(0, len(messages_texts) - 1)] +
                                    sobyanin_message_endings[round(triangular(0, 3, 4))],
                                x=w * 0.0135, y=h * 0.8722 - lowest_bottom, font_name='OpenSans-Regular',
                                font_size=8.4*self.r, anchor_x='left', anchor_y='top',
                                width=w * 0.21 * (0.96 - 0.01), multiline=True, batch=self.messages_batch
                                )
                    )
                message_idx = 'template'
            elif source == 'end':
                m = True
                source = 'sobyanin'
                message_idx = 'template'
                if num_strikes > 0:
                    idx = randint(0,1)
                else:
                    idx = 1
                self.messages_texts.append(
                    arcade.Text(sobyanin_end[idx],
                                x=w * 0.0135, y=h * 0.8722 - lowest_bottom, font_name='OpenSans-Regular',
                                font_size=8.4*self.r, anchor_x='left', anchor_y='top',
                                width=w * 0.21 * (0.96 - 0.01), multiline=True, batch=self.messages_batch
                                )
                )
                delta = randint(20, 35)
            if m:
                message = messages[f'{source} {message_idx}']
                message_texture = message[0]
                message_width = 0.22 * message[1]
                message_height = w * 0.1455 * message[2]
                message_rect = arcade.LRBT(w * 0.005, w * (0.005 + message_width), h * 0.895 - message_height - lowest_bottom,
                                           h * 0.895 - lowest_bottom)
                self.messages_list.append((message_texture, message_rect))
                views = randint(0, 9)
                time += delta
                hours = time // 60
                minutes = time % 60
                data_text = arcade.Text(
                    f'{views}   {'0' if hours < 10 else ''}{hours}:{'0' if minutes < 10 else ''}{minutes}',
                    x=w * (0.005 + message_width - 0.03), y=h * 0.906 - message_height - lowest_bottom,
                    font_size=8.4*self.r, font_name='OpenSans-Regular', color=(131, 142, 147),
                    anchor_x='left', anchor_y='center', batch=self.messages_batch)
                if comments:
                    data_text.y = h * 0.942 - message_height - lowest_bottom
                self.messages_data_list.append(data_text)
                lowest_bottom += message_height + h * 0.005
