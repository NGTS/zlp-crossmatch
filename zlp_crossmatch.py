#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import argparse
from astropy import units as u
import fitsio
from StringIO import StringIO
import numpy as np
import os
import subprocess as sp
import tempfile
from collections import defaultdict
import joblib
import shutil

BASEDIR = os.path.dirname(__file__)

memory = joblib.Memory(cachedir=tempfile.gettempdir())

COLUMNS = {
    'ucac3': [
        'f.mag', 'a.mag', 'e_f.mag', 'e_a.mag',
        'pmRA', 'pmDE', 'e_pmRA', 'e_pmDE',
        'Jmag', 'Hmag', 'Kmag', 'Bmag', 'R2mag',
        'Imag', 'angDist',
    ],
    'simbad': [
        'otype', 'sp_type',
    ],
}

class Stilts(object):
    stilts_script = os.path.join(BASEDIR, 'stilts')

    @classmethod
    def query(cls, infile, external_name, radius=10.):
        self = cls()
        self.infile = infile
        self.radius = radius
        self.external_name = external_name

        with tempfile.NamedTemporaryFile(suffix='.fits') as tfile:
            self.query_external(tfile)
            tfile.seek(0)

            self.results_table = fitsio.read(tfile.name, 1)

        return self

    def query_external(self, fh):
        cmd = ['bash', self.stilts_script,
               'cdsskymatch',
               'cdstable={}'.format(self.external_name),
               'find=all',
               'in={}#catalogue'.format(self.infile),
               'radius={}'.format(self.radius),
               'out={}'.format(fh.name),
               ]
        sp.check_call(cmd)


@memory.cache
def fetch(filename, external_name):
    return Stilts.query(filename, external_name).results_table


def main(args):
    original_catalogue = fitsio.read(args.filename, 'catalogue')
    query_results = fetch(args.filename, args.external_catalogue)

    missing_keys = COLUMNS[args.external_catalogue]

    print('Adding columns: {}'.format(missing_keys))
    new_cols = defaultdict(list)
    matched_obj_id = query_results['OBJ_ID'].tolist()

    for obj_id in original_catalogue['OBJ_ID']:
        if obj_id in matched_obj_id:
            index = matched_obj_id.index(obj_id)

            for key in missing_keys:
                value = query_results[key][index]
                if value.dtype.kind == 'S':
                    value = value.strip()
                new_cols[key].append(value)
        else:
            for key in missing_keys:
                new_cols[key].append(np.nan)

    new_cols = {key: np.array(new_cols[key]) for key in new_cols}

    shutil.copyfile(args.filename, args.output)

    with fitsio.FITS(args.output, 'rw') as outfile:
        hdu = outfile['catalogue']
        for colname in new_cols:
            print('Adding column {}'.format(colname))
            hdu.insert_column(colname, new_cols[colname])



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('-e', '--external-catalogue', required=True,
                        choices=['ucac3', 'simbad'])
    parser.add_argument('-o', '--output', required=True)
    main(parser.parse_args())
