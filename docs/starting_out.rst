
============
Starting Out
============

.. _Starting Out:

Kanban is a very simple way that you can organize tasks and manage your projects.

This means that it may very well be ideal for your usage.

Tasks are organized by whether or not they are blocked, that is, they depend on another task to be completed before the task itself can be done. 
Once a task is completed the tasks that depend on it may be placed back into the available column. 

At some point it would be a good idea to add things like tasks that exist to track what they depend on, but for now you may simply set such a task to completed and it will be handled appropriately.

So, the basic workflow here is:

1. Create top level task
2. Create subsidiary tasks to whatever granularity you like

	Set dependencies, set categories
3. Work through them, going back to 2 whenever it feels appropriate 
    (such as when you underestimated the amount of work required to do something as a monolithic task)

Item creation and editing Dialog
--------------------------------

This is where you set the various fields of a task such as:

- Name

  The name used to refer to the task in brief
- Description

  Longer description of the task, specifications, etc
- Priority
  
  The urgency that a task should be considered with
- Depends On
  
  The list of tasks that this one depends on to be completed
- Dependents Of

  The list of tasks that depend on the task being edited.
- Categories

  Metadata to permit further categorization based on whatever reasoning you prefer.

No fields are required, but in general you'll probably want to have
at least a name and description. 

A current flaw in the application as of now is that you have to set 
the task as being dependent on the parent task, this is just a tad 
annoying to do, but we are currently considering ways to improve 
this experience

The Categories of an item are edited in their own dialog, 
which permits you to create new categories, change which ones are 
selected out of the current pool, etc.

No changes are applied to the task until you press the accept button.

Category Editing
----------------

Categories are able to have foreground and background colors 
assigned to them, in order to make the items more distinct in the
UI. Once set they can be cleared.


Example: Managing tasks for this project
----------------------------------------

When we were first writing this, we decided that we should maintain
the task tracking in this software so we know how it feels like to use.

First we created a task called "1.0 Milestones", which we will use 
as a collection of tasks that we need to do before we will feel okay
with calling it released.

Then we created three more tasks, Fix Bugs, Add Features, and 
Improve UI. (The latter was a later addition to the three after it became clear we hadn't struck gold in the first iteration).

Then we added, Add search, Add categories, fix column flickering

+--------------+-----------------------+
|Task Name     |Depends on             |
+--------------+-----------------------+
|1.0 Milestone |- Fix Bugs             |
|              |- Add Features         |
|              |- Improve UI           |
+--------------+-----------------------+
|Fix Bugs      |- Fix Column Flickering|
+--------------+-----------------------+
|Add Features  |- Add Search           |
|              |- Add Categories       |
+--------------+-----------------------+

Categories then necessitated the addition of further
 tasks, Create Category Assignment UI, Allow styling 
based on categories.

+---------------+-----------------------------------+
|Task Name      |Depends On                         |
+---------------+-----------------------------------+
|Add Categories |- Category Assignment UI           |
|               |- Allow Styling Based on Categories|
+---------------+-----------------------------------+

Working through the tasks produces a relatively 
sensible ordering of a set of tasks that you can 
proceed through in without too much thought [1]_.

Setting priorities on tasks allow further control 
over what order tasks are presented to you in.

.. [1] At least, if you're someone like us who don't much care for forethought

