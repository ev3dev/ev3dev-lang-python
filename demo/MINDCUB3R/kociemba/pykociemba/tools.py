#!/usr/bin/env python

import argparse
import random
from facecube import FaceCube
from cubiecube import CubieCube
from coordcube import CoordCube

def randomCube():
    """
    Generates a random cube.
    @return A random cube in the string representation. Each cube of the cube space has the same probability.
    """
    cc = CubieCube()
    cc.setFlip(random.randint(0, CoordCube.N_FLIP - 1))
    cc.setTwist(random.randint(0, CoordCube.N_TWIST - 1))
    while True:
        cc.setURFtoDLB(random.randint(0, CoordCube.N_URFtoDLB - 1))
        cc.setURtoBR(random.randint(0, CoordCube.N_URtoBR - 1))

        if (cc.edgeParity() ^ cc.cornerParity()) == 0:
            break
    fc = cc.toFaceCube()
    return fc.to_String()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--random', action='store_true', help='Return random cube', default=None)
    args = parser.parse_args()

    if args.random:
        print randomCube()
