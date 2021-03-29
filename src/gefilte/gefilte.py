# search syntax: https://support.google.com/mail/answer/7190?hl=en

import collections
import contextlib
import inspect
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.dom import minidom

import gefilte


class GFilter:
    def __init__(self, fish, conditions):
        self.fish = fish
        self.conditions = conditions
        self.actions = []

    def __repr__(self):
        return f"<{self.__class__.__name__}: cond={self.conditions} act={self.actions!r}>"

    def _filter(self, name, value):
        return self.__class__(self.fish, self.conditions + [(name, value)])

    def has(self, words):
        return self._filter("hasTheWord", words)

    def subject(self, words):
        return self._filter("subject", words)

    def hasnot(self, words):
        return self._filter("doesNotHaveTheWord", words)

    def from_(self, words):
        return self._filter("from", words)

    def to(self, words):
        return self._filter("to", words)

    def cc(self, words):
        return self.has(f"cc:({words})")

    def bcc(self, words):
        return self.has(f"bcc:({words})")

    def replyto(self, words):
        return self.has(f"replyto:({words})")

    def list_(self, words):
        return self.has(f"list:({words})")

    def elif_(self, filter):
        prev_conds = self.conditions[:-1]
        last_key, last_val = self.conditions[-1]
        this_cond = filter.conditions[-1]
        return self.__class__(self.fish, prev_conds + [(last_key, self.not_(last_val)), this_cond])

    def else_(self):
        prev_conds = self.conditions[:-1]
        last_key, last_val = self.conditions[-1]
        return self.__class__(self.fish, prev_conds + [(last_key, self.not_(last_val))])

    def _add_entry(self, elt):
        if not self.actions:
            return

        entry = SubElement(elt, "entry")

        conditions = collections.defaultdict(list)
        for cname, cvalue in self.conditions:
            conditions[cname].append(cvalue)
        for cname, cvalue in conditions.items():
            prop = SubElement(entry, "apps:property")
            prop.set("name", cname)
            prop.set("value", " ".join(cvalue))

        for aname, avalue in self.actions:
            prop = SubElement(entry, "apps:property")
            prop.set("name", aname)
            prop.set("value", avalue)

    def __enter__(self):
        self.fish.push_filter(self)
        return self

    def __exit__(self, *args):
        self.fish.finish_filter(self)

    def _add_action(self, name, value):
        self.actions.append((name, value))
        return self

    def label(self, label):
        return self._add_action("label", label)

    def star(self):
        return self._add_action("shouldStar", "true")

    def never_spam(self):
        return self._add_action("shouldNeverSpam", "true")

    def skip_inbox(self):
        return self._add_action("shouldArchive", "true")

    def mark_important(self):
        return self._add_action("shouldAlwaysMarkAsImportant", "true")

    def delete(self):
        return self._add_action("shouldTrash", "true")

    def exact(self, phrase):
        return f'"{phrase}"'

    def not_(self, thing):
        if isinstance(thing, str):
            return f"-{thing}"
        elif isinstance(thing, GFilter):
            key, val = thing.conditions[-1]
            return thing.fish._filter(key, self.not_(val))

    def or_(self, *things):
        assert len(set(type(t) for t in things)) == 1
        if isinstance(things[0], str):
            return "(" + " OR ".join(things) + ")"
        elif isinstance(things[0], GFilter):
            conds = [filt.conditions[-1] for filt in things]
            assert len(set(k for k,v in conds)) == 1
            key = conds[0][0]
            val = self.or_(*[v for k,v in conds])
            new_filt = things[0].fish._filter(key, val)
            return new_filt


class GefilteFish:
    def __init__(self, filter_class=GFilter):
        self.filter_class = filter_class
        self.filters = [self.filter_class(self, [])]
        self.dom = Element("feed")
        self.dom.set("xmlns", "http://www.w3.org/2005/Atom")
        self.dom.set("xmlns:apps", "http://schemas.google.com/apps/2006")
        self.dom.append(Comment(f" Made by gefilte {gefilte.__version__}: {gefilte.__url__} "))

    def push_filter(self, filter):
        self.filters.append(filter)

    def finish_filter(self, filter):
        assert self.filters[-1] is filter
        filter._add_entry(self.dom)
        self.filters.pop()

    def __getattr__(self, name):
        return getattr(self.filters[-1], name)

    @contextlib.contextmanager
    def dsl(self):
        meths = {meth for meth in dir(self.filter_class) if not meth.startswith("_")}
        caller_scope = inspect.stack()[2][0].f_locals
        orig_values = {}
        for meth in meths:
            if meth in caller_scope:
                orig_values[meth] = caller_scope[meth]
            caller_scope[meth] = (
                lambda meth=meth:
                    lambda *args, **kwargs:
                        getattr(self, meth)(*args, **kwargs)
                )()

        yield

        for meth in meths:
            if meth in orig_values:
                caller_scope[meth] = orig_values[meth]
            else:
                del caller_scope[meth]

    def xml(self):
        """Return a pretty-printed XML string for the Element."""
        rough_string = ElementTree.tostring(self.dom, "utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="    ")
