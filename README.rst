##########################
Gefilte GMail filter maker
##########################

Gefilte automates the creation of GMail filters.

Use it like this::

    from gefilte import GefilteFish, GFilter

    class GitHubFilter(GFilter):
        def repo(self, repo_name):
            org, repo = repo_name.split("/")
            return self.list_(f"{repo}.{org}.github.com")

    fish = GefilteFish(GitHubFilter)

    with fish.dsl():
        with replyto("noreply-spamdigest@google.com"):
            never_spam()
            mark_important()

        with subject(exact("[Confluence]")).has(exact("liked this page")):
            label("liked")

        with from_("notifications@github.com"):
            skip_inbox()

            with repo("myproject/tasks") as f:
                label("todo")
                with f.elif_(repo("otherproject/something")) as f:
                    label("otherproject")
                    with f.else_():
                        label("Code reviews")

            with from_("renovate[bot]"):
                delete()

            with to("author@noreply.github.com"):
                label("mine").star()

            with has('Merged, "into master"'):
                label("merged")

            with repo("myproject/tasks") as f:
                label("todo")
                with f.elif_(repo("otherproject/something")) as f:
                    label("otherproject")
                    with f.else_():
                        label("Code reviews")

            for who, where in [
                ("Joe Junior", "myproject/component1"),
                ("Francine Firstyear", "myproject/thing2"),
            ]:
                with from_(exact(who)).repo(where):
                    label("mentee").star()

        for toaddr, the_label in [
            ("info@mycompany.com", "info@"),
            ("security@mycompany.com", "security@"),
            ("con2020@mycompany.com", "con20"),
            ("con2021@mycompany.com", "con21"),
        ]:
            with to(toaddr):
                label(the_label)

    print(fish.xml())

The output will be XML.  Save it in a file.  Go to GMail - Settings - Filters
and Blocked Addresses.  Then "Import Filters", "Choose File", "Open File", then
"Create Filters".  You might want to select "Apply new filters to existing
email."


Changelog
=========

0.5.0 -- 2021-03-28
-------------------

First version.
