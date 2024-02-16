from web3 import Web3
import json
import time
import requests
import random
import string
import os


"""
Easy way to implement the GPT4-Turbo model market
"""
class GPT4ModelMarket:

    # Initialize the model market and make all the connections
    def __init__(self, private_key, public_key):
        self.rpc = "https://testnet.skalenodes.com/v1/aware-fake-trim-testnet"
        self.web3 = Web3(Web3.HTTPProvider(self.rpc))
        script_dir = os.path.dirname(__file__)  # Get the script's directory
        file_path = os.path.join(script_dir, "LLMMarket.json")
        f = open(file_path)
        data = json.load(f)
        f.close()
        abi = data["abi"]
        self.llm_market = self.web3.eth.contract(address="0xf89e454558717f19926ce66E0EAEF533646d20B0", abi=abi)
        self.private_key = private_key
        self.public_key = public_key
        script_dir = os.path.dirname(__file__)  # Get the script's directory
        file_path = os.path.join(script_dir, "ForumUSD.json")
        f = open(file_path)
        data = json.load(f)
        f.close()
        abi = data["abi"]
        self.forumUSD = self.web3.eth.contract(address="0x67fB809D3c4d265898B2ca6108bd6fe01B89858d", abi=abi)
        print("Initialized!")

    # returns all the nodes
    def get_hosts(self):
        return self.llm_market.functions.getHosts().call()

    # checks if a node is currently paused
    def get_paused(self, host_address):
        return self.llm_market.functions.getPaused(host_address).call()

    # returns the usd token balance of a given address
    def get_token_balance(self, address):
        return self.forumUSD.functions.balanceOf(address).call()

    # mints the usd token (note: only a testnet functionality)
    def mint_token(self):
        unsent_minting_tx = self.forumUSD.functions.mint().build_transaction({
            "from": self.public_key,
            "nonce": self.web3.eth.get_transaction_count(self.public_key),
            "gasPrice": self.web3.eth.gas_price,
        })
        signed_tx = self.web3.eth.account.sign_transaction(unsent_minting_tx, private_key=self.private_key)

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)
        return tx_receipt

    # add a request on the chain
    def add_request_on_chain(self, unique_code, host_address, value):
        unsent_token_approval_tx = self.forumUSD.functions.approve(self.llm_market.address, value).build_transaction({
            "from": self.public_key,
            "nonce": self.web3.eth.get_transaction_count(self.public_key),
            "gasPrice": self.web3.eth.gas_price,
        })
        signed_tx = self.web3.eth.account.sign_transaction(unsent_token_approval_tx, private_key=self.private_key)

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        self.web3.eth.wait_for_transaction_receipt(tx_hash)

        unsent_request_tx = self.llm_market.functions.addRequest(unique_code, host_address, value).build_transaction({
            "from": self.public_key,
            "nonce": self.web3.eth.get_transaction_count(self.public_key),
            "gasPrice": self.web3.eth.gas_price,
        })
        signed_tx = self.web3.eth.account.sign_transaction(unsent_request_tx, private_key=self.private_key)

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)
        return tx_receipt

    # generates an unique code
    @staticmethod
    def generate_unique_code():
        return int(''.join(random.choices(string.digits, k=10)))

    # sends the chat to the node
    @staticmethod
    def create_completion(self, chat, node_url, unique_code):

        data = {
            "unique_code": unique_code,
            "messages": chat
        }
        resp = requests.post(node_url + "ai/create/", json=data)
        return resp.json().get("result")

    # gets the response from the node
    def get_completion(self, node_url, result_code):
        resp = requests.get(node_url + "ai/get/" + result_code)
        return resp.json().get("content")

    def generate(self, total_output_tokens, chat) -> str:
        """
        Generates AI response based on the chat and with max total_output_tokens tokens.

        Args:
            total_output_tokens - int, max number of output tokens of AI response, also influences max number of input chars
            chat - list [{"role": "user", "content": "Lorem ipsum"}, ...], represents the input chat
        Return:
            string - generated output
        """
        node = None
        c = 0
        while not node:
            temp = random.choice(self.get_hosts())
            if not self.get_paused(temp[1]):
                node = temp
            c += 1
            if c > 100:
                return "No nodes active, try again later!"

        unique_code = self.generate_unique_code()
        result_code = self.create_completion(chat, node[0], unique_code)

        value = node[2] * total_output_tokens
        if self.get_token_balance(self.public_key) < value:
            self.mint_token()

        self.add_request_on_chain(unique_code, node[1], value)

        resp = "Still generating!"
        c = 0
        while resp == "Still generating!":
            resp = self.get_completion(node[0], result_code)
            time.sleep(5)
            c += 1
            if c == 20:
                return "Timeout!"
        return resp

    @staticmethod
    def check_if_additional_tokens_necessary(self, total_output_tokens, chat) -> int:
        """
        Checks if the output tokens are enough for a given input (max 15 * input chars than max output tokens allowed) and
        returns how many additional output tokens are required for the generation to work

        Args:
            total_output_tokens - int, max number of output tokens of AI response, also influences max number of input chars
            chat - list [{"role": "user", "content": "Lorem ipsum"}, ...], represents the input chat
        Return:
            int - additional tokens needed
        """
        inp = ""
        for c in chat:
            inp += c["content"]
        return max((int(len(inp) / 15) + 5) - total_output_tokens, 0)
