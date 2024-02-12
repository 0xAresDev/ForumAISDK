import os
from ModelMarketSDK.ModelMarket import GPT4ModelMarket
from dotenv import load_dotenv, find_dotenv

"""
Simple demonstration of how easy it is to implement model markets!
"""


# load keys
load_dotenv(find_dotenv())

model_market = GPT4ModelMarket(os.environ.get("PRIVATE_KEY"), os.environ.get("PUBLIC_KEY"))

chat = [{"role": "system", "content": "You are a helpful coding assistant"}]
cont = True

while cont:
    text = input("Input:")
    if text == "q":
        cont = False
        break
    else:
        chat.append({"role": "user", "content": text})
        resp = model_market.generate(1000, chat)
        print(resp)
        chat.append({"role": "assistant", "content": resp})
