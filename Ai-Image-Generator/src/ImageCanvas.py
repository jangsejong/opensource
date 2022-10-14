from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics.texture import Texture
from kivy.core.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from PIL import Image as Pimage
from array import array
from random import randint
from threading import Thread
from ImgGenerator import StableDiffusion
from SecondaryMenu import SecondaryMenu
from ConfigManager import ConfigManager

# class that handles modifying the canvas with the varies methods this program offers
class ImageCanvas(BoxLayout):
    # less than this number the cord is not over the canvas
    CANVAS_BOUND_X = 175
    # send objects to this cord to hide
    UNRENDER = (-8000, -8000)
    # default sizes
    BACKGROUND_SIZE = (10000, 10000)
    GENERATOR_SIZE = (512, 512)
    BRUSH_SIZE = (20, 20)

    def __init__(self, **kwargs):
        super(ImageCanvas, self).__init__(**kwargs)
        
        # get mouse and keyboard input
        Window.bind(mouse_pos=self.mouse_pos)
        Window.size = (1000, 800)
        Window.bind(on_resize=self.on_resize)

        self.config_manager = ConfigManager()

        self.edit_mode = "none"
        self.state = "none"
        self.ai_mode = "none"

        # create the texture that will store the image
        self.canvas_size = self.config_manager.get_value("canvas_size")
        self.arr_size = self.canvas_size[0] * self.canvas_size[1] * 4
        self.img_texture = Texture.create(size=self.canvas_size, colorfmt="rgba")
        self.mask_texture = Texture.create(size=self.canvas_size, colorfmt="rgba")

        # create the array that will store the image and a array to store erased pixles
        self.img_arr = None
        self.mask_arr = None

        # begin loading the AI model 
        self.generator = StableDiffusion(self.config_manager)

        # init any objects that will be needed later
        with self.canvas:
            self.background = Rectangle(pos=(-5000, -5000), size=ImageCanvas.BACKGROUND_SIZE, source="textures/background.png")
            self.image_rect = Rectangle(texture=self.img_texture, pos=(175, 0), size=self.canvas_size)
            self.generator_rect = Rectangle(pos=ImageCanvas.UNRENDER, size=ImageCanvas.GENERATOR_SIZE, source="textures/selector_box.png")
            self.progress_rect = Rectangle(pos=ImageCanvas.UNRENDER, size=ImageCanvas.GENERATOR_SIZE, source="textures/progress_box.png")
            self.brush_head = Ellipse(pos=ImageCanvas.UNRENDER, size=ImageCanvas.BRUSH_SIZE)

            # make a text box for getting prompts #TODO make this its own class with more options
            self.text_input = TextInput(unfocus_on_touch=False, multiline=False, pos=(180, 10), size=(Window.size[0] - 175 - 10, 40), background_color=(0.9, 0.9, 1, 0.5))
            self.text_input.bind(on_text_validate=self.request_img_gen)
            self.text_input.bind(focus=self.on_focus)

        # get the canvas ready
        self.init_canvas_array()

        # blit image texture
        self.update_img()

        # schedule a update to the texture anytime there is a change
        self.img_texture.add_reload_observer(self.update_img)

        # schedule a regular update (example)
        Clock.schedule_interval(self.check_update, 0.1)

    # update the texture
    def update_img(self):
        self.img_texture.blit_buffer(self.img_arr, colorfmt="rgba", bufferfmt="ubyte")
        self.image_rect.texture = self.img_texture

    # check if the image should be re-blit 
    def check_update(self, dt):
        if self.generator.has_img == True:
            img, pos = self.generator.get_img()
            self.blit_segment_to_canvas(img, pos)
            # TODO change some modes after this as well if needed
        self.update_img()


    # check if the config has new data and update the canvas if needed
    def update_settings(self):
        self.generator.update_settings(self.config_manager)
        self.config_manager.save_config()

    # when the mouse is clicked on this widget
    def on_touch_down(self, touch):
        touch.ud["lastx"], touch.ud["lasty"] = touch.x, touch.y 
        self.handle_zoom(touch)
        self.handle_click(touch)

    def on_focus(self, instance, value):
        if value:
            self.state = "generating" # lock the generator rect in place
        else:
            self.state = "none"

    # when the mouse is being moved and clicked
    # controlling the position and drawing is handled here
    def on_touch_move(self, touch):
        if touch.ud.get("lastx") is None:
            touch.ud["lastx"], touch.ud["lasty"] = touch.x, touch.y
        image_pos = self.image_rect.pos
        mouse_dif = (image_pos[0] - (touch.ud["lastx"] - touch.x), image_pos[1] - (touch.ud["lasty"] - touch.y))
        mouse_dif_background = self.background.pos[0] - (touch.ud["lastx"] - touch.x), self.background.pos[1] - (touch.ud["lasty"] - touch.y)
        mouse_dif_progress = self.progress_rect.pos[0] - (touch.ud["lastx"] - touch.x), self.progress_rect.pos[1] - (touch.ud["lasty"] - touch.y)
        mouse_dif_generator = self.generator_rect.pos[0] - (touch.ud["lastx"] - touch.x), self.generator_rect.pos[1] - (touch.ud["lasty"] - touch.y)

        touch.ud["lastx"], touch.ud["lasty"] = touch.x, touch.y
        
        # if right click is down drag the image
        if touch.button == "right":
            self.image_rect.pos = mouse_dif
            self.background.pos = mouse_dif_background
            self.progress_rect.pos = mouse_dif_progress
            self.generator_rect.pos = mouse_dif_generator

        if touch.button == "left":
            self.handle_drag()

    # called every time there is a mouse position change
    def mouse_pos(self, window, pos):
        # if in generator mode move the selection box with the mouse
        if self.edit_mode == "generator" and pos[0] > ImageCanvas.CANVAS_BOUND_X and self.state != "generating":
            self.generator_rect.pos = min((self.image_rect.pos[0] + self.image_rect.size[0]) - self.generator_rect.size[0], max(self.image_rect.pos[0], pos[0] - self.generator_rect.size[0] / 2)),\
                                      min((self.image_rect.pos[1] + self.image_rect.size[1]) - self.generator_rect.size[1], max(self.image_rect.pos[1], pos[1] - self.generator_rect.size[1] / 2))
        elif self.state != "generating":
            self.generator_rect.pos = ImageCanvas.UNRENDER
        elif self.edit_mode != "generator":
            self.generator_rect.pos = ImageCanvas.UNRENDER

        
        # if in pen or eraser mode bring the brush to the mouse position
        if self.edit_mode == "pen" or self.edit_mode == "eraser":
            self.brush_head.pos = pos[0] - self.brush_head.size[0] / 2, pos[1] - self.brush_head.size[1] / 2
        else:
            self.brush_head.pos = ImageCanvas.UNRENDER

    # denpending on the mode we are in handle a click
    def handle_click(self, touch):
        if self.edit_mode == "pen":
            pass
        elif self.edit_mode == "eraser":
            pass
        elif self.edit_mode == "generator":
            if self.ai_mode == "stable" and touch.button == "left":
                # select the text prompt
                if (self.text_input.focus == True):
                    self.text_input.focus = False
                else:
                    self.text_input.focus = True

    # denpending on the mode we are in handle a drag
    def handle_drag(self):
        if self.edit_mode == "pen":
            pass
        elif self.edit_mode == "eraser":
            pass
        pass

    # handle zooming the image
    def handle_zoom(self, touch):
        # only zoom if the mouse is over the canvas
        if (touch.x > ImageCanvas.CANVAS_BOUND_X):
            # adjust the size but also the position so it zooms on the mouse
            start_pos_img_rect = self.image_rect.pos
            start_size_img_rect = self.image_rect.size
            if touch.button == "scrolldown":
                self.image_rect.size = self.image_rect.size[0] * 1.05, self.image_rect.size[1] * 1.05
                self.generator_rect.size = self.generator_rect.size[0] * 1.05, self.generator_rect.size[1] * 1.05
                self.progress_rect.size = self.progress_rect.size[0] * 1.05, self.progress_rect.size[1] * 1.05
                self.brush_head.size = self.brush_head.size[0] * 1.05, self.brush_head.size[1] * 1.05
            elif touch.button == "scrollup":
                self.image_rect.size = self.image_rect.size[0] * 0.95, self.image_rect.size[1] * 0.95
                self.generator_rect.size = self.generator_rect.size[0] * 0.95, self.generator_rect.size[1] * 0.95
                self.progress_rect.size = self.progress_rect.size[0] * 0.95, self.progress_rect.size[1] * 0.95
                self.brush_head.size = self.brush_head.size[0] * 0.95, self.brush_head.size[1] * 0.95
            end_size = self.image_rect.size
            ratios = (touch.x - start_pos_img_rect[0]) / start_size_img_rect[0], (touch.y - start_pos_img_rect[1]) / start_size_img_rect[1]
            end_pos = -(ratios[0] * end_size[0]) + touch.x, -(ratios[1] * end_size[1]) + touch.y 
            self.image_rect.pos = end_pos

            # update the generator box position, the pen position and the progress rect
            if (self.edit_mode == "generator"):
                ratios = (self.generator_rect.pos[0] - start_pos_img_rect[0]) / start_size_img_rect[0], (self.generator_rect.pos[1] - start_pos_img_rect[1]) / start_size_img_rect[1]
                end_pos = (ratios[0] * end_size[0]) + self.image_rect.pos[0], (ratios[1] * end_size[1]) + self.image_rect.pos[1]
                self.generator_rect.pos = end_pos
            if (self.edit_mode == "pen" or self.edit_mode == "eraser"):
                self.brush_head.pos = touch.x - self.brush_head.size[0] / 2, touch.y - self.brush_head.size[1] / 2
            if (self.progress_rect.pos != ImageCanvas.UNRENDER):
                ratios = (self.progress_rect.pos[0] - start_pos_img_rect[0]) / start_size_img_rect[0], (self.progress_rect.pos[1] - start_pos_img_rect[1]) / start_size_img_rect[1]
                end_pos = (ratios[0] * end_size[0]) + self.image_rect.pos[0], (ratios[1] * end_size[1]) + self.image_rect.pos[1]
                self.progress_rect.pos = end_pos

    def on_resize(self, window, width, height):
        self.text_input.size = (self.size[0] - 175 - 10, 40)
            
    def save_image(self, name):
        self.img_texture.save(name)

    # TODO load this in to its own rectange and then once a pos is selected update the canvas with it
    def load_image(self, name):
        img = Image(name).texture
        # if the image is bigger than the canvas resize the canvas
        self.image_rect.size = img.size[0], img.size[1]
        self.canvas_size = img.size
        self.arr_size = img.size[0] * img.size[1] * 4

        self.img_texture = Texture.create(size=img.size, colorfmt="rgba")

        # flip the texture
        self.img_arr = self.flip_img_arr(img)

        # now reload the mask TODO make this default to 0
        self.mask_arr = array("B", [255] * (self.canvas_size[0] * self.canvas_size[1] * 4))
        self.update_img()
        self.reset_sizes()

    # start generating a image based on the prompt in the input box and location of the 
    # generator rect
    def request_img_gen(self, prompt):
        # check if the model is loaded and ready
        if (self.generator.ready == False):
            print("Model not loaded...")
            return

        # move the progress rect to the location
        self.progress_rect.pos = self.generator_rect.pos
        
        # get the pixles of the image that is the top left of the progress rect
        # and the size of the progress rect (if outside of the image snap to the edge)
        x = self.progress_rect.pos[0] - self.image_rect.pos[0]
        x = min(self.image_rect.size[0], max(0, x))
        x = int(x / self.image_rect.size[0] * self.img_texture.size[0])
        y = self.progress_rect.pos[1] - self.image_rect.pos[1]
        y = min(self.image_rect.size[1], max(0, y))
        y = int(y / self.image_rect.size[1] * self.img_texture.size[1])

        # get the img array
        mask_arr = self.flip_arr(self.get_generator_block_mask((x, y)))
        img_arr = self.flip_arr(self.get_generator_block((x, y)))

        # make the PIL image
        pil_mask = Pimage.frombuffer("RGBA", ImageCanvas.GENERATOR_SIZE, mask_arr).convert("RGB")
        pil_image = Pimage.frombuffer("RGBA", ImageCanvas.GENERATOR_SIZE, img_arr).convert("RGB")

        # start the image generation
        img_thread = Thread(target=self.generator.generate_image, args=(prompt.text, (x, y), pil_mask, pil_image))
        img_thread.start()
        
    def init_canvas_array(self):
        self.canvas_size = self.config_manager.get_value("canvas_size")
        self.image_rect.size = self.canvas_size
        self.arr_size = self.canvas_size[0] * self.canvas_size[1] * 4

        self.mask_arr = array("B", [255] * (self.canvas_size[0] * self.canvas_size[1] * 4))
        self.img_arr = array("B", [150] * (self.canvas_size[0] * self.canvas_size[1] * 4))
        self.img_texture = Texture.create(size=self.canvas_size, colorfmt="rgba")
        self.mask_texture = Texture.create(size=self.canvas_size, colorfmt="rgba")
        self.img_texture.blit_buffer(self.img_arr, colorfmt="rgba", bufferfmt="ubyte")
        self.mask_texture.blit_buffer(self.mask_arr, colorfmt="rgba", bufferfmt="ubyte")
        self.image_rect.texture = self.img_texture
        self.update_img()
        self.reset_sizes()
        
    def reset_sizes(self):
        self.generator_rect.size = ImageCanvas.GENERATOR_SIZE
        self.brush_head.size = ImageCanvas.BRUSH_SIZE
        self.progress_rect.size = ImageCanvas.GENERATOR_SIZE

    # blit the generated segment to the canvas
    def blit_segment_to_canvas(self, img_arr, pos):
        # flip the image
        img_arr = self.flip_arr(img_arr)

        # update the image array with this data
        self.add_generator_output(img_arr, pos)

        # once this is finished move the progress rect to the location
        self.progress_rect.pos = ImageCanvas.UNRENDER

        # put focus back on the input box
        self.text_input.focus = True


    # take a texture and flip it then return it as an array
    def flip_img_arr(self, img):
        # flip the texture
        img = img.pixels[::-1]
        # turn img_texture into a array
        arr = array("B", img)
        #reverse the rows in chunks of 4
        for i in range(self.canvas_size[1]):
            arr[i * self.canvas_size[0] * 4 : (i + 1) * self.canvas_size[0] * 4] = arr[i * self.canvas_size[0] * 4 : (i + 1) * self.canvas_size[0] * 4][::-1]
        return arr

    # flips a image array of size (ImgCanvas.GENERATOR_SIZE) and returns it
    def flip_arr(self, arr):
        # to flip the columbs flip the rows and then flip the whole thing
        for i in range(ImageCanvas.GENERATOR_SIZE[1]):
            arr[i * ImageCanvas.GENERATOR_SIZE[0] * 4 : (i + 1) * ImageCanvas.GENERATOR_SIZE[0] * 4] = arr[i * ImageCanvas.GENERATOR_SIZE[0] * 4 : (i + 1) * ImageCanvas.GENERATOR_SIZE[0] * 4][::-1]
        return arr[::-1]

    # adds the output to the image array and updates the mask array
    def add_generator_output(self, img_arr, pos):
        starting_index = (pos[0] * 4) + (pos[1] * self.canvas_size[0] * 4)

        for i in range(ImageCanvas.GENERATOR_SIZE[1]):
            # calculate the index offset
            index_offset_canvas = starting_index + (self.canvas_size[0] * 4 * i)
            index_offset_img = ImageCanvas.GENERATOR_SIZE[0] * 4 * i
            for j in range(ImageCanvas.GENERATOR_SIZE[0]):
                # calculate the index
                index_canvas = index_offset_canvas + (j * 4)
                index_img = index_offset_img + (j * 4)

                # update the image array
                self.img_arr[index_canvas] = img_arr[index_img]
                self.img_arr[index_canvas + 1] = img_arr[index_img + 1]
                self.img_arr[index_canvas + 2] = img_arr[index_img + 2]
                self.img_arr[index_canvas + 3] = img_arr[index_img + 3]

                # update the mask array
                self.mask_arr[index_canvas] = 0
                self.mask_arr[index_canvas + 1] = 0
                self.mask_arr[index_canvas + 2] = 0
                self.mask_arr[index_canvas + 3] = 0

    # gets a portion of the image array and returns it
    def get_generator_block(self, pos):
        # return the portion of the image array
        starting_index = pos[0] * 4 + (pos[1] * self.canvas_size[0] * 4)
        arr = array("B", [0] * (ImageCanvas.GENERATOR_SIZE[0] * ImageCanvas.GENERATOR_SIZE[1] * 4))
        for i in range(ImageCanvas.GENERATOR_SIZE[1]):
            # calculate the index offset
            index_offset_canvas = starting_index + (self.canvas_size[0] * 4 * i)
            index_offset_img = ImageCanvas.GENERATOR_SIZE[0] * 4 * i
            for j in range(ImageCanvas.GENERATOR_SIZE[0]):
                # calculate the index
                index_canvas = index_offset_canvas + (j * 4)
                index_img = index_offset_img + (j * 4)

                # update the image array
                arr[index_img] = self.img_arr[index_canvas]
                arr[index_img + 1] = self.img_arr[index_canvas + 1]
                arr[index_img + 2] = self.img_arr[index_canvas + 2]
                arr[index_img + 3] = self.img_arr[index_canvas + 3]
        return arr

    def get_generator_block_mask(self, pos):
        # return the portion of the image array
        starting_index = pos[0] * 4 + (pos[1] * self.canvas_size[0] * 4)
        arr = array("B", [0] * (ImageCanvas.GENERATOR_SIZE[0] * ImageCanvas.GENERATOR_SIZE[1] * 4))
        for i in range(ImageCanvas.GENERATOR_SIZE[1]):
            # calculate the index offset
            index_offset_canvas = starting_index + (self.canvas_size[0] * 4 * i)
            index_offset_img = ImageCanvas.GENERATOR_SIZE[0] * 4 * i
            for j in range(ImageCanvas.GENERATOR_SIZE[0]):
                # calculate the index
                index_canvas = index_offset_canvas + (j * 4)
                index_img = index_offset_img + (j * 4)

                # update the image array
                arr[index_img] = self.mask_arr[index_canvas]
                arr[index_img + 1] = self.mask_arr[index_canvas + 1]
                arr[index_img + 2] = self.mask_arr[index_canvas + 2]
                arr[index_img + 3] = self.mask_arr[index_canvas + 3]
        return arr
