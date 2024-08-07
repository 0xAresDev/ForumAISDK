import os
import time

from ModelMarketSDK.ModelMarket import Mixtral8x7BSaakuruMainnet
from dotenv import load_dotenv, find_dotenv

"""
Simple demonstration of how easy it is to implement model markets with 'streams'!
"""


# load keys
load_dotenv(find_dotenv())

model_market = Mixtral8x7BSaakuruMainnet(os.environ.get("PRIVATE_KEY"), os.environ.get("PUBLIC_KEY"))

chat = [{"role": "system", "content": "You are a helpful assistant."}]
cont = True

while cont:
    text = input("Input:")
    if text == "q":
        cont = False
        break
    else:
        chat.append({"role": "user", "content": text})
        node_url, result_code = model_market.generate_self_requesting(400, chat, 0.000001)
        full_resp = ""
        done = False
        while not done:
            resp, done = model_market.get_next_output(node_url, result_code, full_resp)
            full_resp += resp
            print(resp, end="")
            time.sleep(0.1)
        chat.append({"role": "assistant", "content": full_resp})
        print("\n")
