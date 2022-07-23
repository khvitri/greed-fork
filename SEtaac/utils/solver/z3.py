import z3

from SEtaac.utils.solver.base import Solver


class Z3(Solver):
    """
    This is a singleton class, and all methods are static
    """

    def __init__(self):
        self.solver = z3.SolverFor('QF_ABV')
        self.BVSort_cache = dict()
        self.BVV_cache = dict()
        self.BVS_cache = dict()

    def BVSort(self, width):
        if width not in self.BVSort_cache:
            self.BVSort_cache[width] = z3.BitVecSort(width)
        return self.BVSort_cache[width]

    def BVV(self, value, width):
        if (value, width) not in self.BVV_cache:
            self.BVV_cache[(value, width)] = z3.BitVecVal(value, width)
        return self.BVV_cache[(value, width)]

    def BVS(self, symbol, width):
        if (symbol, width) not in self.BVS_cache:
            self.BVS_cache[(symbol, width)] = z3.BitVec(symbol, width)
        return self.BVS_cache[(symbol, width)]

    def bv_unsigned_value(self, bv):
        return int(bv.as_binary_string(), 2)

    def is_concrete(self, bv):
        return z3.is_const(bv)

    def is_sat(self, ):
        return self.solver.check() == z3.sat

    def is_unsat(self, ):
        return self.solver.check() == z3.unsat

    def is_sat_formula(self, formula):
        self.push()
        self.add_assertion(formula)
        sat = self.is_sat()
        self.pop()

        return sat

    def push(self, ):
        # Create a Z3 backtracking point
        self.solver.push()

    def pop(self, ):
        # Remove a Z3 backtracking point
        self.solver.pop()

    def add_assertion(self, formula):
        self.solver.add(formula)

    def add_assertions(self, formulas):
        self.solver.add(*formulas)

    def add_assumption(self, formula):
        raise Exception

    def add_assumptions(self, formulas):
        raise Exception

    def reset_assumptions(self, ):
        raise Exception

    def fixate_assumptions(self, ):
        raise Exception

    def simplify(self, ):
        # We need to pass a specific formula to simplify
        raise Exception

    def new_solver_context(self, ):
        return Z3

    def Array(self, symbol, index_sort, value_sort):
        return z3.Array(symbol, index_sort, value_sort)

    def ConstArray(self, symbol, index_sort, value_sort, default):
        raise Exception

    # CONDITIONAL OPERATIONS

    def If(self, cond, value_if_true, value_if_false):
        return z3.If(cond, value_if_true, value_if_false)

    # BOOLEAN OPERATIONS

    # def Equalself, (a, b):
    #    return self.solver.Eq(a, b)

    # def NotEqualself, (a, b):
    #    return self.solver.Ne(a, b)

    # def Orself, (a, b):
    #    return self.solver.Or(a, b)

    # def Andself, (a, b):
    #    return self.solver.And(a, b)

    # def Notself, (a):
    #    return self.solver.Not(a)

    # BV OPERATIONS

    def Equal(self, a, b):
        return z3.eq(a, b)

    def NotEqual(self, a, b):
        return z3.is_not(z3.eq(a, b))

    def BV_Extract(self, start, end, bv):
        # Z3 extract is (start_offset, length, symbol)
        return z3.Extract(start, (end-start), bv)

    def BV_Concat(self, terms):
        res = z3.Concat(terms[0], terms[1])
        for i in range(2, len(terms)):
            res = z3.Concat(res, terms[i])
        return res

    def BV_Add(self, a, b):
        return a + b

    def BV_Sub(self, a, b):
        return a - b

    def BV_Mul(self, a, b):
        return a * b

    def BV_UDiv(self, a, b):
        return z3.UDiv(a, b)

    def BV_SDiv(self, a, b):
        return a / b

    def BV_SMod(self, a, b):
        return a % b 

    def BV_SRem(self, a, b):
        return z3.SRem(a,b)

    def BV_URem(self, a, b):
        return z3.URem(a, b)

    def BV_Sign_Extend(self, a, b):
        return z3.SignExt(a, b)

    def BV_Zero_Extend(self, a, b):
        return z3.ZeroExt(a, b)

    def BV_UGE(self, a, b):
        return z3.UGE(a, b)

    def BV_ULE(self, a, b):
        return z3.ULE(a, b)

    def BV_UGT(self, a, b):
        return z3.UGT(a, b)

    def BV_ULT(self, a, b):
        return z3.ULT(a, b)

    def BV_SGE(self, a, b):
        return a >= b

    def BV_SLE(self, a, b):
        return a <= b

    def BV_SGT(self, a, b):
        return a > b

    def BV_SLT(self, a, b):
        return a < b

    def BV_And(self, a, b):
        return z3.And(a, b)

    def BV_Or(self, a, b):
        return z3.Or(a, b)

    def BV_Xor(self, a, b):
        return z3.Xor(a, b)

    def BV_Not(self, a):
        return z3.Not(a)

    def BV_Shl(self, a, b):
        return a >> b

    def BV_Shr(self, a, b):
        return a << b

    # ARRAY OPERATIONS

    def Array_Store(self, arr, index, elem):
        return z3.Store(arr, index, elem)

    def Array_Select(self, arr, index):
        return z3.Select(arr, index)

    def eval_one_array(self, array, length):
        self.is_sat()
        return [int(self.Array_Select(array, self.BVV(i, 256)).assignment, 2) for i in
                range(length)]
