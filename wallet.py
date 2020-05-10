from constants import *
import subprocess
import json
import os
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy
from bit import wif_to_key, PrivateKeyTestnet
from bit.network import NetworkAPI
from eth_account import Account

load_dotenv()

#Generating a Mnemonic and creating a variable for the accounts private key
mnemonic = os.getenv('MNEMONIC')

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

#Deriving the wallet keys

def derive_wallets (mnemonic,coin,number):
    command = f'php ./hd-wallet-derive/hd-wallet-derive.php --mnemonic="{mnemonic}" -g --numderive="{number}" --coin="{coin}" --cols=address,index,path,privkey,pubkey,pubkeyhash,xprv,xpub --format=json'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) =p.communicate()
    p_status = p.wait()
    keys = json.loads(output)
    return keys

# Linking the transaction signing libraries

def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    elif coin == BTCTEST:
        return PrivateKeyTestnet(priv_key)

def create_tx(coin, account, to, amount):
    if coin == ETH:
        gasEstimate = w3.eth.estimateGas(
        {"from": eth_acc.address, "to": to, "value": amount}
    )
        return {
            "from": eth_acc.address,
            "to": to,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(account.address),
            
    }
    elif coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])


def send_tx(coin,account, recipient, amount):
    tx = create_tx(coin,account,recipient,amount)
    
    if coin == ETH:
        signed_tx = eth_account.sign_transaction(tx)
        result = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return result.hex()
    elif coin == BTCTEST:
        signed_tx = btc_account.sign_transaction(tx)
        return NetworkAPI.broadcast_tx_testnet(signed_tx)
    
def transaction(coin, sender, to, amount):
    send_key = derive_wallets(mnemonic, coin, 5)[sender]['privkey']
    send_hash = priv_key_to_account(coin, send_key)
    to_address = derive_wallets(mnemonic, coin, 5)[to]['address']
    return send_tx(coin, send_hash, to_address, amount)




