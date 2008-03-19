"""This module contains utilities for computing signatures of
products. Signatures are used to uniquely identify reference
tensors that may be common to a group of terms."""

__author__ = "Anders Logg (logg@simula.no)"
__date__ = "2005-09-06 -- 2008-03-19"
__copyright__ = "Copyright (C) 2005-2008 Anders Logg"
__license__  = "GNU GPL version 3 or any later version"

# Modified by Kristian Oelgaard 2006

# Python modules
from re import sub

# FFC modules
from algebra import *
from tokens import *

def __index_signature(index):
    "Return unique signature for index, including range"
    if isinstance(index, Index):
        return str(index) + ", " + str(index.range)
    return str(index)

def compute_hard_signature(product):
    "Compute hard (unique) signature."
    
    # Create signature for numeric constant
    numeric = "%.15e" % product.numeric
    
    # Create signatures for basis functions
    factors = []
    for v in product.basisfunctions:
        factors += ["{%s;%s;%s;%s;%s}" % \
                    (str(v.element),     \
                     __index_signature(v.index), \
                     "[" + ", ".join([__index_signature(c) for c in v.component]) + "]",
                     "[" + ", ".join([str(d) for d in v.derivatives]) + "]",
                     str(v.restriction))]

    # Sort signatures for basis functions
    factors.sort()

    # Create signature for integral
    integral = str(product.integral)

    # Create signature for product
    return "*".join([numeric] + factors + [integral])

def compute_soft_signature(product):
    "Compute soft (modulo secondary index numbers) signature."

    # Compute hard signature
    signature = compute_hard_signature(product)

    # Ignore secondary index numbers
    return sub('a\d+', 'a', signature)
