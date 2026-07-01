import arcade
from views import Menu

window = arcade.Window(1920, 1080, 'Российское ПВО v1.0.0', resizable=True, fullscreen=True)
window.activate()
window.show_view(Menu())
arcade.run()
