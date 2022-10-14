import json # For reading and writing JSON files

# handles saving and loading of the config file
class ConfigManager:
    def __init__(self):
        self.config = None
        self.config_path = "config.json"
        self.load_config()

    def load_config(self):
        # load the config file
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
            
        except FileNotFoundError:
            print("Config file not found, creating new config file...")
            self.make_default_config()

        # loading the config file was successful
        print("Config file loaded successfully!")

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f)

    def make_default_config(self):
        self.config = {
            "model_id": "CompVis/stable-diffusion-v1-4",
            "device": "cuda",
            "guidance_scale": 7.5,
            "num_inference_steps": 50,
            "strength": 0.75,
            "canvas_size": (512, 512)
        }
        self.save_config()

    def get_value(self, key):
        return self.config.get(key)

    def set_value(self, key, value):
        self.config[key] = value
        self.save_config()
