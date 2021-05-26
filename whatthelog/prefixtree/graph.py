# ****************************************************************************************************
# Imports
# ****************************************************************************************************

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# External
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import random
import os
from typing import List, Union, Dict

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Internal
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from whatthelog.syntaxtree.syntax_tree import SyntaxTree
from whatthelog.prefixtree.state import State
from whatthelog.auto_printer import AutoPrinter
from whatthelog.exceptions import StateAlreadyExistsException, StateDoesNotExistException
from whatthelog.prefixtree.sparse_matrix import SparseMatrix
from whatthelog.prefixtree.edge_properties import EdgeProperties
from whatthelog.prefixtree.state_properties import StateProperties

random.seed(os.environ['random_seed'] if 'random_seed' in os.environ else 5)


# ****************************************************************************************************
# Utilities
# ****************************************************************************************************

def template_matches_state(template: str, state: State) -> bool:
    return template in state.properties.log_templates


# ****************************************************************************************************
# Graph
# ****************************************************************************************************

class Graph(AutoPrinter):
    """
    Class implementing a graph
    """

    __slots__ = ['syntax_tree', 'edges', 'states', 'state_indices_by_id', 'prop_by_hash', 'start_node']

    def __init__(self, syntax_tree: SyntaxTree, start_node: State = None):

        self.syntax_tree = syntax_tree
        self.edges = SparseMatrix()
        self.states: Dict[int, State] = {}
        self.state_indices_by_id: Dict[int, int] = {}
        self.prop_by_hash: Dict[int, StateProperties] = {}
        self.start_node = start_node

    def get_state_by_id(self, state_id: int):
        """
        Method to fetch the state object from its hash.
        :param state_id: the hash of the state to fetch
        :return: the state object
        """
        if state_id not in self.state_indices_by_id:
            raise StateDoesNotExistException()
        return self.states[self.state_indices_by_id[state_id]]

    def get_outgoing_states_not_self(self, current: State) -> List[State]:
        """
        Retrieves the outgoing states of a given state, excluding itself in case of a self-loop.
        :param current: The state of which we want to retrieve the outgoing states.
        :return: All the outgoing states, excluding itself in case of a self-loop. In this case that the state is not
                 present, we return an empty list
        """
        outgoing = self.get_outgoing_states(current)
        if outgoing:
            return list(filter(lambda x: x is not current, outgoing))
        else:
            return []

    def merge_states(self, state1: State, state2: State) -> None:
        """
        This method merges two states and passes the properties from one state to the other.
        :param state1: The new 'merged' state
        :param state2: The state that will be deleted and which properties will be passed to state 1
        """

        props = state1.properties.log_templates.copy()

        for temp in state2.properties.log_templates:
            if temp not in state1.properties.log_templates:
                props.append(temp)
        state1.properties = StateProperties(props)

        if state2.is_terminal:
            state1.is_terminal = True

        if state2 is self.start_node:
            self.start_node = state1

        if state1.properties.get_prop_hash() in self.prop_by_hash:
            state1.properties = self.prop_by_hash[state1.properties.get_prop_hash()]
        else:
            self.prop_by_hash[state1.properties.get_prop_hash()] = state1.properties

        self.edges.change_parent_of_children(self.state_indices_by_id[id(state1)],
                                             self.state_indices_by_id[id(state2)])

        self.edges.change_children_of_parents(self.state_indices_by_id[id(state2)],
                                              self.state_indices_by_id[id(state1)])

        del self.states[self.state_indices_by_id[id(state2)]]
        del self.state_indices_by_id[id(state2)]
        del state2

    def add_state(self, state: State) -> None:
        """
        Method to add a new state to the graph.

        :param state: State to add
        :raises StateAlreadyExistsException: if state already exists
        """

        if state in self:
            raise StateAlreadyExistsException()

        curr_index = len(self.states)
        self.states[curr_index] = state
        self.state_indices_by_id[id(state)] = curr_index

        if state.properties.get_prop_hash() in self.prop_by_hash:
            state.properties = self.prop_by_hash[state.properties.get_prop_hash()]
        else:
            self.prop_by_hash[state.properties.get_prop_hash()] = state.properties

    def add_edge(self, start: State, end: State, props: EdgeProperties = EdgeProperties()) -> bool:
        """
        Method to add an edge to the graph

        :param start: Origin state of the edge
        :param end: Destination state of the edge
        :param props: the edge properties object
        :return: Whether adding the edge was successful. If one of the nodes in
        edge does not exist or edge already exists returns False else True.
        """

        if id(start) not in self.state_indices_by_id or id(end) not in self.state_indices_by_id:
            return False

        start_index = self.state_indices_by_id[id(start)]
        end_index = self.state_indices_by_id[id(end)]
        if not (start_index, end_index) in self.edges:

            self.edges[start_index, end_index] = str(props)
            return True
        return False

    def size(self):
        """
        Method to get the size of the graph.

        :return: Number of states
        """
        return len(self.states)

    def get_outgoing_props(self, state: State) -> Union[List[EdgeProperties], None]:
        """
        Method to get outgoing edges of a state.

        :param state: State to get outgoing edges for
        :return: List of outgoing edges from state.
        If state does not exist return None.
        """
        if state in self:
            results = self.edges.find_children(self.state_indices_by_id[id(state)])
            return [EdgeProperties.parse(result[1]) for result in results]
        else:
            return None

    def get_outgoing_states(self, state: State) -> Union[List[State], None]:
        """
        Method to get outgoing states of a state.

        :param state: State to get outgoing states for
        :return: List of outgoing edges from state.
        If state does not exist return None.
        """
        if state in self:
            results = self.edges.find_children(self.state_indices_by_id[id(state)])
            return [self.states[result[0]] for result in results] if results is not None else []
        else:
            return None

    def get_incoming_states(self, state: State):
        """
                Method to get outgoing states of a state.

                :param state: State to get outgoing states for
                :return: List of outgoing edges from state.
                If state does not exist return None.
                """
        if state in self:
            results = self.edges.get_parents(self.state_indices_by_id[id(state)])
            return [self.states[result] for result in results] if results else []
        else:
            return None

    def update_edge(self, start: State, end: State, passes: int = 1):
        """
        Method to update an edge by adding a given number of passes (default is 1).
        :param start: the start node of the edge
        :param end: the end node of the edge
        :param passes: the number of passes to update the edge with (default is 1)
        :return: True if the update succeeded, else otherwise
        """

        if id(start) not in self.state_indices_by_id or id(end) not in self.state_indices_by_id:
            return False

        start_index = self.state_indices_by_id[id(start)]
        end_index = self.state_indices_by_id[id(end)]
        if (start_index, end_index) in self.edges:
            self.edges[start_index, end_index] = int(self.edges[start_index, end_index]) + passes
            return True
        return False

    def match_trace(self, trace: List[str]) -> Union[List[State], None]:
        """
        Checks if a given trace matches a path in the graph.
        First, the first line is checked against the start node of the graph.
        If it fits, a successor that matches the next line is picked and the list
        is traversed recursively.

        :param trace: The lines to be matched against the tree.
        :return: If the trace corresponds to a sequence of states in the graph,
                 those states are returned in order. If no match is found, None is returned.
        """

        if len(trace) == 0:
            # If the trace is empty, then it has been fully parsed
            return []

        # Check which state the current line belongs to
        template = self.syntax_tree.search(trace[0])

        # If no state is found, return None
        if template is None:
            return None

        # Get the root's children
        root_children = list(
            filter(lambda s: template_matches_state(template.name, s),
                   self.get_outgoing_states(self.start_node)))

        # If no suitable option, return
        if len(root_children) == 0:
            return None

        # Randomly pick first suitable state
        current_state: State = random.choice(root_children)

        # Check if the template matches the root of the state tree
        if template_matches_state(template.name, current_state):

            # If the trace is exactly one line long, return the root state if it is terminal
            if len(trace) == 1:
                return [current_state] \
                    if [s for s in self.get_outgoing_states(current_state) if s.is_terminal] \
                    else None

            # Remove the checked line from trace
            trace[:] = trace[1:]

            # Find the state for the second line
            template = self.syntax_tree.search(trace[0])

            # If no state is found, raise an exception
            if template is None:
                return None

            # Check if any of the children of current node contain the template in their state
            children: List[State] = self.get_outgoing_states(current_state)
            successor: List[State] = list(filter(
                lambda next_state: template_matches_state(template.name, next_state),
                children))

            if len(successor) == 0:
                # If none found, the trace cannot be matched
                return None
            else:
                # Pick a random suitable next node
                # TODO: Should this be removed through an invariant in the prefix tree?
                next_node: State = random.choice(successor)

                # Continue the search recursively
                tail: List[State] = self.match_trace_rec(next_node, trace[1:])

                if tail is None:
                    # If the search failed, return none
                    return None
                else:
                    # If it was successful, prepend the current state
                    tail.insert(0, current_state)
                    return tail

    def match_trace_rec(self,
            current_state: State,
            trace: List[str]) -> Union[List[State], None]:
        """
        Recursive helper for the match_trace function. This function recursively
        finds the next state in the graph for the first line in the trace
        if any exists.

        :param current_state: The current state of the graph
        :param trace: The lines to be matched against the tree.
        :return: If the trace corresponds to a sequence of states in the prefix tree,
                 those states are returned in order. If no match is found, None is returned.
        """

        res = [current_state]

        while len(trace) != 0:
            # Find the template of the first line in the syntax tree
            template = self.syntax_tree.search(trace[0])

            # If no state is found, raise an exception
            if template is None:
                return None

            # Check if any of the children of current node contain the template in their state
            children: List[State] = self.get_outgoing_states(current_state)
            successor: List[State] = list(
                filter(lambda next_state: template_matches_state(template.name, next_state), children))

            if len(successor) == 0:
                # If none found, the trace cannot be matched
                return None
            else:
                # Pick a random suitable next node
                current_state = random.choice(successor)

                # Append result to the list of states
                res.append(current_state)

                # Remove first trace
                trace = trace[1:]

        if [state.is_terminal for state in self.get_outgoing_states(current_state) if state.is_terminal]:
            return res
        return None

    def __str__(self):
        return str(self.states)

    def __contains__(self, item: State):
        return id(item) in self.state_indices_by_id

    def __len__(self):
        return len(self.states)
