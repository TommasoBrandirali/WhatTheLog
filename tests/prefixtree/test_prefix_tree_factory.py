import os
from pathlib import Path

import pytest

from whatthelog.prefixtree.prefix_tree import PrefixTree
from whatthelog.prefixtree.prefix_tree_factory import PrefixTreeFactory

PROJECT_ROOT = Path(os.path.abspath(os.path.dirname(__file__))).parent.parent


@pytest.fixture
def tree() -> PrefixTree:
    traces_path = "tests/resources/traces_single"
    tree = PrefixTreeFactory().get_prefix_tree(
        PROJECT_ROOT.joinpath(traces_path),
        PROJECT_ROOT.joinpath("resources/config.json"))
    return tree

def test_one_trace(tree: PrefixTree):
    traces_path = "tests/resources/traces_single"

    with open(PROJECT_ROOT.joinpath(traces_path).joinpath("xx1"), 'r') as file:
        lines = len(file.readlines())

    assert len(tree) == lines + 1

    root = tree.get_root()
    assert root.properties.log_templates == [""]

    child2 = None
    for i in range(len(tree) - 1):
        if i == 2:
            child2 = root
        assert len(tree.get_children(root)) == 1
        root = tree.get_children(root)[0]

    assert tree.get_children(root) == []
    assert tree.get_parent(tree.get_root()) is None
    assert tree.get_parent(child2) == tree.get_children(tree.get_root())[0]


def test_multiple_traces():
    traces_path = "tests/resources/traces"
    pt = PrefixTreeFactory().get_prefix_tree(PROJECT_ROOT.joinpath(traces_path), PROJECT_ROOT.joinpath("resources/config.json"))

    root = pt.get_root()
    for _ in range(4):
        assert len(pt.get_children(root)) == 1
        root = pt.get_children(root)[0]

    assert len(pt.get_children(root)) == 2


def test_pickle(tree: PrefixTree):
    pickle_file_path = PROJECT_ROOT.joinpath("tests/singleTraceTree.pickle")
    if os.path.exists(pickle_file_path):
        os.remove(pickle_file_path)

    assert os.path.exists(pickle_file_path) is False

    PrefixTreeFactory.pickle_tree(tree, pickle_file_path)

    assert os.path.exists(pickle_file_path)

    pt = PrefixTreeFactory.unpickle_tree(pickle_file_path)

    for x, y in zip(tree.states.values(), pt.states.values()):
        assert x.is_equivalent(y)

    os.remove(pickle_file_path)


def test_remove_trivial_loops_single_file():
    traces_path = "tests/resources/traces_single"
    tree = PrefixTreeFactory().get_prefix_tree(
        PROJECT_ROOT.joinpath(traces_path),
        PROJECT_ROOT.joinpath("resources/config.json"),
        True)
    assert len(tree) == 13  # 12 + root


def test_remove_trivial_loops_several():
    traces_path = "tests/resources/testlogs"
    tree = PrefixTreeFactory().get_prefix_tree(
        PROJECT_ROOT.joinpath(traces_path),
        PROJECT_ROOT.joinpath("resources/config.json"),
        True)

    assert len(tree) == 36  # 35 + root





