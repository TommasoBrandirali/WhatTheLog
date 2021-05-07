import bisect
from typing import Union, Tuple, Any, List


class SparseMatrix:
    """
    As we had no efficient way to store the edges, we implemented our own approach to achieve this.
    """

    separator = '.'

    def __init__(self):
        # The list in which the sparse matrix is stored
        self.list: List[str] = list()

    def __setitem__(self, key: Tuple[int, int], value: Any) -> None:
        """
        Set item in SparseMatrix using insertion sort.
        """
        index = self.find_index(key)
        if index is None:
            bisect.insort_right(self.list, str(key[0]) + self.separator + str(key[1]) + self.separator + str(value))
        else:
            self.list[index] = str(key[0]) + self.separator + str(key[1]) + self.separator + str(value)

    def __getitem__(self, key: Tuple[int, int]) -> str:
        """
        Get item from SparseMatrix using binary search.
        """
        value: str = self.find_edge(key)
        if value is None:
            raise KeyError
        return value

    def __contains__(self, item: Tuple[int, int]) -> bool:
        """
        Checks if an edge exists.
        """
        index: int = self.bisearch(self.list, str(item[0]) + self.separator + str(item[1]))
        if index != len(self.list):
            return True
        return False

    def __find_index(self, search_list: List[str], item: Tuple[int, int]) -> Union[int, None]:
        """
        Use binary search to search for a specific entry in the list of the SparseMatrix.
        """
        index: int = self.bisearch(search_list, str(item[0]) + self.separator + str(item[1]) + self.separator)
        if index != len(self.list):
            return index
        else:
            return None

    def find_index(self, coordinates: Tuple[int, int]) -> Union[int, None]:
        """
        Use binary search to search for a specific entry in the given list.
        Return the index of the entry in the entry list, or None if no entry found.
        :param coordinates: the coordinates of the entry to find.
        :return the index of the input entry, or None if no entry found.
        """
        return self.__find_index(self.list, coordinates)

    def find_edge(self, coordinates: Tuple[int, int]) -> Union[str, None]:
        """
        Use binary search to search for a specific entry value in the given list.
        Return the value of the entry, or None if no entry found.
        :param coordinates: the coordinates of the entry to find.
        :return the value of the input entry, or None if no entry found.
        """
        return self.get_values(self.find_index(coordinates))[2]

    def __find_children(self, search_list: List[str], item: int) -> Union[List[Tuple[int, str]], None]:
        """
        Use binary search to search for all children of the given entry in an input list.
        Return a list of tuples in the form (child_number, value), or None if no child found.
        :param search_list: the list of entries to search for matches.
        :param item: the item to match on.
        :return a list of tuples (child_number, value), or None if no child found.
        """
        index: int = self.bisearch(search_list, str(item) + self.separator)

        if index != len(search_list):
            current = self.get_values(search_list, index)
            result = [(current[1], current[2])]
            idx = index - 1
            while idx >= 0 and search_list[idx].startswith(str(item) + self.separator):
                current = self.get_values(search_list, idx)
                result.append((current[1], current[2]))
                idx -= 1
            idx = index + 1
            while idx < len(search_list) and search_list[idx].startswith(str(item) + self.separator):
                current = self.get_values(search_list, idx)
                result.append((current[1], current[2]))
                idx += 1
            return result
        else:
            return None

    def find_children(self, item: int) -> Union[List[Tuple[int, str]], None]:
        """
        Use binary search to search for all children of the given entry in the main list.
        Return a list of tuples in the form (child_number, value), or None if no child found.
        :param item: the item to match on.
        :return a list of tuples (child_number, value), or None if no child found.
        """
        return self.__find_children(self.list, item)

    @staticmethod
    def bisearch(arr: List[str], target: str) -> int:
        """
        Perform a binary search on the prefix (of unspecified length) of the elements
        """
        low: int = 0
        high: int = len(arr) - 1
        while high >= low:
            ix = (low + high) // 2
            if arr[ix].startswith(target):  # todo make this more efficient maybe?
                return ix
            elif target < arr[ix]:
                high = ix - 1
            else:
                low = ix + 1
        return len(arr)

    @staticmethod
    def get_values(array: List[str], index: int) -> Tuple[int, int, str]:
        """
        Retrieves the tuple of coordinates and value for the given index.
        Raises an exception if the index is out of bounds.
        :param array: The sparse matrix list
        :param index: the index of the tuple to fetch.
        :return a tuple in the form(start_node, end_node, edge_value)
        """
        if index < 0 or index >= len(array):
            raise IndexError

        value: str = array[index]
        strings = value.split('.', 2)
        return int(strings[0]), int(strings[1]), strings[2]

    def get_parents(self, i: int) -> List[int]:
        """
        Return all the entries which are linked to the input entry.
        :param i: the input entry
        :return: the list of parent entries
        """

        copy = self.list.copy()
        reverse = []
        for item in copy:
            parent, child, props = item.split('.', 2)
            bisect.insort_right(reverse, f"{child}.{parent}.{props}")

        children = self.__find_children(reverse, i)

        return [tup[0] for tup in self.__find_children(reverse, i)] if children is not None else []

    def __len__(self):
        return len(self.list)

    def __str__(self):
        return str(self.list)
