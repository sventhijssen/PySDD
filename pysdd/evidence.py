#!/usr/bin/env python3
# encoding: utf-8
"""
pysdd-cli
~~~~~~~~~

PySDD command line interface.

:author: Wannes Meert, Arthur Choi
:copyright: Copyright 2019 KU Leuven and Regents of the University of California.
:license: Apache License, Version 2.0, see LICENSE for details.
"""
from pathlib import Path
import sys
import time
import argparse
import logging
from pysdd.sdd import SddManager, Vtree, Fnf, CompilerOptions


logger = logging.getLogger(__name__)


def main(argv=None):
    options, args = getopt(argv)

    if options.cnf_filename is not None:
        print("creating manager...")
        sdd, _ = SddManager.from_cnf_file(bytes(options.cnf_filename))

        root = sdd.root

        # Model Counting
        wmc = root.wmc(log_mode=False)
        wmc.propagate()

        weights = read_weights(bytes(options.cnf_filename))
        print("Weights size: " + str(len(weights)))

        literals = [sdd.literal(i) for i in range(1, sdd.var_count()+1)]

        print("Number of literals: " + str(len(literals)))

        # Set weights for all literals
        for i in range(1, len(literals)+1):
            wmc.set_literal_weight(i, weights[(i-1)*2])  # Positive literal weight
            wmc.set_literal_weight(-i, weights[(i-1)*2+1])  # Negative literal weight

        w = wmc.propagate()

        print("Weighted model count: " + str(w))
        #
        # for i in range(1, sdd.var_count()+1):
        #     print(str(i) + ": " + str(wmc.literal_weight(i)))
        #     print(str(-i) + ": " + str(wmc.literal_weight(-i)))

        # print("Model count: " + str(sdd.model_count(root)))

        # for i in range(1, sdd.var_count() + 1):
        #     print(str(i-1) + ": " + str(wmc.literal_pr(i)))

        # Weighted Model Counting

        wmc.set_literal_weight(literals[29], 0)  # Positive literal weight
        # wmc.set_literal_weight(-literals[29], 0)  # Negative literal weight

        # wmc.set_literal_weight(literals[32], 0)  # Positive literal weight
        wmc.set_literal_weight(-literals[32], 0)  # Negative literal weight
        #
        # wmc.set_literal_weight(literals[40], 0)  # Positive literal weight
        wmc.set_literal_weight(-literals[40], 0)  # Negative literal weight

        # for i in range(1, sdd.var_count()+1):
        #     print(str(i) + ": " + str(wmc.literal_weight(i)))
        #     print(str(-i) + ": " + str(wmc.literal_weight(-i)))

        w = wmc.propagate()

        for i in range(1, sdd.var_count() + 1):
            print(str(i) + ": " + str(wmc.literal_pr(i)))

        print("Weighted model count: " + str(w))

        print("8: " + str(wmc.literal_pr(8)))


def read_weights(nnf_path):
    """
    Format: c weights PW_1 NW_1 ... PW_n NW_n
    :param nnf_path: Path to NNF file
    :return: list of weights
    """
    weight_str = None
    with open(nnf_path, "r") as ifile:
        for line in ifile.readlines():
            if "c weights " in line:
                weight_str = line[10:].strip()
                break
    if weight_str is None:
        return None
    weight_strs = weight_str.split(" ")
    weights = [float(w) for w in weight_strs]
    return weights


def create_wmc(node, weights):
    if weights is None:
        return None
    wmc = node.wmc(False)
    for i in range(len(weights)):
        lit = (i // 2) + 1
        if (i % 2) == 1:
            lit = -lit
        w = weights[i]
        wmc.set_literal_weight(node.manager.literal(lit), w)
    return wmc


class CustomHelpFormatter(argparse.HelpFormatter):

    def _format_text(self, text):
        text = super()._format_text(text)
        if "Copyright" in text:
            a, b = text.split("Copyright")
            text = a + "\n\n" + super()._format_text("Copyright" + b)
        return text


def create_parser():
    def bytes_path(p):
        return bytes(Path(p))

    def bytes_str(s):
        return s.encode()

    epilog = ("Weighted Model Counting is performed if the NNF file containts a line formatted as follows: "
              "\"c weights PW_1 NW_1 ... PW_n NW_n\"."
              "Copyright 2017-2019, Regents of the University of California and KU Leuven")
    parser = argparse.ArgumentParser(description='Sentential Decision Diagram, Compiler',
                                     epilog=epilog,
                                     formatter_class=CustomHelpFormatter)
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('-c', metavar='FILE', type=bytes_path,
                             dest='cnf_filename', help='set input CNF file')
    input_group.add_argument('-d', metavar='FILE', type=bytes_path,
                             dest='dnf_filename', help='set input DNF file')
    input_group.add_argument('-s', metavar='FILE', type=bytes_path,
                             dest='sdd_filename', help='set input SDD file')
    parser.add_argument('-v', metavar='FILE', type=bytes_path,
                        dest='vtree_filename', help='set input VTREE file')

    parser.add_argument('-W', metavar='FILE', type=bytes_path,
                        dest='output_vtree_filename', help='set output VTREE file')
    parser.add_argument('-V', metavar='FILE', type=bytes_path,
                        dest='output_vtree_dot_filename', help='set output VTREE (dot) file')
    parser.add_argument('-R', metavar='FILE', type=bytes_path,
                        dest='output_sdd_filename', help='set output SDD file')
    parser.add_argument('-S', metavar='FILE', type=bytes_path,
                        dest='output_sdd_dot_filename', help='set output SDD (dot) file')

    parser.add_argument('-m', action='store_true',
                        dest='minimize_cardinality', help='minimize the cardinality of compiled sdd')

    parser.add_argument('-t', metavar='TYPE', type=bytes_str, default='balanced',
                        choices=[b'left', b'right', b'vertical', b'balanced', b'random'],
                        dest='initial_vtree_type',
                        help='set initial vtree type (left/right/vertical/balanced/random)')

    parser.add_argument('-r', metavar='K', type=int, default=-1,
                        dest='vtree_search_mode',
                        help='if K>0: invoke vtree search every K clauses. If K=0: disable vtree search. ' +
                             'By default (no -r option), dynamic vtree search is enabled')

    parser.add_argument('-q', action='store_true',
                        dest='post_search', help='perform post-compilation vtree search')

    parser.add_argument('-p', action='store_true',
                        dest='verbose', help='verbose output')

    parser.add_argument('--log_mode', action='store_true',
                        dest='log_mode', help='weights in log')

    return parser


def getopt(argv=None):
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    options = CompilerOptions(cnf_filename=args.cnf_filename,
                              dnf_filename=args.dnf_filename,
                              vtree_filename=args.vtree_filename,
                              sdd_filename=args.sdd_filename,
                              output_vtree_filename=args.output_vtree_filename,
                              output_vtree_dot_filename=args.output_vtree_dot_filename,
                              output_sdd_filename=args.output_sdd_filename,
                              output_sdd_dot_filename=args.output_sdd_dot_filename,
                              initial_vtree_type=args.initial_vtree_type,
                              minimize_cardinality=args.minimize_cardinality,
                              vtree_search_mode=args.vtree_search_mode,
                              post_search=args.post_search,
                              verbose=args.verbose)
    # print(str(options))
    return options, args
