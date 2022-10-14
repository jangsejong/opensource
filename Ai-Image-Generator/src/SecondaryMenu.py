# A secondary menu for the main menu that shows up when the user clicks on an item in the main menu
 
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput

class SecondaryMenu(BoxLayout):
    def __init__(self, **kwargs):
        super(SecondaryMenu, self).__init__(**kwargs)
        self.orientation = "vertical"

        self.config_manager = None
        self.img_canvas = None


    def change_mode(self, mode, config_manager):
        self.config_manager = config_manager
        if mode == "stable_diffusion":
            self.clear_widgets()
            self.add_widget(Label(text=f"Guidance Scale"))
            self.add_widget(Slider(min=0, max=10, step=0.1, value=config_manager.get_value("guidance_scale"), on_touch_move=self.touch_move_gscale))
            self.add_widget(Label(text="Num Inference Steps"))
            self.add_widget(Slider(min=0, max=100, step=1, value=config_manager.get_value("num_inference_steps"), on_touch_move=self.touch_move_nisteps))
            self.add_widget(Label(text="Strength"))
            self.add_widget(Slider(min=0, max=1, step=0.01, value=config_manager.get_value("strength"), on_touch_move=self.touch_move_strength))

        elif mode == "eraser":
            self.clear_widgets()
            self.add_widget(Label(text="Eraser Size"))
            self.add_widget(Slider(min=0, max=100, step=1, value=20, on_touch_move=self.touch_move_eraser_size))

        elif mode == "brush":
            self.clear_widgets()
            self.add_widget(Label(text="Brush Size"))
            self.add_widget(Slider(min=0, max=100, step=1, value=20, on_touch_move=self.touch_move_eraser_size))

        elif mode == "none":
            self.clear_widgets()

    # update the config file when anything is changed
    def touch_move_gscale(self, instance, touch):
        self.config_manager.set_value("guidance_scale", instance.value)
        self.img_canvas.update_settings()

    def touch_move_nisteps(self, instance, touch):
        self.config_manager.set_value("num_inference_steps", instance.value)
        self.img_canvas.update_settings()

    def touch_move_strength(self, instance, touch):
        self.config_manager.set_value("strength", instance.value)
        self.img_canvas.update_settings()

    def reload_canvas(self, instance):
        size = [self.children[1].text, self.children[0].text]
        if int(size[0]) < 512:
            size[0] = "512"
            self.children[1].text = "512"
        if int(size[1]) < 512:
            size[1] = "512"
            self.children[0].text = "512"
        
        self.config_manager.set_value("canvas_size", (int(size[0]), int(size[1])))
        self.img_canvas.init_canvas_array()

    def touch_move_eraser_size(self, instance, touch):
        self.img_canvas.eraser_size = instance.value
