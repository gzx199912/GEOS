/*
 * ------------------------------------------------------------------------------------------------------------
 * SPDX-License-Identifier: LGPL-2.1-only
 *
 * Copyright (c) 2018-2020 Lawrence Livermore National Security LLC
 * Copyright (c) 2018-2020 The Board of Trustees of the Leland Stanford Junior University
 * Copyright (c) 2018-2020 TotalEnergies
 * Copyright (c) 2019-     GEOSX Contributors
 * All rights reserved
 *
 * See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
 * ------------------------------------------------------------------------------------------------------------
 */

/**
 * @file ConstantViscosity.cpp
 */

#include "ConstantViscosity.hpp"

namespace geos
{

namespace constitutive
{

namespace compositional
{

ConstantViscosity::ConstantViscosity( string const & name,
                                      ComponentProperties const & componentProperties ):
  FunctionBase( name, componentProperties )
{}

ConstantViscosity::KernelWrapper
ConstantViscosity::createKernelWrapper() const
{
  return KernelWrapper( );
}

} // end namespace compositional

} // namespace constitutive

} // end namespace geos
