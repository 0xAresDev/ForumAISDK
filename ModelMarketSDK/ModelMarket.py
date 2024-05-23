from typing import Iterator
from web3 import Web3
from web3.types import TxReceipt
import json
import requests
import random
import os
import tiktoken
from eth_account.signers.local import LocalAccount
from eth_account import Account
import uuid
import json
from .util import sign_payment
from .constant import CURRENCY_TOKEN, LLM_MARKET, RPC


"""
Mixtral8x7BModelMarketTestnet allows developers to access the Mixtral8x7B model on the testnet
"""


class Mixtral8x7BModelMarketTestnet:

    # Initialize the model market and make all the connections
    def __init__(self, private_key, *argv):
        self.rpc = RPC
        self.web3 = Web3(Web3.HTTPProvider(self.rpc))
        script_dir = os.path.dirname(__file__)  # Get the script's directory
        file_path = os.path.join(script_dir, "LLMMarket.json")
        f = open(file_path)
        data = json.load(f)
        f.close()
        abi = data["abi"]
        self.llm_market = self.web3.eth.contract(address=LLM_MARKET, abi=abi)
        self.private_key = private_key
        self.public_key = self.web3.eth.account.from_key(private_key).address
        script_dir = os.path.dirname(__file__)  # Get the script's directory
        file_path = os.path.join(script_dir, "USDC.json")
        f = open(file_path)
        data = json.load(f)
        f.close()
        abi = data["abi"]
        self.usdc = self.web3.eth.contract(address=CURRENCY_TOKEN, abi=abi)
        self.account: LocalAccount = Account.from_key(private_key)
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
    def mint_token(self, amount=5*(10**18)):
        unsent_minting_tx = self.usdc.functions.mint(amount).build_transaction({
            "from": self.public_key,
            "nonce": self.web3.eth.get_transaction_count(self.public_key),
            "gasPrice": self.web3.eth.gas_price,
        })
        signed_tx = self.web3.eth.account.sign_transaction(
            unsent_minting_tx, private_key=self.private_key)

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)

        unsent_token_approval_tx = self.usdc.functions.approve(self.llm_market.address, amount).build_transaction({
            "from": self.public_key,
            "nonce": self.web3.eth.get_transaction_count(self.public_key),
            "gasPrice": self.web3.eth.gas_price,
        })
        signed_tx = self.web3.eth.account.sign_transaction(
            unsent_token_approval_tx, private_key=self.private_key)

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt

    # add a request on the chain
    def add_request_on_chain(self, uuid, host_address, amount, wait_for_tx = False) -> str | TxReceipt:

        allowance = self.usdc.functions.allowance(
            self.public_key, self.llm_market.address).call()
        if allowance < amount:
            unsent_token_approval_tx = self.usdc.functions.approve(self.llm_market.address,
                                                                   self.usdc.functions.balanceOf(self.public_key).call()).build_transaction({
                                                                       "from": self.public_key,
                                                                       "nonce": self.web3.eth.get_transaction_count(self.public_key),
                                                                       "gasPrice": self.web3.eth.gas_price,
                                                                   })
            signed_tx = self.web3.eth.account.sign_transaction(
                unsent_token_approval_tx, private_key=self.private_key)

            tx_hash = self.web3.eth.send_raw_transaction(
                signed_tx.rawTransaction)

            self.web3.eth.wait_for_transaction_receipt(tx_hash)

        unsent_request_tx = self.llm_market.functions.addRequest(uuid, host_address, amount).build_transaction({
            "from": self.public_key,
            "nonce": self.web3.eth.get_transaction_count(self.public_key),
            "gasPrice": self.web3.eth.gas_price,
        })
        signed_tx = self.web3.eth.account.sign_transaction(
            unsent_request_tx, private_key=self.private_key)

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        if wait_for_tx:
            self.web3.eth.wait_for_transaction_receipt(tx_hash)
            tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            return tx_receipt
        else:
            return tx_hash.hex()

    @staticmethod
    def num_tokens_from_string(string: str, encoding_name: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def deposit(self, amount=5 * 10 ** 18):
        if self.get_token_balance(self.account.address) < amount:
            self.mint_token(amount)

        unsent_request_tx = self.llm_market.functions.deposit(amount).build_transaction({
            "from": self.public_key,
            "nonce": self.web3.eth.get_transaction_count(self.public_key),
            "gasPrice": self.web3.eth.gas_price,
        })
        signed_tx = self.web3.eth.account.sign_transaction(
            unsent_request_tx, private_key=self.private_key)

        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)
        return tx_receipt

    def balance_of(self, address: str = None):
        return self.llm_market.functions.balances(address if address else self.account.address).call()

    def prepaid_chat_completion(self, total_output_tokens, chat, stream=False) -> str | Iterator[str]:
        """
        Generates AI response based on the chat and with max total_output_tokens tokens.

        Args:
            total_output_tokens - int, max number of output tokens of AI response, also influences max number of input chars
            chat - list [{"role": "user", "content": "Lorem ipsum"}, ...], represents the input chat
            stream - bool, stream enabled or not
        Return:
            string | string generator - generated output or a generator for stream ouput
        """
        node = random.choice(self.get_hosts())
        node_url, node_address, token_price = node
        # print(node_url, node_address, token_price)

        amount = token_price * (total_output_tokens+(Mixtral8x7BModelMarketTestnet.num_tokens_from_string(
            '\n'.join([c["content"] for c in chat]), "cl100k_base") + len(chat)*4))
        payment = {
            'sender': self.account.address,
            'receiver': node_address,
            'amount': amount,
            'uuid': str(uuid.uuid4())
        }
        signature = sign_payment(payment, self.account)

        payload = {
            "messages": chat,
            "stream": stream,
            "payment": {
                "uuid": payment["uuid"],
                "sender": payment["sender"],
                "receiver": payment["receiver"],
                "max_amount": payment["amount"],
                "signature": signature
            }
        }

        if not stream:
            try:
                resp = requests.post(node_url + "/chat", json=payload)
                resp_content = resp.json()['choices'][0]['message']['content']
                return resp_content
            except Exception as e:
                print(e)
                return "Invalid response"
        else:
            def get_streamed_resp():
                try:
                    headers = {'Accept': 'text/event-stream'}
                    with requests.post(node_url + "/chat", stream=True, headers=headers, json=payload) as response:
                        for line in response.iter_lines():
                            json_resp = json.loads(line.decode())
                            yield json_resp['choices'][0]['delta']['content']
                except Exception as e:
                    return "Invalid response"
            return get_streamed_resp()

    def paid_chat_completion(self, total_output_tokens, chat, stream=False) -> str | Iterator[str]:
        """
        Generates AI response based on the chat and with max total_output_tokens tokens.

        Args:
            total_output_tokens - int, max number of output tokens of AI response, also influences max number of input chars
            chat - list [{"role": "user", "content": "Lorem ipsum"}, ...], represents the input chat
            stream - bool, stream enabled or not
        Return:
            string | string generator - generated output or a generator for stream ouput
        """
        node = random.choice(self.get_hosts())
        node_url, node_address, token_price = node
        # print(node_url, node_address, token_price)

        resp = requests.get(node_url + "/paid-chat")
        uuid =  resp.json().get("uuid")

        amount = token_price * (total_output_tokens+(Mixtral8x7BModelMarketTestnet.num_tokens_from_string(
            '\n'.join([c["content"] for c in chat]), "cl100k_base") + len(chat)*4))
        
        tx_hash = self.add_request_on_chain(uuid, node_address, amount)
        
        
        paid_payment = {
            'uuid': uuid,
            'tx_hash': tx_hash
        }
        
        payload = {
            "messages": chat,
            "stream": stream,
            "paid_payment": paid_payment
        }

        if not stream:
            try:
                resp = requests.post(node_url + "/paid-chat-completion", json=payload)
                resp_content = resp.json()['choices'][0]['message']['content']
                return resp_content
            except Exception as e:
                print(e)
                return "Invalid response"
        else:
            def get_streamed_resp():
                try:
                    headers = {'Accept': 'text/event-stream'}
                    with requests.post(node_url + "/paid-chat-completion", stream=True, headers=headers, json=payload) as response:
                        for line in response.iter_lines():
                            json_resp = json.loads(line.decode())
                            yield json_resp['choices'][0]['delta']['content']
                except Exception as e:
                    yield "Invalid response"
            return get_streamed_resp()

    def chat_completion(self, total_output_tokens, chat, stream=False, prepaid=False) -> str | Iterator[str]:
        """
        Generates AI response based on the chat and with max total_output_tokens tokens.

        Args:
            total_output_tokens - int, max number of output tokens of AI response, also influences max number of input chars
            chat - list [{"role": "user", "content": "Lorem ipsum"}, ...], represents the input chat
            stream - bool, stream enabled or not
            prepaid - bool, if you already deposit to the model market then you can use prepaid mode, this mode will reduce the latency for the chat
        Return:
            string | string generator - generated output or a generator for stream ouput
        """
        if prepaid:
            return self.prepaid_chat_completion(total_output_tokens, chat, stream)
        else:
            return self.paid_chat_completion(total_output_tokens, chat, stream)
