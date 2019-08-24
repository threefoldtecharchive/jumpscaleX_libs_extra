import gevent

from .Task import Task
from .Story import Story
from .utils import _index_story, _parse_body, _repoowner_reponame

from Jumpscale import j


class GithubBot:
    """Github specific bot for Storybot
    """

    LABEL_STORY = "type_story"

    def __init__(self, token=None, repos=None):
        """Github bot constructor
        
        Keyword Arguments:
            token string -- github API token (default: None)
            repos list -- List of repos the githubbot should watch (can be `username/repo` or 
                `repo` that will be assumed to be the user's own repo) (default: [])

        Raises:
            ValueError -- if token was not provided
        """
        data = {}
        if not token:
            raise j.exceptions.Value("Token was not provided and is mandatory")

        data["token_"] = token
        self.client = j.clients.github.get(data=data, interactive=False)
        self.username = self.client.api.get_user().login
        self._repos = repos

    @property
    def repos(self):
        """Returns a list of repos

        Returns
            [str] -- String list of repositories

        Raises:
            ValueError -- Invalid repo name in provided repo list
        """
        repos = []

        # Get the repo owner and repo name and uniquely add them to the repos list
        for r in self._repos:
            repoowner, reponame = _repoowner_reponame(r, self.username)
            r = repoowner + "/" + reponame
            if r not in repos:
                repos.append(r)

        self._repos = repos

        # If wildcard reponame, fetch all repos from repoowner
        gls = []
        for r in repos:
            repoowner, reponame = _repoowner_reponame(r, self.username)
            if reponame == "*":
                # fetch all repos from repoowner
                gls.append(gevent.spawn(self._get_all_repos_user, repoowner))

        gevent.joinall(gls)

        # add found repositories uniquely
        # these are not added to the local repo list as this property would fetch the wildcard repos at the time of call
        for gl in gls:
            to_add = gl.value
            for r in to_add:
                if r not in repos:
                    repos.append(r)

        return repos

    def _get_all_repos_user(self, user):
        """Returns list of repositories from provided user
        
        Arguments:
            user str -- username/owner of repositories to fetch from

        Returns:
            [str] -- String list of repositories
        """
        repos = []
        try:
            repos_l = self.client.api.get_user(user).get_repos()
        except Exception as err:
            self._log_error("Something went wrong getting Github repos from user '%s': %s" % (user, err))
            return repos

        for r in repos_l:
            repos.append(user + "/" + r.name)

        return repos

    def get_stories(self):
        """Loop over all provided repos return a list of stories found in the issues

        Returns:
            [Story] -- A list of stories (Story) found in the provided github repos
        """
        self._log_info("Checking for stories on github...")
        stories = []

        if not self.repos:
            self._log_info("No repos provided to the Github bot")
            return stories

        gls = []
        for repo in self.repos:
            gls.append(gevent.spawn(self._get_story_repo, repo))

        gevent.joinall(gls)
        for gl in gls:
            stories.extend(gl.value)

        self._log_info("Done checking for stories on github!")
        return stories

    def _get_story_repo(self, repo):
        """Get stories from a single repo
        
        Arguments:
            repo str -- Name of Github repo
        
        Returns:
            [Story] -- List of stories (Story) found in repo
        """
        self._log_debug("checking repo '%s'" % repo)
        stories = []
        repoowner, reponame = _repoowner_reponame(repo, self.username)
        # skip wildcard repos
        if reponame == "*":
            return stories

        # get issues
        try:
            repo = self.client.api.get_user(repoowner).get_repo(reponame)
        except Exception as err:
            self._log_error("Could not fetch Github repo '%s': %s" % (repo, err))
            return stories

        issues = repo.get_issues(state="all")
        # loop issue pages
        i = 0
        while True:
            page = issues.get_page(i)
            self._log_debug("Issue page: %s" % i)
            if len(page) == 0:
                self._log_debug("page %s is empty" % i)
                break
            i += 1

            for iss in page:
                self._log_debug("checking issue '%s'" % iss.html_url)
                # not a story if no type story label
                if not self.LABEL_STORY in [label.name for label in iss.labels]:
                    continue
                # check title format
                title = iss.title
                if title[-1:] == ")":
                    # get story title
                    start_i = title.rfind("(")
                    if start_i == -1:
                        self._log_error(
                            "issue title of %s has a closeing bracket, but no opening bracket", iss.html_url
                        )
                        continue
                    story_title = title[start_i + 1 : -1]
                    story_desc = title[:start_i].strip()
                    stories.append(
                        Story(
                            title=story_title,
                            url=iss.html_url,
                            description=story_desc,
                            state=iss.state,
                            update_func=self._update_iss_func(iss),
                            body=iss.body,
                        )
                    )

        return stories

    def find_tasks_and_link(self, stories=None):
        """Loop over all provided repos and see if there are any issues related to provided stories.
        Link them if so.

        Returns a list of found tasks.

        Keyword Arguments:
            stories [Story] -- List of stories (default: None)

        Returns:
            [Task] -- List of tasks (Task) found in the provided Github repos
        """
        self._log_info("Linking tasks on github to stories...")

        if not stories:
            self._log_info("No stories provided to link Github issues with")
            return
        if not self.repos:
            self._log_info("No repos provided to the Github bot")
            return

        gls = []
        for repo in self.repos:
            gls.append(gevent.spawn(self._link_issues_stories_repo, repo, stories))
        gevent.joinall(gls)
        tasks = []
        for gl in gls:
            tasks.extend(gl.value)

        self._log_info("Done linking tasks on github to stories!")

        return tasks

    def _link_issues_stories_repo(self, repo, stories):
        """links issues from a single repo with stories

        Arguments:
            repo str -- Name of Github repo
            stories [Story] --List of stories (Story) to link with

        Returns:
            [Task] -- List of tasks (Task) found in the provided repo
        """
        self._log_debug("Repo: %s" % repo)
        tasks = []
        repoowner, reponame = _repoowner_reponame(repo, self.username)
        # skip wildcard repos
        if reponame == "*":
            return tasks

        # get issues
        try:
            repo = self.client.api.get_user(repoowner).get_repo(reponame)
        except Exception as err:
            self._log_error("Could not fetch Github repo '%s': %s" % (repo, err))
            return tasks
        issues = repo.get_issues(state="all")
        # loop issue pages
        i = 0
        while True:
            page = issues.get_page(i)
            self._log_debug("Issue page: %s" % i)
            if len(page) == 0:
                self._log_debug("page %s is empty" % i)
                break
            i += 1

            for iss in page:
                title = iss.title
                self._log_debug("Issue: %s" % title)
                end_i = title.find(":")
                if end_i == -1:
                    self._log_debug("issue is not a story task")
                    continue
                found_titles = [item.strip() for item in title[:end_i].split(",")]
                body = iss.body
                for story_title in found_titles:
                    story_i = _index_story(stories, story_title)
                    story = stories[story_i]
                    if story_i == -1:
                        self._log_debug("Story title was not in story list")
                        continue
                    # update task body
                    self._log_debug("Parsing task issue body")
                    try:
                        body = _parse_body(body, story)
                    except RuntimeError as err:
                        self._log_error("Something went wrong parsing body for %s:\n%s" % (iss.html_url, err))
                        continue
                    iss.edit(body=body)

                    # update story with task
                    self._log_debug("Parsing story issue body")
                    desc = title[end_i + 1 :].strip()
                    task = Task(
                        url=iss.html_url,
                        description=desc,
                        state=iss.state,
                        body=body,
                        update_func=self._update_iss_func(iss),
                    )
                    try:
                        story.update_list(task)
                    except RuntimeError as err:
                        self._log_error("Something went wrong parsing body for %s:\n%s" % (task.url, err))
                        continue
                    if task in tasks:
                        tasks[tasks.index(task)] = task
                    else:
                        tasks.append(task)

        return tasks

    def _update_iss_func(self, issue):
        """Returns a function that can update a task issue with provided body
        
        Arguments:
            issue github.Issue.Issue -- Github issue
        
        Returns:
            [type] -- [description]
        """

        def updater(body):
            issue.edit(body=body)

        return updater
