import arcade
from math import cos, sin, radians, degrees, atan2
from random import uniform, random
from constants import SOUND_VOLUME, REFINERY_DRON_DAMAGE, REFINERY_OBLOMOK_DAMAGE, REFINERY_ROCKET_DAMAGE, \
    TANK_DRON_DAMAGE, TANK_OBLOMOK_DAMAGE, PVO_DRON_DAMAGE, PVO_OBLOMOK_DAMAGE, PVO_ROCKET_DAMAGE

print("Загрузка звуков.")
launch_sound = arcade.load_sound('sounds/launch.mp3')
bom_sound = arcade.load_sound('sounds/boom short.mp3')
print("Готово.\n")

print("Загрузка текстур (1/2).")
bom_gif = arcade.load_animated_gif('gifs/bom transparent 1.gif')
smoke_texture = arcade.load_texture('textures/smoke.png')

dron_texture_right = arcade.load_texture('textures/dron/dron.png')
dron_texture_left = dron_texture_right.flip_left_right()
oblomok_texture = arcade.load_texture('textures/dron/oblomok.png')

tank_texture = arcade.load_texture('textures/tank/tank.png')
lid_texture = arcade.load_texture('textures/tank/lid.png')
refinery_texture = arcade.load_texture('textures/refinery/refinery.png')

rocket_texture = arcade.load_texture('textures/pvo/rocket.png')
pvo_tower_texture = arcade.load_texture('textures/pvo/tower.png')
pvo_texture = arcade.load_texture('textures/pvo/pvo.png')
print("Готово.\n")

class WhiteSmoke(arcade.Sprite):
    scale_max = 0.15
    expansion_rate = 0.1

    change_x = 0
    change_y = 0

    def __init__(self, view, x: float, y: float):
        super().__init__()
        self.texture = smoke_texture
        self.center_x = x
        self.center_y = y

        self.r = view.r
        self.scale = 0.0375 * self.r
        self.scale_max *= self.r
        self.change_x *= self.r
        self.change_y *= self.r

    def update(self, delta_time: float = 1 / 60, *args, **kwargs):
        self.scale_x += self.expansion_rate * self.r * delta_time
        self.scale_y += self.expansion_rate * self.r * delta_time

        self.center_y += self.change_y * delta_time
        self.center_x += self.change_x * delta_time

        alpha = max(127 - (self.scale_x - 0.0375) * 127 / (self.scale_max - 0.0375), 0)
        self.update_color_alpha(int(alpha))

        if self.scale_x >= self.scale_max:
            self.kill()

    def update_color_alpha(self, alpha: int):
        self.alpha = alpha

class BlackSmoke(WhiteSmoke):
    def __init__(self, view, x: float, y: float):
        super().__init__(view, x, y)

    def update_color_alpha(self, alpha: int):
        self.color = (0, 0, 0, alpha)

class FireWhiteSmoke(WhiteSmoke):
    def __init__(self, view, x: float, y: float):
        super().__init__(view, x, y)

    def update_color_alpha(self, alpha: int):
        if self.scale_x <= 0.056:
            self.color = (255, max(64 - 64 * (self.scale_x - 0.0375) / 0.0185, 0), 0, alpha)
        else:
            green = blue = min(255 * (self.scale_x - 0.056) / 0.05, 255)
            self.color = (255, green, blue, alpha)

class FireBlackSmoke(WhiteSmoke):
    scale_max = 0.375
    expansion_rate = 0.05

    change_y = 75
    change_x = -15

    def __init__(self, view, x: float, y: float):
        super().__init__(view, x, y)
        self.scale = 0.15 * self.r

    def update_color_alpha(self, alpha: int):
        alpha = max(127 - 127 * (self.scale_x - 0.15) / (self.scale_max - 0.15), 0)
        if self.scale_x <= 0.2:
            self.color = (255, max(64 - 64 * (self.scale_x - 0.15) / 0.05, 0), 0, alpha)
        else:
            self.color = (max(255 - 255 * (self.scale_x - 0.2) / 0.1, 0), 0, 0, alpha)

class Explosive(arcade.Sprite):
    exploding = False
    explosion = None
    explosion_time = 0
    explosion_list = None
    explosion_scale = 0.375

    smoke_type = None
    time_between_smoke = 0.5

    view = None

    time = 0

    health = 100

    def setup_explosion(self):
        self.explosion_list = arcade.SpriteList()
        self.explosion: arcade.TextureAnimationSprite = arcade.TextureAnimationSprite()
        self.explosion.animation = bom_gif.animation
        self.explosion.scale = self.explosion_scale
        self.explosion.visible = False
        self.explosion_list.append(self.explosion)

    def explode(self):
        self.exploding = True
        self.visible = False
        self.explosion.center_x = self.center_x
        self.explosion.center_y = self.center_y
        self.explosion.visible = True
        self.view.explosions_list.append(self.explosion)
        arcade.play_sound(bom_sound, SOUND_VOLUME)
        self.explosion1()

    def explosion1(self):
        pass

    def append_to_collision_list(self):
        pass

    def check_collision(self) -> None:
        pass

    def check_health(self) -> None:
        pass

    def create_smoke(self) -> None:
        pass

    def update(self, delta_time: float = 1 / 60, *args, **kwargs):
        self.time += delta_time

        if self.time >= self.time_between_smoke and self.smoke_type:
            self.time = 0
            self.create_smoke()

        if not self.exploding:
            self.check_collision()
            self.check_health()
        if self.exploding:
            self.explosion_list.update_animation(delta_time)
            self.explosion_time += delta_time
        if self.explosion_time >= self.explosion.animation.duration_seconds:
            self.explosion.visible = False
            self.view.explosions_list.remove(self.explosion)
            self.kill()

class Refinery(Explosive):
    explosion_scale = 1.5

    smoke_type = FireBlackSmoke

    def __init__(self, view, x: float, y: float):
        super().__init__()
        self.texture = refinery_texture
        self.center_x = x
        self.center_y = y
        self.scale = 0.75 * view.r

        self.view = view
        self.explosion_scale *= view.r
        self.setup_explosion()

    def check_collision(self) -> None:
        if arcade.check_for_collision_with_list(self, self.view.rocket_collision_list):
            self.health -= REFINERY_ROCKET_DAMAGE
            self.view.num_industry_strikes += 1
        if arcade.check_for_collision_with_list(self, self.view.dron_collision_list):
            self.health -= REFINERY_DRON_DAMAGE
            self.view.num_missed_drons += 1
        if arcade.check_for_collision_with_list(self, self.view.oblomki_collision_list):
            self.health -= REFINERY_OBLOMOK_DAMAGE

    def check_health(self) -> None:
        self.view.refinery_health = min(max(self.health, 0), 100)
        if self.health <= 0:
            self.explode()

    def create_smoke(self) -> None:
        r = self.view.r
        if self.health <= 60:
            self.view.smoke_list.append(self.smoke_type(self.view, self.center_x, self.center_y))
        if self.health <= 40:
            self.view.smoke_list.append(self.smoke_type(self.view,self.center_x - 140*r, self.center_y + 30*r))
        if self.health <= 20:
            self.view.smoke_list.append(self.smoke_type(self.view,self.center_x + 200*r, self.center_y - 50*r))

class Lid(Explosive):
    def __init__(self, view, x: float, y: float):
        super().__init__()
        self.texture = lid_texture
        self.center_x = x
        self.center_y = y
        self.change_x = 15
        self.change_y = 225

        self.scale = 0.75 * view.r
        self.explosion_scale *= view.r
        self.view = view
        self.setup_explosion()

    def update(self, delta_time: float = 1 / 60, *args, **kwargs):
        if not self.exploding:
            self.change_y -= 112.5 * delta_time

            self.center_x += self.change_x * delta_time
            self.center_y += self.change_y * delta_time
            self.turn_right(22.5 * delta_time)

            if self.center_y <= self.view.window.height * 0.22:
                self.explode()

        if self.exploding:
            self.explosion_list.update_animation(delta_time)
            self.explosion_time += delta_time
        if self.explosion_time >= self.explosion.animation.duration_seconds:
            self.explosion.visible = False
            self.view.explosions_list.remove(self.explosion)
            self.kill()

class Tank(Explosive):
    explosion_scale = 0.75
    smoke_type = FireBlackSmoke

    def __init__(self, view, x: float, y: float):
        super().__init__()
        self.texture = tank_texture
        self.center_x = x
        self.center_y = y
        self.scale = 0.3 * view.r
        self.explosion_scale *= view.r
        self.view = view
        self.setup_explosion()

    def launch_lid(self):
        self.view.misc_list.append(Lid(self.view, self.center_x, self.center_y))

    def check_collision(self) -> None:
        if arcade.check_for_collision_with_list(self, self.view.dron_collision_list):
            self.health -= TANK_DRON_DAMAGE
            self.view.num_missed_drons += 1
        if arcade.check_for_collision_with_list(self, self.view.oblomki_collision_list):
            self.health -= TANK_OBLOMOK_DAMAGE
        if arcade.check_for_collision_with_list(self, self.view.rocket_collision_list):
            self.launch_lid()
            self.view.num_industry_strikes += 1
            self.health -= 100

    def check_health(self) -> None:
        if abs(self.center_x - self.view.window.width * 0.5) <= self.view.window.width * 0.01:
            self.view.tank1_health = min(max(self.health, 0), 100)
        elif abs(self.center_x - self.view.window.width * 0.63) <= self.view.window.width * 0.01:
            self.view.tank2_health = min(max(self.health, 0), 100)
        if self.health <= 0:
            self.explode()

    def create_smoke(self) -> None:
        if self.health <= 99:
            self.view.smoke_list.append(self.smoke_type(self.view,self.center_x, self.center_y + 50 * self.view.r))

class PvoTower(arcade.Sprite):
    def __init__(self, view, x: float, y: float):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.texture = pvo_tower_texture
        self.scale_x = 0.55 * view.r
        self.scale_y = 0.39 * view.r

        self.view = view

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        oblomki = arcade.check_for_collision_with_list(self, self.view.dron_collision_list)
        if oblomki:
            for oblomok in oblomki:
                oblomok.explode()
            self.view.pvo_list[0].health -= PVO_DRON_DAMAGE
        drons = arcade.check_for_collision_with_list(self, self.view.oblomki_collision_list)
        if drons:
            for dron in drons:
                dron.explode()
            self.view.pvo_list[0].health -= PVO_OBLOMOK_DAMAGE
        rockets = arcade.check_for_collision_with_list(self, self.view.rocket_collision_list)
        if rockets:
            for rocket in rockets:
                rocket.explode()
            self.view.pvo_list[0].health -= PVO_ROCKET_DAMAGE

class Pvo(Explosive):
    def __init__(self, view, x: float, y: float):
        super().__init__()
        self.texture = pvo_texture
        self.center_x = x
        self.center_y = y
        self.scale = 0.218 * view.r
        self.explosion_scale *= view.r
        self.view = view
        self.setup_explosion()

    def check_collision(self) -> None:
        if arcade.check_for_collision_with_list(self, self.view.dron_collision_list):
            self.health -= PVO_DRON_DAMAGE
        if arcade.check_for_collision_with_list(self, self.view.oblomki_collision_list):
            self.health -= PVO_OBLOMOK_DAMAGE

    def check_health(self) -> None:
        self.view.pvo_health = min(max(self.health, 0), 100)
        if self.health <= 0:
            self.explode()

class Projectile(Explosive):
    collision = True
    rotation = 0
    speed = 675
    smoke_type = WhiteSmoke

    target: Refinery | Tank | Pvo = None
    path_to_target: list[tuple[float, float]] = None
    cur_target = 0

    time = 0

    turning_left = False
    turning_right = False
    turning_speed = 500

    def set_target(self, target: Refinery | Tank | Pvo) -> None:
        pass

    def follow_target(self, delta_time: float) -> None:
        pass

    def turn(self, delta_time):
        delta = delta_time * self.turning_speed
        self.rotation = (self.rotation + delta) % 360
        self.turn_right(delta)

    def remove_from_collision_lists(self) -> None:
        pass

    def miss(self) -> None:
        pass

    def update(self, delta_time: float = 1 / 60, *args, **kwargs):
        if not self.exploding:
            self.follow_target(delta_time)

            self.time += delta_time
            if self.turning_left:
                self.turn(-delta_time)
            elif self.turning_right:
                self.turn(delta_time)

            self.change_x = self.speed * sin(radians(self.rotation))
            self.change_y = self.speed * cos(radians(self.rotation))
            self.center_x += self.change_x * delta_time
            self.center_y += self.change_y * delta_time

            if self.time >= self.time_between_smoke:
                self.time = 0
                self.view.smoke_list.append(self.smoke_type(self.view, self.center_x, self.center_y))

            if self.center_y <= 200:
                self.miss()
                self.explode()
            elif self.right <= -200 or self.left >= self.view.window.width + 200 or self.bottom >= self.view.window.height + 200:
                self.miss()
                self.kill()

            self.check_collision()
            self.check_health()
        else:
            if self.collision:
                self.collision = False
                self.remove_from_collision_lists()
            self.explosion_list.update_animation(delta_time)
            self.explosion_time += delta_time
        if self.explosion_time >= self.explosion.animation.duration_seconds:
            self.explosion.visible = False
            self.view.explosions_list.remove(self.explosion)
            self.kill()

class PvoRocket(Projectile):
    smoke_type = FireWhiteSmoke
    speed = 800
    time_between_smoke = 0.0325

    def __init__(self, view, x: float, y: float, rot: float = 0):
        super().__init__()
        arcade.play_sound(launch_sound, SOUND_VOLUME)
        self.texture = rocket_texture
        self.scale = 0.225 * view.r
        self.turn_right(rot)

        self.center_x = x
        self.center_y = y
        self.rotation = rot

        self.explosion_scale *= view.r
        self.view = view
        self.setup_explosion()
        self.append_to_collision_list()

    def append_to_collision_list(self):
        self.view.rocket_collision_list.append(self)

    def remove_from_collision_lists(self) -> None:
        self.view.rocket_collision_list.remove(self)

    def miss(self):
        self.view.num_lost_rockets += 1

    def check_collision(self):
        strike = arcade.check_for_collision_with_lists(self, (self.view.dron_collision_list, self.view.industry_list))
        if strike:
            if type(strike[0]) == Dron and not strike[0].exploding:
                strike[0].explode()
                self.view.num_strikes += 1
            self.explode()

class Dron(Projectile):
    speed = 450
    time_between_smoke = 0.075

    def __init__(self, view, x: float, y: float, speed: float = None, rot: float = 270, texture=None):
        """
        ОБЯЗАТЕЛЬНО ПОСЛЕ ЭТОГО ВЫЗВАТЬ set_target !!!
        """
        super().__init__()
        if texture:
            self.texture = texture
        else:
            if 0 < rot < 180:
                self.texture = dron_texture_right
            else:
                self.texture = dron_texture_left
        self.scale = 0.188 * view.r

        self.center_x = x
        self.center_y = y
        self.rotation = rot
        self.turn_right(rot)

        self.path_to_target = []

        if speed:
            self.speed = speed

        self.explosion_scale *= view.r
        self.view = view
        self.setup_explosion()
        self.append_to_collision_list()

    def set_target(self, target: Refinery | Tank | Pvo):
        self.target = target
        # У каждого дрона есть цель, к которой он летит
        # Он виляет вверх-вниз, пока не достигнет по x цели
        # Путь состоит из нескольких точек, между соседними 100 пикселей по x
        for path_point in range(int((self.center_x - target.center_x) / 100)):
            point_x = self.center_x - 100 * (path_point + 1)
            # Если дрон рядом с ПВО, то он летит высоко
            if self.view.window.width * 0.3 <= point_x <= self.view.window.width * 0.55:
                point_y = uniform(self.view.window.height * 0.7, self.view.window.height * 0.9)
            # Если на подлёте к ПВО, он немного поднимается
            elif self.view.window.width * 0.55 <= point_x <= self.view.window.width * 0.65:
                point_y = uniform(self.view.window.height * 0.5, self.view.window.height * 0.9)
            else:
                point_y = uniform(self.view.window.height * 0.4, self.view.window.height * 0.9)
            self.path_to_target.append((point_x, point_y))

        self.path_to_target.append((target.center_x, target.center_y))

        # print(self.path_to_target)

    def follow_target(self, delta_time: float) -> None:
        # Для следования по пути до цели как бы симулируется управление мышью (как у ракеты)
        # Позиция мыши - координаты следующей точки на пути
        try:
            if not self.target.sprite_lists:
                new_target = self.view.give_new_target()
                if new_target:
                    self.set_target(new_target)
        except AttributeError:
            pass

        if not self.path_to_target:
            return

        if abs(self.center_x - self.path_to_target[min(self.cur_target, len(self.path_to_target) - 1)][0]) <= 30:
            self.cur_target += 1
            self.cur_target = min(self.cur_target, len(self.path_to_target) - 1)

        target_point = self.path_to_target[self.cur_target]

        if delta_time <= 0.02:
            new_rot = degrees(atan2(target_point[0] - self.center_x, target_point[1] - self.center_y))
            rot = self.rotation - int(self.rotation > 180) * 360
            delta = (new_rot - rot + 180) % 360 - 180
            # turning_speed = (1 - (sin(radians(delta - 180) / 2)) ** 10) * 500
            # rocket.turning_speed = turning_speed

            if -3 <= delta <= 3:
                self.turning_right = False
                self.turning_left = False
            elif delta > 0:
                self.turning_right = True
                self.turning_left = False
            elif delta < 0:
                self.turning_right = False
                self.turning_left = True

    def append_to_collision_list(self):
        self.view.dron_collision_list.append(self)

    def remove_from_collision_lists(self) -> None:
        self.view.dron_collision_list.remove(self)

    def explosion1(self):
        if random() > 0.5:
            self.view.dron_list.append(
                Oblomok(self.view, self.center_x, self.center_y, rot=uniform(160, 200), texture=oblomok_texture)
            )

    def turn(self, delta_time):
        last_rot = self.rotation
        delta = 300 * delta_time
        if self.rotation > 180 and self.turning_right or self.rotation < 180 and self.turning_left:
            delta *= (sin(radians(self.rotation) / 2)) ** 2

        self.rotation = (self.rotation + delta) % 360
        self.turn_right(delta)

        if last_rot > 180 and self.rotation <= 180:
            self.texture = dron_texture_right
        elif last_rot < 180 and self.rotation >= 180:
            self.texture = dron_texture_left

    def check_collision(self):
        if arcade.check_for_collision_with_lists(self, (self.view.pvo_list, self.view.industry_list)):
            self.explode()

class Oblomok(Dron):
    speed = 150
    smoke_type = BlackSmoke
    time_between_smoke = 0.173

    def explosion1(self):
        pass

    def append_to_collision_list(self):
        self.view.oblomki_collision_list.append(self)

    def remove_from_collision_lists(self) -> None:
        self.view.oblomki_collision_list.remove(self)

    def miss(self):
        pass

    def check_collision(self):
        if arcade.check_for_collision_with_lists(self, (self.view.pvo_list, self.view.industry_list)):
            self.explode()

    def turn(self, delta_time):
        delta = 300 * delta_time
        if self.rotation > 180 and self.turning_right or self.rotation < 180 and self.turning_left:
            delta *= (sin(radians((self.rotation - 120) * 1.5))) ** 2

        self.rotation = (self.rotation + delta) % 360
        self.turn_right(delta)
