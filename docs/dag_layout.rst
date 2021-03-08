DAG Layout
===========

Determining a suitable position to assign each item in a 
kanbanitem's dependency tree is not terribly simple, since it is
not, in fact, a tree, but instead a Direct Acyclic Graph(DAG).


The current algorithm is a minimal proof of concept, achieving
 relatively little save successfully placing items without 
overlapping them.

It is a variant of Depth First Search, and is written recursively.

The primary reason that it isn't optimal is that it can mostly 
only assign a single column to a single item, so it's wasting a 
lot of display space.

The other issue is more about the GUI framework, which doesn't
really support zooming in on the conventional (old style) widgets.
Unfortunately, this is what the application is written with, and 
converting it to the new graphics framework is more trouble than it seems worth right now.

In the future, it may be adventageous to use a better layout 
algorithm, possibly the one graphviz's dot tool uses.