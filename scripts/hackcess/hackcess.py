import sys 
import logging 
import networkx as nx
import sha3 

from SEtaac import Project
from SEtaac.TAC.base import TAC_Statement
from SEtaac import options
from SEtaac.utils import gen_exec_id
from SEtaac.exploration_techniques import DFS, DirectedSearch, HeartBeat, SimgrViz
from SEtaac.utils.solver.shortcuts import *

from sha_resolver import ShaResolver
from taint_analyses import CalldataToFuncTarget, CalldataToContractTarget

import random

log = logging.getLogger("Hackcess")
log.setLevel(logging.INFO)

class CallInfo():
    def __init__(self, call_stmt):

        self.call_stmt = call_stmt

        # Classification TTT,UTT,UUU,...
        self.taintedContractAddress = True
        self.taintedFunction = True
        self.taintedArguments = True

        # list of destination contracts that can be called
        self.contractAddresses = list()
        # list of destination functions that can be called
        self.functionAddresses = list()
        # list of arguments that can be provided to the call
        self.argumentsValuse = list()

        # Stores here the values of the possible argsOffsets
        self.argsOffsets = list()
        # Stores here the values of the possible argsSizes
        self.argsSizes = list()
    
    @property
    def call_type(self):
        type_str = ""
        if self.taintedContractAddress:
            type_str += "T"
        else:
            type_str += "U"
        if self.taintedFunction:
            type_str += "T"
        else:
            type_str += "U"
        if self.taintedArguments:
            type_str += "*"
        else:
            type_str += "*"
        return type_str
        
    def __str__(self):
        return f"Call at {self.call_stmt.id} | call_type: {self.call_type}"


def analyze_state_at_call(state, target_call_info):
    static_targetContract = False
    tainted_targetContract = False
    tainted_targetFunc = False 

    if len(target_call_info.contractAddresses) == 1:
        log.info(f"Fixated CALL targetContract at {hex(target_call_info.contractAddresses[0])}")
        static_targetContract = True
    else:
        #ta1 = CalldataToContractTarget(state, source_start=68, source_end=77)
        ta1 = CalldataToContractTarget(state, source_start=4)
        ta1.run()
        tainted_targetContract = ta1.is_tainted
    
    assert(state.solver.frame==0)

    if len(target_call_info.functionAddresses) == 1:
        log.info(f"Fixated CALL targetFunc at {hex(target_call_info.functionAddresses[0])}")
    else:
        if static_targetContract:
            sha_deps = None
        else:
            sha_deps = ta1.sha_resolver.sha_deps
        ta2 = CalldataToFuncTarget(state, source_start=4, sha_deps=sha_deps)
        ta2.run()
        tainted_targetFunc = ta2.is_tainted
    
    return tainted_targetContract, tainted_targetFunc
    

def get_init_ctx_for(func):
    # This function will use the prototype recovery to 
    # return an appropiate init_ctx.
    # TODO TODO TODO TODO
    assert(func.public and func.name)
    
    data = ""
    return {"CALLDATA": func.name + data}, 100

def analyze_call_from_ep(entry_point, target_call_info):

    init_ctx, max_calldatasize = get_init_ctx_for(entry_point)
    
    # HACK 
    init_ctx = {"CALLDATA": "0x7da1083a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000aSSSSSSSSSSSSSSSSSSSS00000000000000000000000000"}
    
    # This is init_ctx for CallerTTU
    init_ctx = {"CALLDATA": "0x7214ae990000000000000000000000002fSS96349c51abfce8f7eb2326233f3eb387fa7b000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000SSSSSSSSSS00000000000000000000000000000000000000000000000000000000"}
    
    # This is a good init_ctx for JustTest002/JustTest001
    #init_ctx = {"CALLDATA": "0x7da1083a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000a000000SS00220000SS1100000000000000000000000000"}

    #init_ctx = {"CALLDATA": "0xe0ead80300000000000000000000000000000000000000000000000000000000000000SS"}
    max_calldatasize =  132

    # Some state options
    options.GREEDY_SHA = False
    #options.LAZY_SOLVES = True

    entry_state = p.factory.entry_state(xid=xid, init_ctx=init_ctx, max_calldatasize=max_calldatasize)    
    simgr = p.factory.simgr(entry_state=entry_state)
    
    #simgrviz = SimgrViz()
    #simgr.use_technique(simgrviz)
    
    dfs = DFS()
    simgr.use_technique(dfs)

    directed_search = DirectedSearch(p.factory.statement(target_call_info.call_stmt.id))
    simgr.use_technique(directed_search)

    heartbeat = HeartBeat()
    simgr.use_technique(heartbeat)

    log.info(f"Symbolically executing from {entry_point.id} to CALL at {target_call_info.call_stmt.id}")
    simgr.run(find=lambda s: s.curr_stmt.id == target_call_info.call_stmt.id)
    log.info(f"✅ Found state for CALL at {target_call_info.call_stmt.id}!")

    for state in simgr.found:
        assert(state.solver.frame==0)
        tainted_targetContract, tatined_targetFunc = analyze_state_at_call(state, target_call_info)
        target_call_info.taintedContractAddress = tainted_targetContract
        target_call_info.taintedFunction = tatined_targetFunc

# Here we want to understand from which function
# it is possible to reach this specific CALL statement. 
# Returns a list of entry-points that can reach the CALL.
def how_to_reach(p: Project, target_call:TAC_Statement):
    
    # TODO: if function is guarded, we should abort it, or, find 
    # if there is another contract that owns this specific contract.
    # basically reversing the chain even more.

    target_function = p.factory.block(target_call.block_id).function
    # If the function containing the CALL is public we are done.
    if target_function.public:
        return [target_function]

    # Otherwise, we need to find the entry points that lead to this CALL
    # using the callgraph.
    # To do that, we start from all the public functions, and see if they 
    # can reach the function.id of the CALL under analysis.
    possible_entry_points = [f for f in p.function_at.values() if f.public and f.id != '0x0']
    entry_points = set()
    for ep in possible_entry_points:
        if nx.has_path(p.callgraph, source=ep, target=target_function):
            entry_points.add(ep)
    
    return entry_points

CallInfos = dict()

if __name__ == "__main__":
    p = Project(target_dir=sys.argv[1])
    xid = gen_exec_id()


    # First of all, let's find all the CALL statements
    CallInfos = {s.id:CallInfo(s) for s in p.statement_at.values() if s.__internal_name__ == "CALL"}

    # Collect static information that can be useful for symbolic execution 
    # and for the classification of the CALL.
    for c_id, call in CallInfos.items():
        # [1] 
        # In the simplest case, the contract address should have been already 
        # propagated by Gigahorse, if this is statically known, in these cases
        # just grab it.
        contractAddress = None
        if call.call_stmt.arg2_val:
            contractAddress = call.call_stmt.arg2_val.value
        if contractAddress:
            log.info(f"CALL at {c_id} calls into contract address at {hex(contractAddress)}")
            CallInfos[c_id].taintedContractAddress = False
            CallInfos[c_id].contractAddresses.append(contractAddress)

        # [2]
        # Let's see if the CALL is reading its parameters from a statically known offset,
        # this can be helpful later to pre-constraint some symbolic variables.
        argOffset = None
        if call.call_stmt.arg4_val:
            argOffset = call.call_stmt.arg4_val.value
        if argOffset:
            log.info(f"CALL at {c_id} expect argOffset at {hex(argOffset)}")
            CallInfos[c_id].argsOffsets.append(argOffset)

        # [3]
        # Finally, let's check for known argsSize
        argSize = None
        if call.call_stmt.arg5_val:
            argSize = call.call_stmt.arg5_val.value
        if argSize:
            log.info(f"CALL at {c_id} expect argSize {hex(argSize)}")
            CallInfos[c_id].argsSizes.append(argSize)

        # [4] 
        # Entry points in the contract to reach this CALL
        entry_points = how_to_reach(p, call.call_stmt)

        if not len(entry_points):
            log.warning(f"Cannot find an entry point for CALL {call}. Skipping it.")
            continue
        
        for ep in entry_points:
            analyze_call_from_ep(ep, call)

    log.info("CALLS SUMMARY")
    for call in CallInfos.values():
        log.info(" 📞 "+str(call))


    import ipdb; ipdb.set_trace()

    

