# PyKanban

A small kanban application written in python.

To read how to use it, look at [Starting Out](docs/starting_out.rst)


## Features

* Remembers what file you had open(Yes, groundbreaking stuff here) :3
* Customize some styling of your tasks by category
* Task dependency tracking.
* Lightweight file format
* Filtering


## Todo


* [ ] Task Dependency visualization
    * [ ] Ideally a tree display
* [X] Task categorization
* [X] Filtering
* [X] Searching
* [ ] Cycle Detection
    * Exists in the code, but doesn't have any indication that it 
      happens in the UI
* Alternative views of the tasks remaining
    - [ ] Queue View

      Just show what tasks are immediately doable, for those times when you 
      have no idea what you want to work on, but know that there are things you need to do
    - [ ] Tree View

      Keep track of the dependencies of some goal that you are working towards.
* Stretch ideas
    - Integration with Github/Gitlab issues

      This one could be problematic and difficult for a number of reasons, among them that we have no plans to add richer text support, nor threads of comments, which kinda elides the reasons to use github/gitlab issues in the first place
    - More modern UI styles
      
      Although we believe our code is probably okay, it's written using a rather old set of UI paradigms, mostly with regards to the lack of using Qt's data models for listwidgets, for example. And this limits what we can acheive with the UI in quite a few ways.

      Also in this category are things like smoother UIs, such as the sort that have things like tweening and animations.
