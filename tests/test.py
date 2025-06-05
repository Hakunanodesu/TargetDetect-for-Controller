import json

from modules.controller import DualSenseToX360Mapper

with open("./configs/cfg_global.json", "r") as f:
    config = json.load(f)
vendor_id = int(config["controller"]["Vendor_ID"], 16)
product_id = int(config["controller"]["Product_ID"], 16)

mapper = DualSenseToX360Mapper(vendor_id=vendor_id, product_id=product_id, poll_interval=0.002)
mapper.start()