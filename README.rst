################################
Gefilte Fish: GMail filter maker
################################

Gefilte Fish automates the creation of GMail filters.  You write a Python
program using gefilte's domain-specific language (DSL), run the program, and
import the XML it creates.

Sample Python
=============

Here's an example of creating filters:

.. code-block:: python

    from gefilte import GefilteFish, GFilter

    # Specialize GFilter for repo-specific GitHub notifications.
    class GitHubFilter(GFilter):
        def repo(self, repo_name):
            org, repo = repo_name.split("/")
            return self.list_(f"{repo}.{org}.github.com")

    # Make the filter-maker and use its DSL. All of the methods of GitHubFilter
    # are now usable as global functions.
    fish = GefilteFish(GitHubFilter)
    with fish.dsl():

        # Google's spam moderation messages should never get sent to spam.
        with replyto("noreply-spamdigest@google.com"):
            never_spam()
            mark_important()

        # If the subject and body have these, label it "liked".
        with subject(exact("[Confluence]")).has(exact("liked this page")):
            label("liked")

        # We get a lot of notifications from GitHub,
        # we'll make a number of filters that apply.
        with from_("notifications@github.com"):

            # Skip the inbox (archive them).
            skip_inbox()

            # Notifications from some repos are special.
            with repo("myproject/tasks") as f:
                label("todo")
                with f.elif_(repo("otherproject/something")) as f:
                    label("otherproject")
                    with f.else_():
                        # But everything else goes into "Code reviews".
                        label("Code reviews")

            # Delete annoying bot messages.
            with from_("renovate[bot]"):
                delete()

            # GitHub sends to synthetic addresses to provide information.
            with to("author@noreply.github.com"):
                label("mine").star()

            with has('Merged, "into master"'):
                label("merged")

            # Data-driven filters. I'm mentoring these people
            # on these projects so make sure they get my attention.
            for who, where in [
                ("Joe Junior", "myproject/component1"),
                ("Francine Firstyear", "myproject/thing2"),
            ]:
                with from_(exact(who)).repo(where):
                    label("mentee").star().mark_important()

        # Some inbound addresses come to me. Mark them so
        # I understand what I'm looking at in my inbox.
        for toaddr, the_label in [
            ("info@mycompany.com", "info@"),
            ("security@mycompany.com", "security@"),
            ("con2020@mycompany.com", "con20"),
            ("con2021@mycompany.com", "con21"),
        ]:
            with to(toaddr):
                label(the_label)

    print(fish.xml())

The ``with`` clauses create nested contexts in which all of the enclosing
filters apply.  The ``elif_`` and ``else_`` structures are a little awkward,
but easier than manually making filters with the same effect.


Installing filters
==================

When you run your program, it will create XML output.  Save that output in a
file.  In your browser, go to GMail - Settings - Filters and Blocked Addresses.
Then "Import Filters", "Choose File", "Open File", then "Create Filters".

.. note::
   Be careful with the "Apply new filters to existing email" choice.  "Delete"
   actions that run on incoming email will delete individual messages, but when
   run during import, they delete the entire conversation the message is in.

For more information about filtering in GMail, see `Search operators you can
use with Gmail`__.

__ https://support.google.com/mail/answer/7190?hl=en


License
=======

The code in this repository is licensed under the Apache Software License 2.0
unless otherwise noted.  See ``LICENSE.txt`` for details.


Changelog
=========

0.5.1 --- 2022-02-23
--------------------

- Removed unneeded vestigial XML elements from the output.


0.5.0 --- 2021-03-28
--------------------

First version.
