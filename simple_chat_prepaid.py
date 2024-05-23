import os
from ModelMarketSDK.ModelMarket import Mixtral8x7BModelMarketTestnet
from dotenv import load_dotenv, find_dotenv

"""
Simple demonstration of how easy it is to implement model markets!
"""


# load keys
load_dotenv(find_dotenv())

model_market = Mixtral8x7BModelMarketTestnet(os.environ.get("PRIVATE_KEY"))
if model_market.balance_of(model_market.account.address) < 5*10*18:
    model_market.deposit(5*10**18)

chat = [{"role": "system", "content": "You are a helpful assistant!"}]
cont = True

while cont:
    text = input("Input:")
    if text == "q":
        cont = False
        break
    else:
        chat.append({"role": "user", "content": text})
        resp = model_market.chat_completion(3000, chat, prepaid=True)
        print(resp)
        chat.append({"role": "assistant", "content": resp})
