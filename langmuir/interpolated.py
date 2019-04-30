"""
Copyright 2018
    Sigvald Marholm <marholm@marebakken.com>
    Diako Darian <diakod@math.uio.no>

This file is part of langmuir.

langmuir is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

langmuir is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with langmuir.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import division
from langmuir.tables import *
from langmuir.geometry import *
from langmuir.species import *
from langmuir.misc import *
from scipy.interpolate import griddata
from scipy.constants import value as constants
from copy import deepcopy
import scipy.special as special
import numpy as np
import os

def finite_radius_current(geometry, species, V=None, eta=None, normalize=False,
                          table='laframboise-darian-marholm'):
    """
    A current model taking into account the effects of finite radius by
    interpolating between tabulated normalized currents. The model only
    accounts for the attracted-species currents (for which eta<0). It does
    not extrapolate, but returns ``nan`` when the input parameters are outside
    the domain of the model. This happens when the normalized potential for any
    given species is less than -25, when kappa is less than 4, when alpha is
    more than 0.2 or when the radius is more than 10 or sometimes all the way
    up towards 100 (as the distribution approaches Maxwellian). Normally finite
    radius effects are negligible for radii less than 0.2 Debye lengths (spheres)
    or 1.0 Debye lengths (cylinders).

    The model can be based on the following tables, as decided by the ``table``
    parameter:

    - ``'laframboise'``.
      The de-facto standard tables for finite radius currents, tables 5c
      and 6c in Laframboise, "Theory of Spherical and Cylindrical Langmuir
      Probes in a Collisionless, Maxwellian Plasma at Rest", PhD Thesis.
      Covers Maxwellian plasmas only, probe radii ranging from 0 to 100 Debye
      lengths.

    - ``'darian-marholm uncomplete'``.
      These tables covers Maxwellian, Kappa, Cairns and Kappa-Cairns
      distributions for radii ranging from 0.2 Debye lengths (spheres) or
      1.0 Debye length (cylinders) up to 10 Debye lengths. They are not as
      accurate as ``'laframboise'`` for pure the Maxwellian, but usually within
      one or two percent.

    - ``'darian-marholm'``.
      Same as above, but this is complemented by adding analytical values from
      OML theory, thereby extending the range of valid radii down to zero Debye
      lengths. In addition, the values for zero potential are replaced by
      analytical values (i.e. the thermal current), since these are amongst the
      most inaccurate in the above, and more accurate values can be analytically
      computed.

    - ``'laframboise-darian-marholm'``.
      This replaces the tabulated values for the Maxwellian distribution in
      ``'darian-marholm'`` with those of Laframboise. Accordingly this table
      produces the most accurate result available in any situation, and has the
      widest available parameter domain, with the probe radius gradually
      increasing from 10 towards 100 Debye lengths as the distribution
      approaches the Maxwellian.

    Parameters
    ----------
    geometry: Plane, Cylinder or Sphere
        Probe geometry

    species: Species or list of Species
        Species constituting the background plasma

    V: float or float array
        Probe voltage(s) in volts

    eta: float or float array
        Normalized probe voltage(s), i.e. q*V/k*T, where q and T are the
        species' charge and temperature, k is Boltzmann's constant and V is
        the probe voltage in volts.

    normalize: bool
        Whether or not to normalize the output current by
        ``normalization_current()``

    table: string
        Which table to use for interpolation. See detailed description above.

    Returns
    -------
    float or float array of currents.
    """
    if isinstance(species, list):
        if normalize == True:
            logger.error('Cannot normalize current to more than one species')
            return None
        if eta is not None:
            logger.error('Cannot normalize voltage to more than one species')
            return None
        I = 0
        for s in species:
            I += finite_radius_current(geometry, s, V, eta, table=table)
        return I

    q, m, n, T = species.q, species.m, species.n, species.T
    kappa, alpha = species.kappa, species.alpha
    k = constants('Boltzmann constant')

    if V is not None:
        V = make_array(V)
        eta = q*V/(k*T)
    else:
        eta = make_array(eta)

    eta = deepcopy(eta)

    I = np.zeros_like(eta)

    indices_n = np.where(eta > 0)[0]   # indices for repelled particles
    indices_p = np.where(eta <= 0)[0]  # indices for attracted particles

    if normalize:
        I0 = 1
    else:
        I0 = normalization_current(geometry, species)

    if isinstance(geometry, Sphere):
        table += ' sphere'
    elif isinstance(geometry, Cylinder):
        table += ' cylinder'
    else:
        raise ValueError('Geometry not supported: {}'.format(geometry))

    R = geometry.r/species.debye

    if "darian-marholm" in table:
        table = get_table(table)
        pts = table['points']
        vals = table['values'].reshape(-1)
        I[indices_p] = I0*griddata(pts, vals, (1/kappa, alpha, R, eta[indices_p]))

    else:
        table = get_table(table)
        pts = table['points']
        vals = table['values'].reshape(-1)
        I[indices_p] = I0*griddata(pts, vals, (R, eta[indices_p]))
        if(kappa != float('inf') or alpha != 0):
            logger.warning("Using pure Laframboise tables discards spectral indices kappa and alpha")

    if len(indices_n)>0:
        pos_neg = "positive" if q>0 else "negative"
        logger.warning("Only attracted species current is covered by tabulated "
                       "values. Currents due to {} is set to zero for "
                       "{} potentials".format(species, pos_neg))

    if any(np.isnan(I)):
        logger.warning("Data points occurred outside the domain of tabulated values resulting in nan")

    return I[0] if len(I) == 1 else I

def finite_length_current_density(geometry, species, z=None, zn=None,
                                  V=None, eta=None, normalize=None):

    if isinstance(species, list):
        if normalize == True:
            logger.error('Cannot normalize current to more than one species')
            return None
        if eta is not None:
            logger.error('Cannot normalize voltage to more than one species')
            return None
        I = 0
        for s in species:
            I += finite_length_current_density(geometry, species, z=None, zn=None,
                                               V=None, eta=None, normalize=False)
        return I

    q, m, n, T = species.q, species.m, species.n, species.T
    kappa, alpha = species.kappa, species.alpha
    k = constants('Boltzmann constant')

    if kappa != float('inf') or alpha != 0:
        logger.error("Finite length effect data only available for Maxwellian")

    if V is not None:
        eta = q*V/(k*T)

    if z is not None:
        zn = z/species.debye

    if not isinstance(geometry, Cylinder):
        raise ValueError('Geometry not supported: {}'.format(geometry))

    ln = geometry.l/species.debye

    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),'cache.npz')
    file = np.load(fname)
    lns = file['ls']
    etas = file['etas']
    vals_A = file['popts'][:,0]
    vals_alpha = file['popts'][:,1]
    vals_gamma = file['popts'][:,4]
    vals_C = file['popts'][:,5]

    A     = griddata((lns, etas), vals_A    , (ln, eta))
    alpha = griddata((lns, etas), vals_alpha, (ln, eta))
    gamma = griddata((lns, etas), vals_gamma, (ln, eta))
    C     = griddata((lns, etas), vals_C    , (ln, eta))

    def f(z):
        return A*np.exp(-alpha*z)*(z**gamma)

    def g(z, l):
        return C+f(z)+f(l-z)

    if normalize=='th':
        geonorm = deepcopy(geometry)
        geonorm.l = 1
        I0 = OML_current(geonorm, species, eta=eta, normalize=True)
    elif normalize=='OML':
        I0 = 1
    else:
        geonorm = deepcopy(geometry)
        geonorm.l = 1
        I0 = OML_current(geonorm, species, eta=eta)

    I = I0*g(zn, ln)

    return I

def finite_length_current(geometry, species, z=None, zn=None,
                          V=None, eta=None, normalize=None):

    if isinstance(species, list):
        if normalize == True:
            logger.error('Cannot normalize current to more than one species')
            return None
        if eta is not None:
            logger.error('Cannot normalize voltage to more than one species')
            return None
        I = 0
        for s in species:
            I += finite_length_current(geometry, species, z=None, zn=None,
                                       V=None, eta=None, normalize=False)
        return I

    q, m, n, T = species.q, species.m, species.n, species.T
    kappa, alpha = species.kappa, species.alpha
    k = constants('Boltzmann constant')

    if kappa != float('inf') or alpha != 0:
        logger.error("Finite length effect data only available for Maxwellian")

    if V is not None:
        eta = q*V/(k*T)

    if not isinstance(geometry, Cylinder):
        raise ValueError('Geometry not supported: {}'.format(geometry))

    ln = geometry.l/species.debye
    lln = geometry.lguard/species.debye
    lrn = geometry.rguard/species.debye
    ltn = lln + ln + lrn

    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),'cache.npz')
    file = np.load(fname)
    lns = file['ls']
    etas = file['etas']
    vals_A = file['popts'][:,0]
    vals_alpha = file['popts'][:,1]
    vals_gamma = file['popts'][:,4]
    vals_C = file['popts'][:,5]

    A     = griddata((lns, etas), vals_A    , (ltn, eta))
    alpha = griddata((lns, etas), vals_alpha, (ltn, eta))
    gamma = griddata((lns, etas), vals_gamma, (ltn, eta))
    C     = griddata((lns, etas), vals_C    , (ltn, eta))

    if normalize=='th':
        geonorm = deepcopy(geometry)
        geonorm.l = 1
        I0 = OML_current(geonorm, species, eta=eta, normalize=True)
    elif normalize=='OML':
        I0 = 1
    else:
        geonorm = deepcopy(geometry)
        geonorm.l = 1
        I0 = OML_current(geonorm, species, eta=eta)

    I = I0*species.debye*(int_additive_model(lln+ln, ltn, A, alpha, 0, 1, gamma, C)
                         -int_additive_model(lln   , ltn, A, alpha, 0, 1, gamma, C))
    return I

def Gamma(a, x):
    return special.gammaincc(a, x)*special.gamma(a)

def h(zeta, alpha, gamma):
    return np.exp(-alpha*zeta)*(zeta**gamma)

# Indefinite integral of h
def H(zeta, alpha, gamma):
    if zeta==0: zeta=np.finfo(float).eps
    return -(zeta**gamma)*((alpha*zeta)**(-gamma))*Gamma(1+gamma,alpha*zeta)/alpha

def additive_model(zeta, lambd, A, alpha, B, beta, gamma, C):
    return C + A*h(zeta, alpha, gamma) + B*h(zeta, beta, gamma) \
             + A*h(lambd-zeta, alpha, gamma) + B*h(lambd-zeta, beta, gamma)

def int_additive_model(zeta, lambd, A, alpha, B, beta, gamma, C):
    return C*zeta + A*H(zeta, alpha, gamma) + B*H(zeta, beta, gamma) \
                  - A*H(lambd-zeta, alpha, gamma) - B*H(lambd-zeta, beta, gamma)
