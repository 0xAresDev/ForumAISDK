from web3 import Web3
import json
import time
import requests
import random
import string
import os
import tiktoken



"""
Mixtral8x7BModelMarketTestnet allows developers to access the Mixtral8x7B model on the testnet
"""
class Mixtral8x7BModelMarketTestnet:

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
        self.llm_market = self.web3.eth.contract(address="0x6b0934eeF1BeD7F3f53fE1E647096666286Df443", abi=abi)
        self.private_key = private_key
        self.public_key = public_key
        script_dir = os.path.dirname(__file__)  # Get the script's directory
        file_path = os.path.join(script_dir, "USDC.json")
        f = open(file_path)
        data = json.load(f)
        f.close()
        abi = data["abi"]
        self.usdc = self.web3.eth.contract(address="0xC1e229808C9A2Dc675d1E415C03FaD1C41C92b2b", abi=abi)
        print("Initialized!")

    # returns all the nodes
    def get_hosts(self):
        return self.llm_market.functions.getHosts().call()

    # checks if a node is currently paused
    def get_paused(self, host_address):
        return self.llm_market.functions.getPaused(host_address).call()

    # returns the usd token balance of a given address
    def get_token_balance(self, address):
        return self.usdc.functions.balanceOf(address).call()

    # mints the usdc token (note: only a testnet functionality)
    def mint_token(self):
        unsent_minting_tx = self.usdc.functions.mint(5*(10**18)).build_transaction({
            "from": self.public_key,
            "nonce": self.web3.eth.get_transaction_count(self.public_key),
            "gasPrice": self.web3.eth.gas_price,
        })
        signed_tx = self.web3.eth.account.sign_transaction(unsent_minting_tx, private_key=self.private_key)

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)

        unsent_token_approval_tx = self.usdc.functions.approve(self.llm_market.address, 5*(10**6)).build_transaction({
            "from": self.public_key,
            "nonce": self.web3.eth.get_transaction_count(self.public_key),
            "gasPrice": self.web3.eth.gas_price,
        })
        signed_tx = self.web3.eth.account.sign_transaction(unsent_token_approval_tx, private_key=self.private_key)

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt

    # add a request on the chain
    def add_request_on_chain(self, unique_code, host_address, value):

        allowance = self.usdc.functions.allowance(self.public_key, self.llm_market.address).call()
        if allowance < value:
            unsent_token_approval_tx = self.usdc.functions.approve(self.llm_market.address,
                                                                   self.usdc.functions.balanceOf(self.public_key).call()).build_transaction({
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
    def create_completion(chat, node_url, unique_code):

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

        inp = ""
        for c in chat:
            inp += c["content"]
        value = node[2] * (total_output_tokens+(Mixtral8x7BModelMarketTestnet.num_tokens_from_string(inp, "cl100k_base") + len(chat)*4))
        if self.get_token_balance(self.public_key) < value:
            self.mint_token()

        self.add_request_on_chain(unique_code, node[1], value)

        c = 0
        resp = ""
        while len(resp) < 10 or resp[-3:] != "<e>":

            resp = self.get_completion(node[0], result_code)
            time.sleep(1)
            c += 1
            if c == 50:
                return "Timeout!"

        return resp[3:-3]

    def generate_self_requesting(self, total_output_tokens, chat) -> (str, str):
        """
        Requests an AI response based on the chat and with max total_output_tokens tokens.

        Args:
            total_output_tokens - int, max number of output tokens of AI response, also influences max number of input chars
            chat - list [{"role": "user", "content": "Lorem ipsum"}, ...], represents the input chat
        Return:
            string - node url
            string -result code
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

        inp = ""
        for c in chat:
            inp += c["content"]
        value = node[2] * (total_output_tokens + (
                    Mixtral8x7BModelMarketTestnet.num_tokens_from_string(inp, "cl100k_base") + len(chat) * 4))
        if self.get_token_balance(self.public_key) < value:
            self.mint_token()

        self.add_request_on_chain(unique_code, node[1], value)

        return node[0], result_code

    # returns the next part of the output
    def get_next_output(self, node_url, result_code, old_output="") -> (str, bool):
        """
            Returns the next part of the output that has been generated by now

            Args:
                node_url - url of the node that handels the API request
                result_code - unique code that allows to access the response
                old_output - output that has been generated until now
            Return:
                string - next part of the output
                bool - shows if the generation is finished
        """
        done = False
        resp = self.get_completion(node_url, result_code)
        resp = resp[len(old_output)+3:]
        if resp[-3:] == "<e>":
            resp = resp[:-3]
            done = True
        return resp, done

    @staticmethod
    def num_tokens_from_string(string: str, encoding_name: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
