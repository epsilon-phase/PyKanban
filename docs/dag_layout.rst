DAG Layout
===========

Determining a suitable position to assign each item in a 
kanbanitem's dependency tree is not terribly simple, since it is
not, in fact, a tree, but instead a Direct Acyclic Graph(DAG).


The current algorithm is a minimal proof of concept, achieving
 relatively little save successfully placing items without 
overlapping them.

It is a variant of Depth First Search, and is written recursively.

In our tests, it manages to place items in roughly 30% of the area
available to it, assuming that the hierarchies are similar to those 
in our test case.

The other issue is more about the GUI framework, which doesn't
really support zooming in on the conventional (old style) widgets.
Unfortunately, this is what the application is written with, and 
converting it to the graphics framework is more trouble than it seems worth right now.

In the future, it may be adventageous to use a better layout 
algorithm, possibly the one graphviz's dot tool uses.