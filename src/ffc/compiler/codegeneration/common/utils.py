"Code generation utils"

__author__ = "Anders Logg (logg@simula.no)"
__date__ = "2007-04-11 -- 2007-04-11"
__copyright__ = "Copyright (C) 2007 Anders Logg"
__license__  = "GNU GPL Version 2"

# Modified by Kristian Oelgaard 2007

# FFC common modules
from ffc.common.constants import *
import numpy

def inner_product(a, b, format):
    """Generate code for inner product of a and b, where a is a list
    of floating point numbers and b is a list of symbols."""

    # Check input
    if not len(a) == len(b):
        raise runtimeError, "Dimensions don't match for inner product."

    # Prefetch formats to speed up code generation
    format_add            = format["add"]
    format_subtract       = format["subtract"]
    format_multiply       = format["multiply"]
    format_floating_point = format["floating point"]
    
    # Add all entries
    value = None
    for i in range(len(a)):

        # Skip terms where a is almost zero
        if abs(a[i]) <= FFC_EPSILON:
            continue

        # Fancy handling of +, -, +1, -1
        if value:
            if abs(a[i] - 1.0) < FFC_EPSILON:
                value = format_add([value, b[i]])
            elif abs(a[i] + 1.0) < FFC_EPSILON:
                value = format_subtract([value, b[i]])
            elif a[i] > 0.0:
                value = format_add([value, format_multiply([format_floating_point(a[i]), b[i]])])
            else:
                value = format_subtract([value, format_multiply([format_floating_point(-a[i]), b[i]])])
        else:
            if abs(a[i] - 1.0) < FFC_EPSILON or abs(a[i] + 1.0) < FFC_EPSILON:
                value = b[i]
            else:
                value = format_multiply([format_floating_point(a[i]), b[i]])

    return value or format_floating_point(0.0)

def tabulate_matrix(matrix, Indent, format):
    "Function that tabulates the values of a matrix, into a two dimensional array."

    # Check input
    if not len(numpy.shape(matrix)) == 2:
        raise runtimeError, "This is not a matrix."

    # Prefetch formats to speed up code generation
    format_block          = format["block"]
    format_separator      = format["separator"]
    format_floating_point = format["floating point"]

    # Get size of array
    num_rows = numpy.shape(matrix)[0]
    num_cols = numpy.shape(matrix)[1]

    # Set matrix entries equal to zero if their absolute values is smaller than FFC_EPSILON
    for i in range(num_rows):
        for j in range(num_cols):
            if ( abs(matrix[i][j]) < FFC_EPSILON ):
                matrix[i][j] = 0.0

    # Generate array of values
    value = format["new line"] + format["block begin"]
    rows = []

    for i in range(num_rows):
        rows += [format_block(format_separator.join([format_floating_point(matrix[i,j])\
                 for j in range(num_cols)]))]

    value += format["block separator"].join(rows)
    value += format["block end"]

    return value
