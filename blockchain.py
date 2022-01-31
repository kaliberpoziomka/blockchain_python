# %%
from curses.panel import new_panel
import datetime
from email.encoders import encode_noop
import hashlib
import json
from operator import ne
from pydoc import resolve
from attr import has
from flask import Flask, jsonify

# %% [markdown]
### Part 1 - building a blockchain
# %%
class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block(proof = 1, previous_hash = '0')
    
    def create_block(self, proof, previous_hash):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": str(datetime.datetime.now()),
            "proof": proof,
            "previous_hash": previous_hash,
        }
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
    
    def is_chain_valid(self, difficulty=4):
        '''This function checks if:
            - the previous blockchain is the same as current
            - Proof of work is valid - i.e. hash generated to mine a block is under given difficulty'''
        previous_block = self.chain[0]
        for block_index, block in enumerate(self.chain[1:]):
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
            previous_block = self.chain[block_index]
        return True

# %% [markdown]
### Part 2 - mining the blockchain
# %%
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

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
    # now we can create block
    block = blockchain.create_block(proof, previous_hash)
    response = {
        "message": "Congratulations, you just mined a block",
        "index": block["index"],
        "timestamp": block["timestamp"],
        "proof": block['proof'],
        "previous_hash": block["previous_hash"],
    }
    return jsonify(response), 200
# %% [markdown]
### Getting the full Blockchain
# %%
@app.route("/get_chain", methods = ["GET"])
def get_chain():
    response = {
        "chain_key": blockchain.chain,
        "length": len(blockchain.chain)
    }
    return jsonify(response), 200
# %%
@app.route('/is_valid', methods = ["GET"])
def is_valid():
    is_valid = blockchain.is_chain_valid()
    if is_valid:
        return jsonify({
        "message": "The blockchain is valid",
        "is_valid": True
    }), 200
    return jsonify({
        "message": "The blockchain is NOT VALID",
        "is_valid": False
    }), 200
# %%
app.run(host = "0.0.0.0", port = 5000)