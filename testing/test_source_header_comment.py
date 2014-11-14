import os
import subprocess as sp
import sys
from astropy.io import fits as pyfits
import pytest

def add_from_catalogue(source_filename, fname, cattype):
    cmd = [sys.executable, './zlp_crossmatch.py',
           '-e', cattype,
           source_filename,
           '-o', fname]
    sp.check_call(map(str, cmd))


def check_history(fname, *check_strings):
    header = pyfits.getheader(fname, 'catalogue')
    history = str(header['history'])
    for check_string in check_strings:
        assert check_string in history


@pytest.fixture
def tempfits(tmpdir):
    output_filename = str(tmpdir.join('30-wasp18b-matched.fits'))
    return output_filename

@pytest.fixture
def source_filename():
    return '30-wasp18b.fits'

def test_simbad_comment(source_filename, tempfits):
    add_from_catalogue(source_filename, tempfits, 'simbad')

    check_history(tempfits, 'Added columns otype, sp_type from Simbad')


def test_ucac_comment(source_filename, tempfits):
    add_from_catalogue(source_filename, tempfits, 'ucac3')

    check_history(tempfits,
                  'Bmag', 'Hmag', 'Imag', 'Jmag',
                  'from Ucac3')

def test_both(source_filename, tempfits):
    add_from_catalogue(source_filename, tempfits, 'simbad')
    add_from_catalogue(tempfits, tempfits, 'ucac3')

    check_strings = ['Bmag', 'Hmag', 'Imag', 'Jmag', 'otype', 'sp_type',
                     'Simbad', 'Ucac3']

    check_history(tempfits, *check_strings)
