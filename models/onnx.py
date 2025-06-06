import cv2
import numpy as np
import onnxruntime
import json


class APV5Experimental:
    def __init__(self, model_path):
        with open("configs/cfg_model.json", "r") as f:
            config = json.load(f)
        self.input_size = config["imgsz"]
        self.conf_thres = config["inference_settings"]["conf"]
        self.iou_thres = config["inference_settings"]["iou"]
        self.classes = config["inference_settings"]["classes"]
        with open("configs/cfg_global.json", "r") as f:
            config = json.load(f)
        self.screenshot_size = config["screenshot_settings"]["size"]
        self.scale = self.screenshot_size / self.input_size

        self.session = onnxruntime.InferenceSession(
            model_path,
            providers=[
                "DmlExecutionProvider",
                "CPUExecutionProvider"
            ]
        )
        self.input_name = self.session.get_inputs()[0].name
        self.provider = self.session.get_providers()[0]

    def preprocess(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        tensor = cv2.resize(image, (self.input_size, self.input_size))
        tensor = tensor.astype(np.float32) / 255.0
        tensor = np.transpose(tensor, (2, 0, 1))  # HWC -> CHW
        tensor = np.expand_dims(tensor, axis=0)
        return tensor, image

    def predict(self, image):
        input_tensor, image = self.preprocess(image)
        preds = self.session.run(None, {self.input_name: input_tensor})[0][0]  # shape: [N, 85]

        boxes = preds[:, :4]  # xywh
        scores = preds[:, 4]
        class_probs = preds[:, 5:]
        class_ids = np.argmax(class_probs, axis=1)
        confidences = scores * class_probs[np.arange(len(class_probs)), class_ids]

        # 筛选 class == 0 且 confidence > 阈值
        mask = (class_ids == self.classes) & (confidences > self.conf_thres)
        boxes = boxes[mask]
        confidences = confidences[mask]

        if len(boxes) == 0:
            return [], image

        # NMS 处理
        xyxy_boxes = boxes.copy()
        xyxy_boxes[:, 0] = boxes[:, 0] - boxes[:, 2] / 2  # x1
        xyxy_boxes[:, 1] = boxes[:, 1] - boxes[:, 3] / 2  # y1
        xyxy_boxes[:, 2] = boxes[:, 0] + boxes[:, 2] / 2  # x2
        xyxy_boxes[:, 3] = boxes[:, 1] + boxes[:, 3] / 2  # y2

        keep = self.nms(xyxy_boxes, confidences, self.iou_thres)
        kept_boxes = boxes[keep]  # 原始 xywh，取中心点即可

        # 计算中心点，缩放回原图尺寸
        cxcy_list = []
        for box in kept_boxes:
            cx = box[0] * self.scale
            cy = box[1] * self.scale
            cxcy_list.append((float(cx), float(cy)))

            w = box[2] * self.scale
            h = box[3] * self.scale
            # 计算左上角与右下角
            x1 = int(cx - w / 2)
            y1 = int(cy - h / 2)
            x2 = int(cx + w / 2)
            y2 = int(cy + h / 2)
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        return cxcy_list, image

    @staticmethod
    def nms(boxes, scores, iou_threshold):
        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            inter = np.maximum(0.0, xx2 - xx1) * np.maximum(0.0, yy2 - yy1)
            iou = inter / (areas[i] + areas[order[1:]] - inter)
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        return keep

if __name__ == "__main__":
    model = APV5Experimental("apv5.onnx")
    image = cv2.imread("320.jpg")
    cxcy_list = model.predict(image)
    print(cxcy_list)
    cv2.imshow("detection", model.img)
    while True:
        if cv2.waitKey(1) == ord("q"):
            break