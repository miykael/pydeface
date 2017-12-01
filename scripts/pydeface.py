#!/usr/bin/env python
"""Deface an image using FSL.

Usage:
------
pydeface.py <filename to deface> <optional: outfilename>

"""

# Copyright 2011, Russell Poldrack. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY RUSSELL POLDRACK ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL RUSSELL POLDRACK OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import nibabel
import os
import sys
import tempfile
from nipype.interfaces import fsl
from pkg_resources import resource_filename, Requirement, require


def main():
    cleanup, verbose = True, False

    template = resource_filename(Requirement.parse("pydeface"),
                                 "pydeface/data/mean_reg2mean.nii.gz")
    facemask = resource_filename(Requirement.parse("pydeface"),
                                 "pydeface/data/facemask.nii.gz")

    if not os.path.exists(template):
        raise Exception('Missing template: %s' % template)
    if not os.path.exists(facemask):
        raise Exception('Missing face mask: %s' % facemask)

    if len(sys.argv) < 2:
        sys.stdout.write(__doc__)
        sys.exit(2)
    else:
        infile = sys.argv[1]

    if len(sys.argv) > 2:
        outfile = sys.argv[2]
    else:
        outfile = infile.replace('.nii', '_defaced.nii')

    if os.path.exists(outfile):
        raise Exception('%s already exists, remove it first.' % outfile)

    if 'FSLDIR' not in os.environ:
        raise Exception("FSL must be installed and "
                        "FSLDIR environment variable must be defined.")
        sys.exit(2)

    _, tmpmat = tempfile.mkstemp()
    tmpmat = tmpmat + '.mat'
    _, tmpfile = tempfile.mkstemp()
    tmpfile = tmpfile + '.nii.gz'
    if verbose:
        print(tmpmat)
        print(tmpfile)
    _, tmpfile2 = tempfile.mkstemp()
    _, tmpmat2 = tempfile.mkstemp()

    print('Defacing...\n%s' % infile)

    # register template to infile
    flirt = fsl.FLIRT()
    flirt.inputs.cost_func = 'mutualinfo'
    flirt.inputs.in_file = template
    flirt.inputs.out_matrix_file = tmpmat
    flirt.inputs.out_file = tmpfile2
    flirt.inputs.reference = infile
    flirt.run()

    # warp facemask to infile
    flirt = fsl.FLIRT()
    flirt.inputs.in_file = facemask
    flirt.inputs.in_matrix_file = tmpmat
    flirt.inputs.apply_xfm = True
    flirt.inputs.reference = infile
    flirt.inputs.out_file = tmpfile
    flirt.inputs.out_matrix_file = tmpmat2
    flirt.run()

    # multiply mask by infile and save
    infile_img = nibabel.load(infile)
    tmpfile_img = nibabel.load(tmpfile)
    outdata = infile_img.get_data() * tmpfile_img.get_data()
    outfile_img = nibabel.Nifti1Image(outdata, infile_img.get_affine(),
                                      infile_img.get_header())
    outfile_img.to_filename(outfile)

    if cleanup:
        os.remove(tmpfile)
        os.remove(tmpfile2)
        os.remove(tmpmat)

    print('Output saved as:\n%s' % outfile)


if __name__ == "__main__":
    welcome_str = 'pydeface ' + require("pydeface")[0].version
    welcome_decor = '-' * len(welcome_str)
    print(welcome_decor + '\n' + welcome_str + '\n' + welcome_decor)
    main()
