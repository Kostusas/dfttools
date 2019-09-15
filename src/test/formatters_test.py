import unittest

from dfttools.formatters import *
from dfttools.parsers import structure, qe, openmx
from dfttools.types import *
from numpy import testing
from numericalunits import angstrom


class BackForthTests(unittest.TestCase):

    def setUp(self):
        self.cell = UnitCell(
            Basis((2.5 * angstrom, 2.5 * angstrom, 10 * angstrom, 0, 0, .5), kind='triclinic'),
            (
                (1. / 3, 1. / 3, .5),
                (2. / 3, 2. / 3, .5),
            ),
            'C',
        )

        coords = (numpy.linspace(0, 1, 11, endpoint=False), numpy.linspace(0, 1, 13, endpoint=False),
                  numpy.linspace(0, 1, 17, endpoint=False))

        self.grid = Grid(
            self.cell,
            coords,
            numpy.zeros((11, 13, 17)),
        )
        self.grid.values = numpy.prod(numpy.sin(self.grid.explicit_coordinates() * 2 * numpy.pi), axis=-1)

    def test_xsf_back_forth(self):
        c1 = self.cell
        cells = structure.xsf(xsf_structure(c1)).unitCells()
        assert len(cells) == 1
        c2 = cells[0]
        assert c1.size == c2.size
        testing.assert_allclose(c1.vectors / angstrom, c2.vectors / angstrom, atol=1e-6)
        testing.assert_allclose(c1.coordinates, c2.coordinates)
        testing.assert_equal(c1.values, c2.values)

    def test_xsf_back_forth_multi(self):
        c1 = []
        for i in range(10):
            c = self.cell.copy()
            c.coordinates += (numpy.random.rand(*c.coordinates.shape) - .5) / 10
            c1.append(c)
        c2 = structure.xsf(xsf_structure(*c1)).unitCells()

        for i, j in zip(c1, c2):
            assert i.size == j.size
            testing.assert_allclose(i.vectors / angstrom, j.vectors / angstrom, atol=1e-6)
            testing.assert_allclose(i.coordinates, j.coordinates)
            testing.assert_equal(i.values, j.values)

    def test_xsf_grid_back_forth(self):
        data = xsf_grid(self.grid, self.cell)
        g = structure.xsf(data).grids()[0]
        testing.assert_allclose(self.grid.values, g.values, atol=1e-7)

    def test_qe_input(self):
        cell = UnitCell(Basis((2.5 * angstrom, 2.5 * angstrom, 10 * angstrom), kind='orthorhombic'),
            (
                (1. / 3, 1. / 3, .5),
                (2. / 3, 2. / 3, .5),
            ),
            'C',
        )
        self.assertEqual(qe_input(
            cell=cell,
            relax_mask=0.1,
            parameters={"system": {"a": 3}, "control": {"b": "c"}, "random": {"d": True}},
            inline_parameters={"random": "hello"},
            pseudopotentials={"C": "C.UPF"},
            masses={"C": 3},
        ), "\n".join((
            "&CONTROL",
            "    b = 'c'",
            "/",
            "&SYSTEM",
            "    a = 3",
            "    ibrav = 0",
            "    nat = 2",
            "    ntyp = 1",
            "/",
            "ATOMIC_SPECIES",
            "    C  3.000 C.UPF",
            "ATOMIC_POSITIONS crystal",
            "     C 0.33333333333333 0.33333333333333 0.50000000000000 0.100000 0.100000 0.100000",
            "     C 0.66666666666667 0.66666666666667 0.50000000000000 0.100000 0.100000 0.100000",
            "CELL_PARAMETERS angstrom",
            "    2.50000000000000e+00 0.00000000000000e+00 0.00000000000000e+00",
            "    0.00000000000000e+00 2.50000000000000e+00 0.00000000000000e+00",
            "    0.00000000000000e+00 0.00000000000000e+00 1.00000000000000e+01",
            "RANDOM hello",
            "    d = .true.",
        )))
        self.assertEqual(qe_input(
            cell=cell,
            relax_mask=(0, 1),
            pseudopotentials={"C": "C.UPF"},
        ), "\n".join((
            "&SYSTEM",
            "    ibrav = 0",
            "    nat = 2",
            "    ntyp = 1",
            "/",
            "ATOMIC_SPECIES",
            "    C  1.000 C.UPF",
            "ATOMIC_POSITIONS crystal",
            "     C 0.33333333333333 0.33333333333333 0.50000000000000 0.000000 0.000000 0.000000",
            "     C 0.66666666666667 0.66666666666667 0.50000000000000 1.000000 1.000000 1.000000",
            "CELL_PARAMETERS angstrom",
            "    2.50000000000000e+00 0.00000000000000e+00 0.00000000000000e+00",
            "    0.00000000000000e+00 2.50000000000000e+00 0.00000000000000e+00",
            "    0.00000000000000e+00 0.00000000000000e+00 1.00000000000000e+01",
        )))

    def test_qe_back_forth(self):
        c1 = self.cell
        c2 = qe.input(qe_input(
            cell=c1,
            pseudopotentials={"C": "C.UPF"},
        )).unitCell()
        assert c1.size == c2.size
        testing.assert_allclose(c1.vectors / angstrom, c2.vectors / angstrom, atol=1e-6)
        testing.assert_allclose(c1.coordinates, c2.coordinates)
        testing.assert_equal(c1.values, c2.values)

    def test_siesta_not_raises(self):
        siesta_input(self.cell)

    def test_openmx_back_forth(self):
        c1 = self.cell
        c2 = openmx.input(openmx_input(
            c1,
            populations={"C": "2 2"},
        )).unitCell()
        assert c1.size == c2.size
        testing.assert_allclose(c1.vectors / angstrom, c2.vectors / angstrom, atol=1e-6)
        testing.assert_allclose(c1.coordinates, c2.coordinates, rtol=1e-6)
        testing.assert_equal(c1.values, c2.values)

    def test_openmx_back_forth_negf_0(self):
        c1 = self.cell
        c2 = openmx.input(openmx_input(
            c1,
            l=c1,
            r=c1,
            populations={"C": "2 2"},
        )).unitCell(l=c1, r=c1)
        assert c1.size == c2.size
        testing.assert_allclose(c1.vectors / angstrom, c2.vectors / angstrom, atol=1e-6)
        testing.assert_allclose(c1.coordinates, c2.coordinates, rtol=1e-6)
        testing.assert_equal(c1.values, c2.values)

    def test_openmx_back_forth_negf_1(self):
        c1 = self.cell.repeated(2, 1, 1)
        l = self.cell
        r = self.cell.repeated(3, 1, 1)
        c2 = openmx.input(openmx_input(
            c1,
            l=l,
            r=r,
            populations={"C": "2 2"},
        )).unitCell(l=l, r=r)
        assert c1.size == c2.size
        testing.assert_allclose(c1.vectors / angstrom, c2.vectors / angstrom, atol=1e-6)
        testing.assert_allclose(c1.coordinates, c2.coordinates, rtol=1e-6)
        testing.assert_equal(c1.values, c2.values)
