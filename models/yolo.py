from ultralytics import YOLO
import os
import json


class YOLO11():

    def __init__(self, model_path: str = "./yolo11n.pt"):
        self.model_name = os.path.basename(model_path)
        print("\n正在载入推理模型...")
        self.model = YOLO(model_path, task='detect')
        print(f"推理模型载入完成，当前模型：{self.model_name}\n")

        with open("./configs/cfg_yolo.json", "r") as f:
            config = json.load(f)
        self.infer_conf = config["inference_settings"]["conf"]
        self.infer_iou = config["inference_settings"]["iou"]
        self.infer_classes = config["inference_settings"]["classes"]
        self.train_epochs = config["train_settings"]["epochs"]
        self.train_patience = config["train_settings"]["patience"]
        self.train_batch = config["train_settings"]["batch"]
        self.train_cache = config["train_settings"]["cache"]
        self.train_workers = config["train_settings"]["workers"]
        self.seed = config["seed"]
        with open("./configs/cfg_global.json") as f:
            config = json.load(f)
        self.screenshot_size = config["screenshot_settings"]["size"]
        self.device = config["device"]

    def inference(self, source):
        results = self.model.predict(
            source=source, 
            conf=self.infer_conf, 
            iou=self.infer_iou,
            imgsz=self.screenshot_size,
            device=self.device,
            classes=self.infer_classes,
            verbose=False
        )
        return results[0]
    
    def train(self, data: str, name: str = None):
        self.model.train(
            data=data,
            epochs=self.train_epochs,
            patience=self.train_patience,
            batch=self.train_batch,
            device=self.device,
            seed=self.seed,
            cache=self.train_cache,
            workers=self.train_workers,
            name=name,
        )
