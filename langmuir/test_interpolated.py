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
from langmuir import *
from pytest import approx
import pytest

# I generally try to test one point in each table, with unequal row/column
# indices and where nearby elements differ from the one I test.

@pytest.fixture
def electron():
    return Species(n=1e11, T=1000)

def test_laframboise_sphere(electron):
    I = finite_radius_current(Sphere(electron.debye), electron, eta=-0.6,
                              normalize=True, table='laframboise')
    assert(I == approx(1.595))

def test_laframboise_cylinder(electron):
    I = finite_radius_current(Cylinder(3*electron.debye, 1), electron, eta=-2.0,
                              normalize=True, table='laframboise')
    assert(I == approx(1.928))

def test_darian_marholm_uncomplete_sphere(electron):

    def curr(kappa, alpha):
        sp = Species(n=1e11, T=1000, kappa=kappa, alpha=alpha)
        return finite_radius_current(Sphere(2*sp.debye), sp, eta=-1,
                                     normalize=True,
                                     table='darian-marholm uncomplete')

    # Testing one element for each alpha/kappa table
    assert(curr(float('inf'), 0  ) == approx(1.958))
    assert(curr(float('inf'), 0.2) == approx(2.069))
    assert(curr(6           , 0  ) == approx(1.982))
    assert(curr(6           , 0.2) == approx(2.369))
    assert(curr(4           , 0  ) == approx(1.990))
    assert(curr(4           , 0.2) == approx(2.846))

    # Testing that V=0 is the inaccurate one and that R=0 doesn't exist
    I = finite_radius_current(Sphere(0.2*electron.debye), electron, 0,
                              normalize=True, table='darian-marholm uncomplete')
    assert(I == approx(0.965))

def test_darian_marholm_sphere(electron):

    # Testing one from the uncomplete subset
    sp = Species(n=1e11, T=1000, kappa=6)
    I = finite_radius_current(Sphere(2*sp.debye), sp, eta=-1,
                              normalize=True, table='darian-marholm')
    assert(I == approx(1.982))

    # Testing that V=0 is the accurate one (not the one from uncomplete)
    I = finite_radius_current(Sphere(0.2*electron.debye), electron, eta=0,
                              normalize=True)
    assert(I == approx(1.0))

    # Testing that R=0 exists
    I = finite_radius_current(Sphere(0), electron, eta=-3,
                              normalize=True, table='darian-marholm')
    assert(I == approx(4.0))

def test_darian_marholm_uncomplete_cylinder(electron):

    def curr(kappa, alpha):
        sp = Species(n=1e11, T=1000, kappa=kappa, alpha=alpha)
        return finite_radius_current(Cylinder(3*sp.debye, 1), sp, eta=-1,
                                     normalize=True,
                                     table='darian-marholm uncomplete')

    assert(curr(float('inf'), 0  ) == approx(1.538))
    assert(curr(float('inf'), 0.2) == approx(1.914))
    assert(curr(6           , 0  ) == approx(1.509))
    assert(curr(6           , 0.2) == approx(2.165))
    assert(curr(4           , 0  ) == approx(1.510))
    assert(curr(4           , 0.2) == approx(2.547))

    # Testing that V=0 is the inaccurate one and that R=0 doesn't exist
    I = finite_radius_current(Cylinder(1.0*electron.debye, 1), electron, 0,
                              normalize=True, table='darian-marholm uncomplete')
    assert(I == approx(0.974))

def test_darian_marholm_cylinder(electron):

    # Testing one from the uncomplete subset
    sp = Species(n=1e11, T=1000, kappa=6)
    I = finite_radius_current(Cylinder(3*sp.debye, 1), sp, eta=-1,
                              normalize=True, table='darian-marholm')
    assert(I == approx(1.509))

    # Testing that V=0 is the accurate one (not the one from uncomplete)
    I = finite_radius_current(Cylinder(electron.debye, 1), electron, eta=0,
                              normalize=True)
    assert(I == approx(1.0))

    # Testing that R=0 exists
    I = finite_radius_current(Cylinder(0,1), electron, eta=-3,
                              normalize=True, table='darian-marholm')
    assert(I == approx(2.2417, 1e-3))

def test_laframboise_darian_marholm_sphere(electron):

    # Testing one from each of Darian-Marholm and Laframboise

    sp = Species(n=1e11, T=1000, kappa=4, alpha=0.2)
    I = finite_radius_current(Sphere(3*sp.debye), sp, eta=-5, normalize=True,
                              table='laframboise-darian-marholm')
    assert(I == approx(4.535))

    I = finite_radius_current(Sphere(3*electron.debye), electron, eta=-5,
                              normalize=True,
                              table='laframboise-darian-marholm')
    assert(I == approx(4.640))

def test_laframboise_darian_marholm_cylinder(electron):

    # Testing one from each of Darian-Marholm and Laframboise
    sp = Species(n=1e11, T=1000, kappa=4, alpha=0.2)
    I = finite_radius_current(Cylinder(3*sp.debye, 1), sp, eta=-5,
                              normalize=True,
                              table='laframboise-darian-marholm')
    assert(I == approx(3.465))

    I = finite_radius_current(Cylinder(3*electron.debye, 1), electron, eta=-5,
                              normalize=True,
                              table='laframboise-darian-marholm')
    assert(I == approx(2.701))
