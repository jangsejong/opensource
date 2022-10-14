from kivy.core.image import Image
from torch import autocast
import torch
from diffusers import StableDiffusionInpaintPipeline, StableDiffusionPipeline
from io import BytesIO
from threading import Thread
import numpy as np
from array import array
import time

class StableDiffusion:
    def __init__(self, config_manager):
        # define some variables for the model
        self.guidance_scale = config_manager.get_value("guidance_scale")
        self.num_inference_steps = config_manager.get_value("num_inference_steps")
        self.strength = config_manager.get_value("strength")

        # state vars
        self.ready = False
        self.has_img = False
        
        # vars for holding input and output img
        self.output_img = None
        self.img_loc = None

        # load the model
        self.model_id = config_manager.get_value("model_id")
        self.device = config_manager.get_value("device")
        self.pipe = None
        # start the loading of the model in another thread
        print("Loading Model...")
        model_loader = Thread(target=self.load_model, args=())
        model_loader.start()

    def load_model(self, model_type="StableDiffusion"):
        # TODO allow switching between models
        self.ready = False

        start_time = time.time()
        self.pipe = StableDiffusionPipeline.from_pretrained(self.model_id,
                    torch_dtype=torch.float16,
                    revision="fp16",
                    use_auth_token=False)
        self.pipe = self.pipe.to(self.device)



        print("Model Loaded in " + str(round(time.time() - start_time, 4)) + "s")
        self.ready = True

    # generate images with the prompt supplied to the function
    def generate_image(self, prompt, image_loc, mask=None, init_img=None):
        # check if the model is ready
        if self.ready == False:
            return
        start_time = time.time()
        with autocast(self.device):
            image = self.pipe(prompt=prompt, init_image=init_img, mask_image=mask,
                    strength=self.strength,
                    num_inference_steps=int(self.num_inference_steps),
                    guidance_scale=self.guidance_scale)\
                    ["sample"][0]
        self.has_img = True
        self.img_loc = image_loc
        self.output_img = image
        print("Image Generated in: " + str(round(time.time() - start_time, 4)) + "s")

    # returns a array image and its location on the canvas
    def get_img(self):
        if self.has_img == False:
            return None, None
        self.has_img = False
        # turn the image in to a array and return it
        self.output_img.convert("RGBA")
        arr = np.array(self.output_img)
        arr = arr.tobytes()
        arr = array("B", arr)
        
        data = BytesIO()
        self.output_img.save(data, format='png')
        data.seek(0) # yes you actually need this
        img = Image(BytesIO(data.read()), ext='png', flipped=False)
        arr = array("B", img.texture.pixels)

        # return the image and its location
        return arr, self.img_loc

    def update_settings(self, config_manager):
        self.guidance_scale = config_manager.get_value("guidance_scale")
        self.num_inference_steps = int(config_manager.get_value("num_inference_steps"))
        self.strength = config_manager.get_value("strength")
        
        # TODO allow switching between models
