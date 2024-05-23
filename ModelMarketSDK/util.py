from web3 import Web3
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount

def sign_payment(payment: dict, account: LocalAccount) -> str:
    sender = payment['sender']
    receiver = payment['receiver']
    amount = payment['amount']
    uuid = payment['uuid']

    # Create the message hash
    message = Web3.solidity_keccak(
        ['address', 'address', 'uint256', 'string'],
        [Web3.to_checksum_address(sender), Web3.to_checksum_address(
            receiver), amount, uuid]
    )

    # Encode the message hash to be compatible with Ethereum signature verification
    encoded_message = encode_defunct(message)

    return account.sign_message(encoded_message).signature.hex()
