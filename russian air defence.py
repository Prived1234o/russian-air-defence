import arcade
from constants import VERSION
from views import Menu, End

# оно resizable, т.к. иначе на Linux оно не отображается правильно
window = arcade.Window(1920, 1080, 'российское ПВО ' + VERSION, resizable=True, fullscreen=True)
window.activate()
window.show_view(Menu())
# Для дебага
# window.show_view(End(0, 0, 100, 5, 0, "00:00", 0, 0, 0, 0))
arcade.run()
