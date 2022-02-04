# %%
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4 # random unique address
from urllib.parse import urlparse
# %% [markdown]
### Part 1 - building a blockchain
# %%
## GLOBAL VARS
NODE_NAME = "NODE" 
# %%
class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = [] # mempool
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
    
    def create_block(self, proof, previous_hash):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": str(datetime.datetime.now()),
            "proof": proof,
            "previous_hash": previous_hash,
            "transactions": self.transactions # transactions added to the block
        }
        self.transactions = [] # clear mempool
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof, difficulty = 4):
        '''This function mines a block using proof of work'''
        new_proof = 1 # nonce
        check_proof = False
        while not check_proof:
            # operation in hash function must be non-symetrical,
            # so for example adding new_proof and previous_proof would create
            # the same prof every two blocks
            # so we need to create asymetric funcion
            hash_operation = hashlib\
                            .sha256(str(new_proof**2 - previous_proof**2)\
                                        .encode())\
                            .hexdigest() # this gives hexadecimal representation
            # .encode() adds b to string, so sha can take it
            if hash_operation[:4] == '0'*difficulty: # 4 zeros - that is difficulty
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        '''This function creates hash from block'''
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain, difficulty=4):
        '''This function checks if:
            - the previous blockchain is the same as current
            - Proof of work is valid - i.e. hash generated to mine a block is under given difficulty'''
        previous_block = chain[0]
        for block_index, block in enumerate(chain[1:]):
            block_index += 1 # because enumerate allways returns index from zero
            # check previous block and current block if they are the same (after the hash function)
            if block["previous_hash"] != self.hash(previous_block):
                return False
            # check if block was validated - i.e. hash operation found a hash with given difficulty
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib\
                            .sha256(str(proof**2 - previous_proof**2)\
                                        .encode())\
                            .hexdigest()
            if hash_operation[:4] != '0'*difficulty:
                return False
            # go to the next block
            previous_block = chain[block_index]
        return True

    
    # TRANSACTIONS
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({"sender": sender, "receiver": receiver, "amount": amount})
        # return index of a block to which transactions are being added
        return self.get_previous_block()["index"]+1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get("http://"+node+"/get_chain")
            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain: # if is not None
            self.chain = longest_chain
            return True
        return False
# %% [markdown]
### Part 2 - mining the blockchain
# %%
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace("-", "")

blockchain = Blockchain()

@app.route('/mine_block', methods=["GET"])
def mine_block():
    # to mine a block we need two things
    # 1. we need to create a proof of work, this is created by taking
    # previous proof (previous block nonce) and currenct nonce, and passing it to sha256. 
    # We need to obtain hex number under certain difficulty (number of zeros at the beginning)
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    # 2. we need to create a hash from previous block
    previous_hash = blockchain.hash(previous_block)
    # transactions
    # here smoneone sends me, because im the Miner, and so when the block is mined, some coins are going to me
    blockchain.add_transaction(sender=node_address, receiver=NODE_NAME, amount=1)
    # now we can create block
    block = blockchain.create_block(proof, previous_hash)
    response = {
        "message": "Congratulations, you just mined a block",
        "index": block["index"],
        "timestamp": block["timestamp"],
        "proof": block['proof'],
        "previous_hash": block["previous_hash"],
        "transaction": block["transactions"]
    }
    return jsonify(response), 200
# %% [markdown]
### Getting the full Blockchain
# %%
@app.route("/get_chain", methods = ["GET"])
def get_chain():
    response = {
        "chain": blockchain.chain,
        "length": len(blockchain.chain)
    }
    return jsonify(response), 200
# %%
@app.route('/is_valid', methods = ["GET"])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        return jsonify({
        "message": "The blockchain is valid",
        "is_valid": True
    }), 200
    return jsonify({
        "message": "The blockchain is NOT VALID",
        "is_valid": False
    }), 200


@app.route('/add_transaction', methods = ["POST"])
def add_transaction():
    json = request.get_json()
    transaction_keys = ["sender", "receiver", "amount"]
    if not all([key in json for key in transaction_keys]):
        return "ERROR: Some elements of the transactions are missing", 400
    sender, receiver, amount = json.values()
    index = blockchain.add_transaction(sender, receiver, amount)
    response = {"message": f"Transactions is going to be added to the block {index}"}
    return response, 201
# %% [markdown]
### Part 3 - Decentralizing
# %%
## Connecting new nodes
@app.route('/connect_node', methods = ["POST"])
def connect_node():
    json = request.get_json()
    nodes_addresses = json.get("nodes") # it contains all the nodes addresses in the network
    if nodes_addresses is None:
        return "No node", 400
    # adding new nodes addresses (from the http post) to the network
    for node_address in nodes_addresses:
        blockchain.add_node(node_address)
    response = {"message": "New nodes connected to the network",
                "total_nodes": list(blockchain.nodes)}
    return jsonify(response), 201

# Concsensus - replace chains with the longest chain
@app.route('/consensus', methods = ["GET"])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        return jsonify({
            "message": "New chain - replaced with by the longest one.",
            "new_chain": blockchain.chain
        }), 200
    return jsonify({
            "message": "No changes, chain is the longest one.",
            "actual_chain": blockchain.chain
        }), 200
# %%
# app.run(host = "0.0.0.0", port = 5000)