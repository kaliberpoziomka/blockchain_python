# %%
from curses.panel import new_panel
import datetime
from email.encoders import encode_noop
import hashlib
import json
from operator import ne
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
        new_proof = 1
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
            if block.previous_hash != self.hash(previous_block):
                return False
            # check if block was validated - i.e. hash operation found a hash with given difficulty
            previous_proof = previous_block.proof
            proof = block.proof
            hash_operation = hashlib\
                            .sha256(str(proof**2 - previous_proof**2)\
                                        .encode())\
                            .hexdigest()
            if hash_operation[:4] != '0'*difficulty:
                return False
            # go to the next block
            previous_block = chain[block_index]

# %% [markdown]
### Part 2 - mining the blockchain
# %%
