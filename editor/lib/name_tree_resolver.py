import typing

class NameTreeResolver:
    resolver_items: dict
    name_func: function
    parent_func: function

    _raise_on_errors = True
    _is_resolved = False

    def __init__(self, name_func: function, parent_func: function, raise_on_errors: bool=True):
        self.resolver_items = {}
        self.name_func = name_func
        self.parent_func = parent_func
        self._raise_on_errors = raise_on_errors

    def add_resolver_item(self, item: typing.Any):
        name = self.name_func(item)
        self.resolver_items[name] = ResolverItem(item, 
                                                 name, 
                                                 self.parent_func(item))
        self._is_resolved = False

    def resolve(self):
        item: ResolverItem

        # Clear resolver data in case we run through multiple times
        for (key, item) in self.resolver_items.items():
            item.clear_resolved_info()

        # Assign according to parent_name
        for (key, item) in self.resolver_items.items():
            if item.resolver_parent_name is not None:
                if not item.resolver_parent_name in self.resolver_items:
                    if self._raise_on_errors:
                        raise ValueError('Parent does not exist!')
                    continue

                if self.resolver_items[item.resolver_parent_name]:
                    item.parent = self.resolver_items[item.resolver_parent_name]
                    item.parent.children.append(item)

        self._is_resolved = True

    def __ensure_resolved(self) -> True:
        if not self._is_resolved:
            self.resolve()
        return True

    def ordered(self) -> list[tuple[str, typing.Any]]:
        self.__ensure_resolved()

        # Generate a flattened sequence
        results = []
        item: ResolverItem
        for item in self.__sorted_parents():
            self.__resolve_item(item, results)
        return results

    def __sorted_parents(self):
        return sorted(self.__parent_items(), key=lambda x: x.resolver_name)

    def __parent_items(self) -> typing.Iterator[ResolverItem]:
        item: ResolverItem
        for (key, item) in self.resolver_items.items():
            if item.parent is None:
                yield item

    def __resolve_item(self, resolver_item: ResolverItem, results: list[tuple[str, typing.Any]]):
        results.append((resolver_item.resolver_name, resolver_item.resolver_item))
        for child in sorted(resolver_item.children, key=lambda x: x.resolver_name):
            self.__resolve_item(child, results)

    def reverse_order(self) -> list[tuple[str, typing.Any]]:
        results = self.ordered()
        results.reverse()
        return results


class ResolverItem:
    resolver_item: object
    resolver_name: str
    resolver_parent_name: str|None

    parent: ResolverItem|None
    children: list[ResolverItem]

    def __init__(self, item, resolver_name: str, resolver_parent: str|None=None):
        self.resolver_item = item
        self.resolver_name = resolver_name
        self.resolver_parent_name = resolver_parent

        # These will be populated later by NameTreeResolver.resolve_order
        self.clear_resolved_info()

    def clear_resolved_info(self):
        self.parent = None
        self.children = []
