import arcade
from views import Menu, End

window = arcade.Window(1920, 1080, 'Российское ПВО v1.0.0', resizable=True, fullscreen=True)
window.activate()
window.show_view(Menu())
# Для дебага
# window.show_view(End(0, 0, 100, 5, 0, "00:00", 0, 0, 0, 0))
arcade.run()
