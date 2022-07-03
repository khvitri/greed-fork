from SEtaac import utils
from SEtaac.utils.exceptions import VMExternalData, VMSymbolicError, VMException
from SEtaac.utils.solver.shortcuts import *
from .base import TAC_Statement
from ..state import SymbolicEVMState

__all__ = ['TAC_Sha3', 'TAC_Address', 'TAC_Balance', 'TAC_Origin', 'TAC_Caller',
           'TAC_Callvalue', 'TAC_Calldataload', 'TAC_Calldatasize', 'TAC_Calldatacopy',
           'TAC_Codesize', 'TAC_Codecopy', 'TAC_Gasprice', 'TAC_Extcodesize', 'TAC_Extcodecopy',
           'TAC_Returndatasize', 'TAC_Returndatacopy', 'TAC_Extcodehash', 'TAC_Blockhash', 'TAC_Coinbase',
           'TAC_Timestamp', 'TAC_Number', 'TAC_Difficulty', 'TAC_Chainid', 'TAC_Gaslimit', 'TAC_Selfbalance',
           'TAC_Basefee', 'TAC_Create', 'TAC_Create2', 'TAC_Revert', 'TAC_Pc', 'TAC_Invalid', 'TAC_Selfdestruct',
           'TAC_Stop', 'TAC_Gas']


class TAC_Sha3(TAC_Statement):
    __internal_name__ = "SHA3"
    __aliases__ = {'offset_var': 'arg1_var', 'offset_val': 'arg1_val',
                   'size_var': 'arg2_var', 'size_val': 'arg2_val',
                   'hash_var': 'res_var', 'hash_val': 'res_val'}

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        raise Exception("NOT IMPLEMENTED. Please have a look")

        # succ = state
        #
        # succ.memory.extend(self.offset_val, self.size_val)
        # mm = succ.memory.read(self.offset_val, self.size_val)
        # if not isinstance(mm, SymRead) and all(concrete(m) for m in mm):
        #     data = utils.bytearray_to_bytestr(mm)
        #     succ.registers[self.res1_var] = utils.big_endian_to_int(utils.sha3(data))
        # else:
        #     if not isinstance(mm, SymRead):
        #         sha_data = BV_Concat([m for m in mm])
        #         for k, v in succ.sha_constraints.items():
        #             if isinstance(v, SymRead):
        #                 continue
        #             if v.size() == sha_data.size() and is_true(v == sha_data):
        #                 sha = k
        #                 break
        #         else:
        #             sha = BVS(f'SHA3_{succ.instruction_count}_{succ.xid}', 256)
        #             succ.sha_constraints[sha] = sha_data
        #     else:
        #         sha_data = mm
        #         sha = BVS(f'SHA3_{succ.instruction_count}_{succ.xid}', 256)
        #         succ.sha_constraints[sha] = sha_data
        #     succ.registers[self.res1_var] = sha
        #
        # succ.set_next_pc()
        # return [succ]


class TAC_Stop(TAC_Statement):
    __internal_name__ = "STOP"

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        # todo: implement revert
        # succ.constraints.append(z3.Or(*(z3.ULE(succ.calldatasize, access) for access in succ.calldata_accesses)))
        succ.halt = True

        return [succ]


class TAC_Address(TAC_Statement):
    __internal_name__ = "ADDRESS"
    __aliases__ = {'address_var': 'res_var', 'address_val': 'res_val'}

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = ctx_or_symbolic('ADDRESS', succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Balance(TAC_Statement):
    __internal_name__ = "BALANCE"
    __aliases__ = {
        'address_var': 'arg1_var', 'address_val': 'arg1_val',
        'balance_var': 'res_var', 'balance_val': 'res_val'
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        s = new_solver_context()
        if is_concrete(self.address_val):
            succ.registers[self.res1_var] = ctx_or_symbolic('BALANCE-%x' % bv_unsigned_value(self.address_val), succ.ctx, succ.xid)
        elif s.is_formula_true(Equal(utils.addr(self.address_val), utils.addr(ctx_or_symbolic('ADDRESS', succ.ctx, succ.xid)))):
            succ.registers[self.res1_var] = self.balance
        elif s.is_formula_true(Equal(utils.addr(self.address_val), utils.addr(ctx_or_symbolic('ORIGIN', succ.ctx, succ.xid)))):
            succ.registers[self.res1_var] = ctx_or_symbolic('BALANCE-ORIGIN', succ.ctx, succ.xid)
        elif s.is_formula_true(Equal(utils.addr(self.address_val), utils.addr(ctx_or_symbolic('CALLER', succ.ctx, succ.xid)))):
            succ.registers[self.res1_var] = ctx_or_symbolic('BALANCE-CALLER', succ.ctx, succ.xid)
        else:
            raise VMSymbolicError('balance of symbolic address (%s)' % str(self.address_val))

        succ.set_next_pc()
        return [succ]


class TAC_Origin(TAC_Statement):
    __internal_name__ = "ORIGIN"
    __aliases__ = {'address_var': 'res_var', 'address_val': 'res_val'}

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = ctx_or_symbolic('ORIGIN', succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Caller(TAC_Statement):
    __internal_name__ = "CALLER"
    __aliases__ = {'address_var': 'res_var', 'address_val': 'res_val'}

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = ctx_or_symbolic('CALLER', succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Callvalue(TAC_Statement):
    __internal_name__ = "CALLVALUE"
    __aliases__ = {'value_var': 'res_var', 'value_val': 'res_val'}

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = ctx_or_symbolic('CALLVALUE', succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Calldataload(TAC_Statement):
    __internal_name__ = "CALLDATALOAD"
    __aliases__ = {'byte_offset_var': 'arg1_var', 'byte_offset_val': 'arg1_val',
                   'calldata_var': 'res_var', 'calldata_val': 'res_val'}

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.constraints.append(BV_UGE(succ.calldatasize, BV_Add(self.byte_offset_val, BVV(32, 256))))
        # succ.calldata_accesses.append(BV_Add(self.byte_offset_val, BVV(32, 256)))
        if not is_concrete(self.byte_offset_val):
            succ.constraints.append(BV_ULT(self.byte_offset_val, BVV(succ.MAX_CALLDATA_SIZE, 256)))
        succ.registers[self.res1_var] = BV_Concat([Array_Select(succ.calldata, BV_Add(self.byte_offset_val, BVV(i, 256))) for i in range(32)])

        succ.set_next_pc()
        return [succ]


class TAC_Calldatasize(TAC_Statement):
    __internal_name__ = "CALLDATASIZE"
    __aliases__ = {'calldatasize_var': 'res_var', 'calldatasize_val': 'res_val'}

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = succ.calldatasize

        succ.set_next_pc()
        return [succ]


class TAC_Calldatacopy(TAC_Statement):
    __internal_name__ = "CALLDATACOPY"
    __aliases__ = {
        'destOffset_var': 'arg1_var', 'destOffset_val': 'arg1_val',
        'calldataOffset_var': 'arg2_var', 'calldataOffset_val': 'arg2_val',
        'size_var': 'arg3_var', 'size_val': 'arg3_val',
    }

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.constraints.append(BV_UGE(succ.calldatasize, BV_Add(self.calldataOffset_val, self.size_val)))
        # succ.calldata_accesses.append(BV_Add(self.calldataOffset_val, self.size_val))
        if not is_concrete(self.calldataOffset_val):
            succ.constraints.append(BV_ULT(self.calldataOffset_val, BVV(succ.MAX_CALLDATA_SIZE, 256)))
        if not is_concrete(self.size_val):
            succ.constraints.append(BV_ULT(self.size_val, BVV(succ.MAX_CALLDATA_SIZE, 256)))
        for i in range(succ.MAX_CALLDATA_SIZE):
            destOffset_plus_i = BV_Add(self.destOffset_val, BVV(i, 256))
            calldataOffset_plus_i = BV_Add(self.calldataOffset_val, BVV(i, 256))
            succ.memory[destOffset_plus_i] = If(BV_ULT(self.size_val, BVV(i, 256)),
                                                succ.memory[destOffset_plus_i],
                                                Array_Select(succ.calldata, calldataOffset_plus_i))

        succ.set_next_pc()
        return [succ]


class TAC_Codesize(TAC_Statement):
    __internal_name__ = "CODESIZE"
    __aliases__ = {
        'size_var': 'arg1_var', 'size_val': 'arg1_val'
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = len(succ.code)

        succ.set_next_pc()
        return [succ]


class TAC_Codecopy(TAC_Statement):
    __internal_name__ = "CODECOPY"
    __aliases__ = {
        'destOffset_var': 'arg1_var', 'destOffset_val': 'arg1_val',
        'offset_var': 'arg2_var', 'offset_val': 'arg2_val',
        'size_var': 'arg3_var', 'size_val': 'arg3_val'
    }

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        if is_concrete(self.destOffset_val) and is_concrete(self.offset_val) and is_concrete(self.size_val):
            for i in range(bv_unsigned_value(self.size_val)):
                if bv_unsigned_value(self.offset_val) + i < len(succ.code):
                    succ.memory[bv_unsigned_value(self.destOffset_val) + i] = succ.code[bv_unsigned_value(self.offset_val) + i]
                else:
                    succ.memory[bv_unsigned_value(self.destOffset_val) + i] = 0
        else:
            raise VMSymbolicError('Symbolic code index @ %s' % succ.pc)

        succ.set_next_pc()
        return [succ]


class TAC_Gasprice(TAC_Statement):
    __internal_name__ = "GASPRICE"
    __aliases__ = {
        'price_var': 'res_var', 'price_val': 'res_val'
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = ctx_or_symbolic('GASPRICE', succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Extcodesize(TAC_Statement):
    __internal_name__ = "EXTCODESIZE"
    __aliases__ = {
        'address_var': 'arg1_var', 'address_val': 'arg1_val',
        'size_var': 'res_var', 'size_val': 'res_val'
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        s = new_solver_context()
        if is_concrete(self.address_val):
            succ.registers[self.res1_var] = ctx_or_symbolic('CODESIZE-%x' % bv_unsigned_value(self.address_val), succ.ctx, succ.xid)
        elif s.is_formula_true(Equal(self.address_val, utils.addr(ctx_or_symbolic('ADDRESS', succ.ctx, succ.xid)))):
            succ.registers[self.res1_var] = ctx_or_symbolic('CODESIZE-ADDRESS', succ.ctx, succ.xid)
        elif s.is_formula_true(Equal(self.address_val, utils.addr(ctx_or_symbolic('CALLER', succ.ctx, succ.xid)))):
            succ.registers[self.res1_var] = ctx_or_symbolic('CODESIZE-CALLER', succ.ctx, succ.xid)
        else:
            raise VMSymbolicError('codesize of symblic address')

        succ.set_next_pc()
        return [succ]


class TAC_Extcodecopy(TAC_Statement):
    __internal_name__ = "EXTCODECOPY"
    __aliases__ = {
        'address_var': 'arg1_var', 'address_val': 'arg1_val',
        'destOffset_var': 'arg2_var', 'destOffset_val': 'arg2_val',
        'offset_var': 'arg3_var', 'offset_val': 'arg3_val',
        'size_var': 'arg4_var', 'size_val': 'arg4_val'
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        raise VMExternalData('EXTCODECOPY')


class TAC_Returndatasize(TAC_Statement):
    __internal_name__ = "RETURNDATASIZE"
    __aliases__ = {
        'size_var': 'res_var', 'size_val': 'res_val'
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        raise VMExternalData('RETURNDATASIZE')


class TAC_Returndatacopy(TAC_Statement):
    __internal_name__ = "RETURNDATACOPY"
    __aliases__ = {
        'destOffset_var': 'arg1_var', 'destOffset_val': 'arg1_val',
        'offset_var': 'arg2_var', 'offset_val': 'arg2_val',
        'size_var': 'arg3_var', 'size_val': 'arg3_val'
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        raise VMExternalData('RETURNDATACOPY')


class TAC_Extcodehash(TAC_Statement):
    __internal_name__ = "EXTCODEHASH"
    __aliases__ = {
        'address_var': 'arg1_var', 'address_val': 'arg1_val',
        'hash_var': 'res_var', 'hash_val': 'res_val'
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        raise VMExternalData('EXTCODEHASH')


class TAC_Blockhash(TAC_Statement):
    __internal_name__ = "BLOCKHASH"
    __aliases__ = {
        'blockNumber_var': 'arg1_var', 'blockNumber_val': 'arg1_val',
        'hash_var': 'res_var', 'hash_val': 'res_val'
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        if not is_concrete(self.blockNumber_val):
            raise VMSymbolicError('symbolic blockhash index')
        succ.registers[self.res1_var] = ctx_or_symbolic('BLOCKHASH[%d]' % bv_unsigned_value(self.blockNumber_val), succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Coinbase(TAC_Statement):
    __internal_name__ = "COINBASE"
    __aliases__ = {
        'address_var': 'res_var', 'address_val': 'res_val',
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = ctx_or_symbolic('COINBASE', succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Timestamp(TAC_Statement):
    __internal_name__ = "TIMESTAMP"
    __aliases__ = {
        'timestamp_var': 'res_var', 'timestamp_val': 'res_val',
    }

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        ts = ctx_or_symbolic('TIMESTAMP', succ.ctx, succ.xid)
        if not is_concrete(ts):
            succ.constraints.append(BV_UGE(ts, succ.min_timestamp))
            succ.constraints.append(BV_ULE(ts, succ.max_timestamp))
        succ.registers[self.res1_var] = ts

        succ.set_next_pc()
        return [succ]


class TAC_Number(TAC_Statement):
    __internal_name__ = "NUMBER"
    __aliases__ = {
        'blockNumber_var': 'res_var', 'blockNumber_val': 'res_val',
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = ctx_or_symbolic('NUMBER', succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Difficulty(TAC_Statement):
    __internal_name__ = "DIFFICULTY"
    __aliases__ = {
        'difficulty_var': 'res_var', 'difficulty_val': 'res_val',
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = ctx_or_symbolic('DIFFICULTY', succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Gaslimit(TAC_Statement):
    __internal_name__ = "GASLIMIT"
    __aliases__ = {
        'gasLimit_var': 'res_var', 'gasLimit_val': 'res_val',
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = ctx_or_symbolic('GASLIMIT', succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Chainid(TAC_Statement):
    __internal_name__ = "CHAINID"
    __aliases__ = {
        'chainID_var': 'res_var', 'chainID_val': 'res_val',
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        chainid = {'mainnet': 1, 'ropsten': 3, 'rinkeby': 4, 'goerli': 5, 'kotti': 6, 'classic': 61, 'mordor': 63,
                   'astor': 212, 'dev': 2018}
        succ.registers[self.res1_var] = chainid['mainnet']

        succ.set_next_pc()
        return [succ]


class TAC_Selfbalance(TAC_Statement):
    __internal_name__ = "SELFBALANCE"
    __aliases__ = {
        'balance_var': 'res_var', 'balance_val': 'res_val',
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = succ.balance

        succ.set_next_pc()
        return [succ]


class TAC_Basefee(TAC_Statement):
    __internal_name__ = "BASEFEE"
    __aliases__ = {
        'baseFee_var': 'res_var', 'baseFee_val': 'res_val',
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        # todo: if the current block is known, this is known
        succ.registers[self.res1_var] = ctx_or_symbolic('BASEFEE', succ.ctx, succ.xid)

        succ.set_next_pc()
        return [succ]


class TAC_Revert(TAC_Statement):
    __internal_name__ = "REVERT"
    __aliases__ = {
        'offset_var': 'arg1_var', 'offset_val': 'arg1_val',
        'size_var': 'arg2_var', 'size_val': 'arg2_val',
    }

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        if not is_concrete(self.offset_val) or not is_concrete(self.size_val):
            raise VMSymbolicError('symbolic memory index')
        # succ.constraints.append(BV_Or(*(BV_ULE(succ.calldatasize, access) for access in succ.calldata_accesses)))
        succ.revert = True
        succ.halt = True

        # succ.set_next_pc()
        return [succ]


class TAC_Create(TAC_Statement):
    __internal_name__ = "CREATE"
    __aliases__ = {
        'value_var': 'arg1_var', 'value_val': 'arg1_val',
        'offset_var': 'arg2_var', 'offset_val': 'arg2_val',
        'size_var': 'arg3_var', 'size_val': 'arg3_val',
        'address_var': 'res_var', 'address_val': 'res_val'
    }

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.constraints.append(z3.UGE(succ.balance, self.value_val))
        succ.balance -= self.value_val
        succ.registers[self.res1_var] = utils.addr(
            z3.BitVec('EXT_CREATE_%d_%d' % (succ.instruction_count, succ.xid), 256))

        succ.set_next_pc()
        return [succ]


class TAC_Create2(TAC_Statement):
    __internal_name__ = "CREATE2"
    __aliases__ = {
        'value_var': 'arg1_var', 'value_val': 'arg1_val',
        'offset_var': 'arg2_var', 'offset_val': 'arg2_val',
        'size_var': 'arg3_var', 'size_val': 'arg3_val',
        'salt_var': 'arg4_var', 'salt_val': 'arg4_val',
        'address_var': 'res_var', 'address_val': 'res_val'
    }

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.constraints.append(z3.UGE(succ.balance, self.value_val))
        succ.balance -= self.value_val
        # todo: this is deployed at a deterministic address
        succ.registers[self.res1_var] = utils.addr(
            z3.BitVec('EXT_CREATE2_%d_%d' % (succ.instruction_count, succ.xid), 256))

        succ.set_next_pc()
        return [succ]


class TAC_Pc(TAC_Statement):
    __internal_name__ = "PC"
    __aliases__ = {
        'counter_var': 'res_var', 'counter_val': 'res_val',
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        # todo: this pc will most probably be different from what the evm expects
        raise VMException("PC not available if executing TAC")

        # succ = state
        # succ.registers[self.res_var] = succ.pc

        # succ.set_next_pc()
        # return [succ]


class TAC_Invalid(TAC_Statement):
    __internal_name__ = "INVALID"

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.halt = True

        return [succ]


class TAC_Selfdestruct(TAC_Statement):
    __internal_name__ = "SELFDESTRUCT"
    __aliases__ = {
        'address_var': 'arg1_var', 'address_val': 'arg1_val'
    }

    @TAC_Statement.handler_with_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        # todo: consider the target address
        # succ.constraints.append(z3.Or(*(z3.ULE(succ.calldatasize, access) for access in succ.calldata_accesses)))
        succ.halt = True

        return [succ]


class TAC_Gas(TAC_Statement):
    __internal_name__ = "GAS"
    __aliases__ = {
        'gas_var': 'res_var', 'gas_val': 'res_val'
    }

    @TAC_Statement.handler_without_side_effects
    def handle(self, state: SymbolicEVMState):
        succ = state

        succ.registers[self.res1_var] = z3.BitVec('GAS_%x' % succ.instruction_count, 256)

        succ.set_next_pc()
        return [succ]
