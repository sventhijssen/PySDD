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
    fnf = None
    weights = None

    if options.cnf_filename is not None:
        # print("reading cnf...")
        fnf = Fnf.from_cnf_file(bytes(options.cnf_filename))
        weights = read_weights(options.cnf_filename)
    elif options.dnf_filename is not None:
        # print("reading dnf...")
        fnf = Fnf.from_dnf_file(bytes(options.dnf_filename))
        weights = read_weights(options.cnf_filename)

    if options.vtree_filename is not None:
        # print("reading initial vtree...")
        vtree = Vtree.from_file(bytes(options.vtree_filename))
    else:
        if fnf is None:
            raise argparse.ArgumentTypeError("CNF or DNF file required")
        # print(f"creating initial vtree {options.initial_vtree_type.decode()}")
        vtree = Vtree(var_count=fnf.var_count, vtree_type=options.initial_vtree_type)

    # print("creating manager...")
    manager = SddManager.from_vtree(vtree)
    manager.set_options(options)

    if options.sdd_filename is None:
        # print("compiling...")
        c1 = time.time()
        node = manager.fnf_to_sdd(fnf)
        c2 = time.time()
        secs = c2 - c1
        # print("")
        # print(f"compilation time         : {secs:.3f} sec")
    else:
        # print("reading sdd from file...")
        c1 = time.time()
        node = manager.read_sdd_file(options.sdd_filename)
        c2 = time.time()
        secs = c2 - c1
        # print(f"read time                : {secs:.3f} sec")
        weights = read_weights(options.sdd_filename)

    wmc = create_wmc(node, weights, args)

    return get_node(node, wmc)


def create_wmc(node, weights, args):
    if weights is None:
        return None
    wmc = node.wmc(log_mode=args.log_mode)
    for i in range(len(weights)):
        lit = (i // 2) + 1
        if (i % 2) == 1:
            lit = -lit
        w = weights[i]
        wmc.set_literal_weight(node.manager.literal(lit), w)
    return wmc


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


def print_node(node, wmc=None):
    # print(f" sdd size                : {node.size()}")
    # print(f" sdd node count          : {node.count()}")
    c1 = time.time()
    mc = node.global_model_count()
    c2 = time.time()
    # print(f" sdd model count         : {mc}    {c2-c1:.3f} sec")
    if wmc is not None:
        c1 = time.time()
        mc = wmc.propagate()
        c2 = time.time()
        # print(f" sdd weighted model count: {mc}    {c2-c1:.3f} sec")


def get_node(node, wmc=None):
    # print(f" sdd size                : {node.size()}")
    # print(f" sdd node count          : {node.count()}")
    c1 = time.time()
    mc = node.global_model_count()
    c2 = time.time()
    # print(f" sdd model count         : {mc}    {c2-c1:.3f} sec")
    if wmc is not None:
        c1 = time.time()
        mc = wmc.propagate()
        c2 = time.time()
        # print(f" sdd weighted model count: {mc}    {c2-c1:.3f} sec")
    return node.size()


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
    # # print(str(options))
    return options, args
