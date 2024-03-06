NOTE: THIS IS NOT ACCURATE ANYMORE. WE ARE GOING TO UPDATE THE DOCS IN A FEW HOURS!

Pre-alpha implementation of the ForumAI model market python sdk.
We will turn this into a proper python package soon.

How to use:

Make sure that you have git installed and use "git clone https://github.com/0xAresDev/ForumAISDK.git" to clone the repo.

Install the required packages with _pip3 install -r ForumAISDK/requirements.txt_

In a python file:

from ForumAISDK.ModelMarketSDK.ModelMarket import GPT4ModelMarket

model_market = GPT4ModelMarket(PRIVATE_KEY, PUBLIC_KEY)

chat = [{"role": "system", "content": "You are a helpful coding assistant"}, {"role": "user", "content": "What is 2 +2?"}]

resp = model_market.generate(1000, chat)

Replace PRIVATE_KEY and PUBLIC_KEY with your keys.

The **generate** method of GPT4ModelMarket takes 2 arguments, the first is max_output_tokens that limits the amount of output tokens and the chat.

Before you can run this code, you also have to claim some sFUEL (native gas tokens for skale blockchains). You can do this here: https://www.sfuelstation.com/
Make sure to switch to testnet and claim sFUEL for the Titan AI Hub chain.
