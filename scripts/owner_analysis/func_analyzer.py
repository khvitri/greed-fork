

import sys
import logging
import os
import sha3
import web3

from SEtaac import Project
from SEtaac import options
from SEtaac.solver.shortcuts import *
from SEtaac.utils import gen_exec_id
from SEtaac.exploration_techniques import DFS, DirectedSearch, HeartBeat, SimgrViz, Prioritizer, SizeLimiter

from guard_blocks_checker import GuardedBlockChecker

LOGGING_FORMAT = "%(levelname)s | %(name)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
log = logging.getLogger("func_analyzer")
log.setLevel(logging.INFO)

# ATTACH TO GETH
w3 = web3.Web3(web3.Web3.HTTPProvider('http://0.0.0.0:8545'))
assert(w3.isConnected())

import db 

FUNCS_TO_CHECK = set()
GUARDED_BASIC_BLOCKS = set()

# This is going to be of this kind:
# GUARDED_BASIC_BLOCKS_COVERAGE[0x12345] = [CALLER1, CALLER2]
# this means that when using CALLER1 OR CALLER2, we covered that basic block.
GUARDED_BASIC_BLOCKS_COVERAGE = dict()

# Check a batch of 100 transactions every time.
LIMIT_BATCH_TX = 100

VALID_OWNERS = list()


def get_public_caller(p, f):
    callers = [e[0] for e in p.callgraph.edges if e[1] == f]
    for caller in callers:
        if caller.id == "0x0":
            continue
        else:
            if caller.public:
                log.info(f"     > Found public caller: {caller.signature}")
                FUNCS_TO_CHECK.add(caller)
            else:
                return get_public_caller(p, caller)

def grab_all_guarded_basic_blocks(p):
    all_guarded_bbs = []
    for f in p.function_at.values():
        for bb in f.blocks:
            if bb.guarded_by_caller:
                all_guarded_bbs.append(bb)
    return all_guarded_bbs

# Scan all the functions in the contract
# and save the GUARDED FUNCTIONS
def grab_guarded_funcs(p):
    for f in p.function_at.values():
        log.info(f"<<<Checking function {f.name} [signature: {f.signature}] [tac_id: {f.id}]>>>")
        # Iterate over all the basic blocks in the function
        for bb in f.blocks:
            # If we find at least one guarded basic block in this function, then 
            # we mark this function as guarded (there exists a guarded path)
            if bb.guarded_by_caller:
                log.info(f"  Function contains guarded basic blocks!")
                log.info(f"     > public, adding to list")
                if f.public:
                    FUNCS_TO_CHECK.add(f)
                else:
                    log.info(f"     > not public, grabbing callers")
                    get_public_caller(p, f)
                # Go to next function.
                break


def tx_to_init_ctx(tx_hash):
    """
    Convert a transaction to an initial context.
    """
    init_ctx = dict()
    
    # We can decide later to filter the TX for which the CALLER 
    # is not a contract TODO

    tx_raw = w3.eth.getTransaction(tx_hash)

    init_ctx["CALLDATA"] = tx_raw['input']
    init_ctx["CALLDATASIZE"] = (len(init_ctx["CALLDATA"]) - 2) // 2
    init_ctx["CALLER"] = int(tx_raw['from'],16)
    init_ctx["CALLVALUE"] = tx_raw['value']
    init_ctx["CHAINID"] = tx_raw['chainId']
    #init_ctx["GASPRICE"] = tx_raw['gasPrice']

    # -1 because we want the current block number when the contract 
    # was executing, NOT when the tx has been included!
    init_ctx["NUMBER"] =  tx_raw['blockNumber'] - 1 

    # This should be good?
    init_ctx["TIMESTAMP"] =  w3.eth.getBlock(init_ctx["NUMBER"]).timestamp
    
    return init_ctx


def replay_transaction_with_context(p, init_ctx):
    options.GREEDY_SHA = True
    options.LAZY_SOLVES = False
    options.STATE_INSPECT = False 
    options.MAX_SHA_SIZE = 300
    xid = gen_exec_id()
    

    # Set the project at that specific block.
    entry_state = p.factory.entry_state(xid=xid, init_ctx=init_ctx, 
                                        max_calldatasize=init_ctx["CALLDATASIZE"],
                                        options={"chain_at": init_ctx["NUMBER"]})

    simgr = p.factory.simgr(entry_state=entry_state)
    
    dfs = DFS()
    simgr.use_technique(dfs)

    #simgrviz = SimgrViz()
    #simgr.use_technique(simgrviz)

    gbc = GuardedBlockChecker(GUARDED_BASIC_BLOCKS)
    simgr.use_technique(gbc)

    heartbeat = HeartBeat(beat_interval=100)
    simgr.use_technique(heartbeat)
 
    simgr.run()

    return simgr._techniques[1].checked_blocks_covered  


def get_tx_to_replay(contract_addr, limit, offset, filtered_from):
    tx_to_replay = list()

    log.info(f"Fetching new TXs to replay. Ignoring these {filtered_from} callers")

    while len(tx_to_replay) != 10:
        
        transactions = db.get_n_transactions_to(contract_addr,LIMIT_BATCH_TX, offset)
        
        if len(transactions) == 0:
            log.warning("No more transactions for contract")
            break
        else:
            offset += len(transactions)
            for tx in transactions:
                func_id = tx.data[:10]
                if func_id in FUNCS_TO_CHECK_SIG and tx.sender not in filtered_from:
                    log.info(f"Tx {tx.transaction_hash} calls the target function {func_id} | caller is {tx.sender}!")
                    tx_to_replay.append(tx)

    return tx_to_replay, offset
    

if __name__ == "__main__":
    target_dir = sys.argv[1]
    contract_addr = sys.argv[2]

    p = Project(target_dir=target_dir, contract_addr=contract_addr, partial_concrete_storage=True)
    
    all_guarded_bbs = grab_all_guarded_basic_blocks(p)

    grab_guarded_funcs(p)

    # Now, for every guarded function we want to extract transactions that are calling those
    # functions
    offset = 0
    FUNCS_TO_CHECK_SIG = [f.signature for f in FUNCS_TO_CHECK]
    
    all_guarded_bbs_covered = set()

    while True:
        all_tx_to_replay, offset = get_tx_to_replay(contract_addr, LIMIT_BATCH_TX, offset, VALID_OWNERS)
        
        # No more txs?
        if len(all_tx_to_replay) == 0:
            break
        
        for tx_to_replay in all_tx_to_replay:
            
            # Skip TXs coming from account that we already know are owners
            if tx_to_replay.sender.lower() in VALID_OWNERS:
                continue
            
            init_ctx = tx_to_init_ctx(tx_to_replay.transaction_hash)
            log.info(f"Replaying tx {tx_to_replay.transaction_hash} with initial context {init_ctx}")
            guarded_blocks_covered = replay_transaction_with_context(p, init_ctx)
            all_guarded_bbs_covered = all_guarded_bbs_covered.union(guarded_blocks_covered)
            if len(guarded_blocks_covered) != 0:
                # This means the caller was able to cover at least one guarded basic block
                # hence, the caller is an "owner"
                # We are not going to consider this CALLER anymore.
                VALID_OWNERS.append(hex(init_ctx["CALLER"]))
        
        if len(all_guarded_bbs_covered) == len(all_guarded_bbs):
            log.info(f"All guarded basic blocks have been covered!")
            break
    
    log.info("Extracted valid owners are:")
    for o in VALID_OWNERS:
        log.info(">> {o}")