from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Ellipse, Line, Canvas
from kivy.uix.stencilview import StencilView
from SecondaryMenu import SecondaryMenu

from ImageCanvas import ImageCanvas

class ImageGeneratorMain(Widget):
    def __init__(self, **kwargs):
        super(ImageGeneratorMain, self).__init__(**kwargs)
        self.image_canvas = self.ids["ImageCanvas"]
        self.image_canvas.secondary_menu = self.ids["SecondaryMenu"]
        self.image_canvas.secondary_menu.img_canvas = self.image_canvas
        self.config_manager = self.image_canvas.config_manager


    # clear the current canvas
    def canvas_options(self):
        self.image_canvas.secondary_menu.change_mode("canvas_settings", self.config_manager)

    # import an image to the canvas
    def import_image(self):
        self.image_canvas.load_image("textures/test_img.png")
        
    # export the current canvas
    def export_image(self):
        self.image_canvas.save_image("output.png")

    # enable the eraser
    def select_eraser(self):
        self.image_canvas.edit_mode = "eraser"

    # enable the pen
    def select_pen(self):
        self.image_canvas.edit_mode = "pen"

    # enable Ai autofill
    def select_stable_diffusion(self):
        self.image_canvas.secondary_menu.change_mode("stable_diffusion", self.config_manager)
        self.image_canvas.edit_mode = "generator"
        self.image_canvas.ai_mode = "stable"

    # run the AI on the basic art you have drawn
    def select_latant_diffusion(self):
        self.image_canvas.edit_mode = "generator"
        self.image_canvas.ai_mode = "latent"

class ImageGeneratorApp(App):
    def build(self):
        return ImageGeneratorMain()    


if __name__ == "__main__":
    ImageGeneratorApp().run()
