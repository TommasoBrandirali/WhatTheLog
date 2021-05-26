# -*- coding: utf-8 -*-
"""
Created on Tuesday 05/25/2021
Author: Tommaso Brandirali
Email: tommaso.brandirali@gmail.com
"""

#****************************************************************************************************
# Imports
#****************************************************************************************************

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# External
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
import pickle
from copy import deepcopy
import numpy as np
from pathlib import Path
import sys
from sknetwork.utils import edgelist2adjacency
from sknetwork.hierarchy import LouvainHierarchy, Paris
from tqdm import tqdm

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Internal
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from whatthelog.prefixtree.graph import Graph
from whatthelog.prefixtree.prefix_tree import PrefixTree
from whatthelog.auto_printer import AutoPrinter
from whatthelog.clustering.evaluator import Evaluator

project_root = Path(os.path.abspath(os.path.dirname(__file__))).parent.parent


#****************************************************************************************************
# State Model Factory
#****************************************************************************************************

class StateModelFactory(AutoPrinter):
    """
    State model factory class.
    """

    default_true_traces_dir = "out/true_traces"
    default_false_traces_dir = "out/false_traces"
    algorithms = {
        'louvain': LouvainHierarchy,
        'paris': Paris
    }

    def __init__(self, tree: PrefixTree, true_traces_dir: str = None, false_traces_dir: str = None):

        if not true_traces_dir:
            true_traces_dir = project_root.joinpath(self.default_true_traces_dir)
        if not false_traces_dir:
            false_traces_dir = project_root.joinpath(self.default_false_traces_dir)

        self.tree = tree
        self.evaluator = Evaluator(tree, true_traces_dir, false_traces_dir)

    def build_from_dendrogram(self, dendrogram: np.ndarray) -> Graph:
        """
        Creates a state model by recursively merging the Prefix Tree nodes
        according to the given dendrogram produced by hierarchical clustering.

        :param dendrogram: the input dendrogram
        :return: the resulting Graph instance
        """

        tree = deepcopy(self.tree)
        length = len(tree)
        merged_states = {}

        # TODO: use evaluator to merge until threshold fitness
        for count, merge in enumerate(tqdm(dendrogram, file=sys.stdout)):

            merge = merge.tolist()
            dest, source = int(merge[0]), int(merge[1])
            dest_index = dest if dest < length else merged_states[dest]
            source_index = source if source < length else merged_states[source]

            tree.merge_states(tree.states[dest_index], tree.states[source_index])

            merged_states[length + count] = dest_index

        return tree

    def run_clustering(self, algorithm: str = 'louvain') -> Graph:
        """
        Performs a clustering of the prefix tree using the given hierarchical algorithm,
        returns the resulting state model as a Graph of merged states.

        :param algorithm: the algorithm to use for clustering
        :return: the reduced prefix tree state model
        """

        model = self.algorithms[algorithm]()
        adj_list = self.tree.get_adj_list(remove_self_loops=False)
        adjacency = edgelist2adjacency(adj_list)

        self.print(f"Running '{algorithm}' clustering algorithm...")
        dendrogram = model.fit_transform(adjacency)

        self.print("Building model...")
        return self.build_from_dendrogram(dendrogram)

    @staticmethod
    def pickle_model(model: Graph, file: str) -> None:
        """
        Pickles and dumps the given model instance into a given file.
        If the file does not exist it will be created.
        :param model: the model instance to pickle
        :param file: the file to dump the pickled model to
        """

        with open(file, 'wb+') as f:
            pickle.dump(model, f)

    @staticmethod
    def unpickle_model(file: str) -> Graph:
        """
        Parses a pickled model instance from a file.
        :param file: the pickle file representing the instance
        :return: the parsed Graph instance
        """

        if not os.path.isfile(file):
            raise FileNotFoundError("Pickle file not found!")

        with open(file, 'rb') as f:
            model = pickle.load(f)

        return model
