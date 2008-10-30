"Code generation for the UFC 1.0 format with DOLFIN"

__author__ = "Anders Logg (logg@simula.no)"
__date__ = "2007-03-24 -- 2008-10-23"
__copyright__ = "Copyright (C) 2007-2008 Anders Logg"
__license__  = "GNU GPL version 3 or any later version"

# Modified by Kristian B. Oelgaard 2008
# Modified by Dag Lindbo, 2008

# Python modules
import os

# UFC code templates
from ufc import *

# FFC common modules
from ffc.common.utils import *
from ffc.common.debug import *
from ffc.common.constants import *

# FFC language modules
from ffc.compiler.language.restriction import *
from ffc.compiler.language.integral import *
from ffc.compiler.language.algebra import *

# FFC format modules
import ufcformat

# Specify formatting for code generation
format = ufcformat.format

def init(options):
    "Initialize code generation for given options"
    ufcformat.init(options)

def write(generated_forms, prefix, options):
    "Generate UFC 1.0 code with DOLFIN wrappers for a given list of pregenerated forms"

    # Strip directory names from prefix and add output directory
    prefix = prefix.split(os.path.join(' ',' ').split()[0])[-1]
    full_prefix = os.path.join(options["output_dir"], prefix)
    
    # Generate code for header
    output = ""
    output += generate_header(prefix, options)
    output += "\n"

    if not options["split_implementation"]:

        debug("Generating code for UFC 1.0 with DOLFIN wrappers")

        # Generate UFC code
        output += ufcformat.generate_ufc(generated_forms, "UFC_" + prefix, options, "combined")

        # Generate code for DOLFIN wrappers
        output += _generate_dolfin_wrappers(generated_forms, prefix, options)

        # Generate code for footer
        output += generate_footer(prefix, options)

        # Write file
        filename = "%s.h" % full_prefix
        file = open(filename, "w")
        file.write(output)
        file.close()
        debug("Output written to " + filename)

    else:
        
        debug("Generating code for UFC 1.0 with DOLFIN wrappers, split header and implementation")

        # UFC declarations and DOLFIN wrappers ---------------------------------

        # Generate UFC code
        output += ufcformat.generate_ufc(generated_forms, "UFC_" + prefix, options, "header")

        # Generate code for DOLFIN wrappers
        output += _generate_dolfin_wrappers(generated_forms, prefix, options)

        # Generate code for footer
        output += generate_footer(prefix, options)

        # Write file
        filename = "%s.h" % full_prefix
        file = open(filename, "w")
        file.write(output)
        file.close()
        debug("Output written to " + filename)

        # UFC implementations --------------------------------------------------
        output = ""
        output += "#include \"%s.h\""%prefix

        # Generate UFC code
        output += ufcformat.generate_ufc(generated_forms, "UFC_" + prefix, options, "implementation")

        # Write file
        filename = "%s.cpp" % full_prefix
        file = open(filename, "w")
        file.write(output)
        file.close()
        debug("Output written to " + filename)

def generate_header(prefix, options):
    "Generate file header"

    # Check if BLAS is required
    if options["blas"]:
        blas_include = "\n#include <cblas.h>"
        blas_warning = "\n// Warning: This code was generated with '-f blas' and requires cblas.h."
    else:
        blas_include = ""
        blas_warning = ""
        
    return """\
// This code conforms with the UFC specification version 1.0
// and was automatically generated by FFC version %s.%s
//
// Warning: This code was generated with the option '-l dolfin'
// and contains DOLFIN-specific wrappers that depend on DOLFIN.

#ifndef __%s_H
#define __%s_H

#include <cmath>
#include <stdexcept>
#include <fstream>
#include <ufc.h>%s
""" % (FFC_VERSION, blas_warning, prefix.upper(), prefix.upper(), blas_include)

def generate_footer(prefix, options):
    "Generate file footer"
    return """\
#endif
"""

def _generate_dolfin_wrappers(generated_forms, prefix, options):
    "Generate code for DOLFIN wrappers"

    output = """\
// DOLFIN wrappers

#include <dolfin/fem/Form.h>
#include <dolfin/fem/FiniteElement.h>
#include <dolfin/fem/DofMap.h>
#include <dolfin/function/Coefficient.h>
#include <dolfin/function/Function.h>
#include <dolfin/function/FunctionSpace.h>

"""
    
    # We generate two versions of all constructors, one using references (_r)
    # and one using shared pointers (_s)

    add_function_space_r = """\
    std::tr1::shared_ptr<dolfin::FunctionSpace> _V%d(&V%d, dolfin::NoDeleter<dolfin::FunctionSpace>());
    _function_spaces.push_back(_V%d);"""

    add_function_space_s = """\
    _function_spaces.push_back(V%d);"""

    add_coefficient_r =  """\
    _coefficients.push_back(std::tr1::shared_ptr<dolfin::Function>(static_cast<dolfin::Function*>(0)));"""

    add_coefficient_s =  """\
    _coefficients.push_back(std::tr1::shared_ptr<dolfin::Function>(static_cast<dolfin::Function*>(0)));"""

    # Extract common test space if any
    test_element = None
    test_elements = [form_data.elements[0] for (form_code, form_data) in generated_forms if form_data.rank >= 1]
    if len(test_elements) > 0 and test_elements[1:] == test_elements[:-1]:
        test_element = test_elements[0]
    elif len(test_elements) > 0:
        raise RuntimeError, "Unable to extract test space (not uniquely defined)."

    # Extract common trial element if any
    trial_element = None
    trial_elements = [form_data.elements[0] for (form_code, form_data) in generated_forms if form_data.rank >= 1]
    if len(trial_elements) > 0 and trial_elements[1:] == trial_elements[:-1]:
        trial_element = trial_elements[0]
    elif len(trial_elements) > 0:
        raise RuntimeError, "Unable to extract trial space (not uniquely defined)."

    # Extract common coefficient element if any
    coefficient_element = None
    coefficients = [c for (form_code, form_data) in generated_forms for c in form_data.coefficients]
    coefficient_elements = []
    for c in coefficients:
        coefficient_elements.append(c.e0)
    if len(coefficient_elements) > 0 and coefficient_elements[1:] == coefficient_elements[:-1]:
        coefficient_element = coefficient_elements[0]

    # Extract common element if any
    common_element = None
    elements = test_elements + trial_elements + coefficient_elements
    if len(elements) > 0 and elements[1:] == elements[:-1]:
        common_element = elements[-1]

    # Build map from elements to forms
    element_map = {}    
    for i in range(len(generated_forms)):
        (form_code, form_data) = generated_forms[i]
        form_prefix = ufcformat.compute_prefix(prefix, generated_forms, i, options)
        for j in range(len(form_data.elements)):
            element_map[form_data.elements[j]] = (form_prefix, j)

    # Generate code for function spaces
    for i in range(len(generated_forms)):
        (form_code, form_data) = generated_forms[i]
        form_prefix = ufcformat.compute_prefix(prefix, generated_forms, i, options)
        for j in range(form_data.rank):
            output += _generate_function_space(form_data.elements[j],
                                               "%sArgumentSpace%d" % (form_prefix, j),
                                               element_map)
            output += "\n"
        for j in range(form_data.num_coefficients):
            output += _generate_function_space(form_data.elements[form_data.rank + j],
                                               "%sCoefficientSpace%d" % (form_prefix, j),
                                               element_map)
            output += "\n"

    # Generate code for special function spaces
    if not test_element is None:
        output += _generate_function_space(test_element, prefix + "TestSpace", element_map) + "\n"
    if not trial_element is None:
        output += _generate_function_space(trial_element, prefix + "TrialSpace", element_map) + "\n"
    if not common_element is None:
        output += _generate_function_space(common_element, prefix + "FunctionSpace", element_map) + "\n"

    # Generate wrappers for all forms
    element_map = {}
    for i in range(len(generated_forms)):

        (form_code, form_data) = generated_forms[i]
        form_prefix = ufcformat.compute_prefix(prefix, generated_forms, i, options)

        # Generate code for coefficient member variables
        coefficient_names = [c.name() for c in form_data.coefficients]
        n = len(coefficient_names)
        coefficient_classes = ["%sCoefficient%d" % (form_prefix, j) for j in range(n)]
        if n == 0:
            coefficient_members = ""
        else:
            coefficient_members = "\n  //Coefficients\n" + "\n".join(["  %s %s;" % (coefficient_classes[j], coefficient_names[j]) for j in range(n)]) + "\n"

        # Generate code for initialization of coefficients
        if n == 0:
            coefficient_init = ""
        else:
            coefficient_init = ", " + ", ".join(["%s(*this)" % coefficient_names[j] for j in range(n)])

        # Generate code for coefficient classes
        for j in range(n):
            output += """\
class %s : public dolfin::Coefficient
{
public:

  // Constructor
  %s(dolfin::Form& form) : dolfin::Coefficient(form) {}

  // Destructor  
  ~%s() {}

  // Attach function to coefficient
  const %s& operator= (dolfin::Function& v)
  {
    attach(v);
    return *this;
  }

  /// Create function space for coefficient
  const dolfin::FunctionSpace* create_function_space() const
  {
    return new %sCoefficientSpace%d(form.mesh());
  }
  
  /// Return coefficient number
  dolfin::uint number() const
  {
    return %d;
  }
  
  /// Return coefficient name
  virtual std::string name() const
  {
    return "%s";
  }
  
};

""" % (coefficient_classes[j], coefficient_classes[j], coefficient_classes[j], coefficient_classes[j],
       form_prefix, j, j, coefficient_names[j])

        # Generate constructors
        constructor_args_r  = ", ".join(["dolfin::FunctionSpace& V%d" % k for k in range(form_data.rank)])
        constructor_args_s  = ", ".join(["std::tr1::shared_ptr<dolfin::FunctionSpace> V%d" % k for k in range(form_data.rank)])
        constructor_body_r  = "\n".join([add_function_space_r % (k, k, k) for k in range(form_data.rank)])
        constructor_body_s  = "\n".join([add_function_space_s % k for k in range(form_data.rank)])
        if form_data.rank > 0:
            constructor_body_r += "\n\n"
            constructor_body_s += "\n\n"
        constructor_body_r += "\n".join([add_coefficient_r for k in range(form_data.num_coefficients)])
        constructor_body_s += "\n".join([add_coefficient_s for k in range(form_data.num_coefficients)])
        if form_data.num_coefficients > 0:
            constructor_body_r += "\n\n"
            constructor_body_s += "\n\n"
        constructor_body_r += "    _ufc_form = new UFC_%s();\n\n" % form_prefix
        constructor_body_s += "    _ufc_form = new UFC_%s();\n\n" % form_prefix
        output += """\
class %s : public dolfin::Form
{
public:

  // Constructor
  %s(%s) : dolfin::Form()%s
  {
%s
  }

  // Constructor
  %s(%s) : dolfin::Form()%s
  {
%s
  }

  // Destructor
  ~%s() {}
%s
};

""" % (form_prefix,
       form_prefix, constructor_args_r, coefficient_init, constructor_body_r,
       form_prefix, constructor_args_s, coefficient_init, constructor_body_s,
       form_prefix, coefficient_members)

    return output

def _generate_function_space(element, classname, element_map):
    "Generate code for function space"

    function_space_class = """\
class %s : public dolfin::FunctionSpace
{
public:

  %s(const dolfin::Mesh& mesh)
    : dolfin::FunctionSpace(std::tr1::shared_ptr<const dolfin::Mesh>(&mesh, dolfin::NoDeleter<const dolfin::Mesh>()),
                            std::tr1::shared_ptr<const dolfin::FiniteElement>(new dolfin::FiniteElement(std::tr1::shared_ptr<ufc::finite_element>(new %s()))),
                            std::tr1::shared_ptr<const dolfin::DofMap>(new dolfin::DofMap(std::tr1::shared_ptr<ufc::dof_map>(new %s()), mesh)))
  {
    // Do nothing
  }

};
"""
    
    (form_prefix, element_number) = element_map[element]
    element_class = "UFC_%s_finite_element_%d" % (form_prefix, element_number)
    dofmap_class = "UFC_%s_dof_map_%d" % (form_prefix, element_number)
    return function_space_class % (classname, classname, element_class, dofmap_class)
