import gevent

from .Task import Task
from .Story import Story
from .utils import _parse_body, _repoowner_reponame, _index_story

from Jumpscale import j


class GiteaBot:
    """Gitea specific bot for Storybot
    """

    LABEL_STORY = "type_story"

    def __init__(self, token=None, api_url="", base_url="", repos=None):
        """GiteaBot constructor
        
        Keyword Arguments:
            token str -- Gitea API token (default: None)
            url str -- gitea API url
            repos list -- List of repos the GiteaBot should watch (can be `username/repo` or 
                `repo` that will be assumed to be the user's own repo) (default: [])

        Raises:
            ValueError -- if token was not provided
            ValueError -- if url was not provided
        """
        data = {}
        if not token:
            raise j.exceptions.Value("Token was not provided and is mandatory")
        data["gitea_token_"] = token

        if api_url == "":
            raise j.exceptions.Value("api url was not provided and is mandatory")
        data["url"] = api_url

        self.client = j.clients.gitea.get(data=data, interactive=False)
        self.username = self.client.api.user.userGetCurrent()[0].login
        self.api_url = api_url
        self.base_url = base_url
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
            repos_l = self.client.api.users.userListRepos(user)[0]
        except Exception as err:
            self._log_error("Something went wrong getting Gitea repos from user '%s': %s" % (user, err))
            return repos

        for r in repos_l:
            repos.append(user + "/" + r.name)

        return repos

    def get_stories(self):
        """Loop over all provided repos return a list of stories found in the issues

        Returns:
            [Story] -- A list of stories (Story) on the provided Gitea repos
        """
        self._log_info("Checking for stories on gitea...")
        stories = []

        if not self.repos:
            self._log_info("No repos provided to the Gitea bot")
            return stories

        gls = []
        for repo in self.repos:
            gls.append(gevent.spawn(self._get_story_repo, repo))

        gevent.joinall(gls)
        for gl in gls:
            stories.extend(gl.value)

        self._log_info("Done checking for stories on Gitea!")
        return stories

    def _get_story_repo(self, repo):
        """Get stories from a single repo
        
        Arguments:
            repo str -- Name of Gitea repo
        
        Returns:
            [Story] -- List of stories (Story) found in repo
        """
        self._log_debug("checking repo '%s'" % repo)
        stories = []

        repoowner, reponame = _repoowner_reponame(repo, self.username)

        # skip wildcard repos
        if reponame == "*":
            return stories

        try:
            issues = self.client.api.repos.issueListIssues(reponame, repoowner, query_params={"state": "all"})[0]
        except Exception as err:
            self._log_error("Could not fetch Gitea repo '%s': %s" % (repo, err))
            return stories

        for iss in issues:
            html_url = self._parse_html_url(repoowner, reponame, iss.number)

            self._log_debug("checking issue '%s'" % html_url)
            # not a story if no type story label
            if not self.LABEL_STORY in [label.name for label in iss.labels]:
                continue
            # check title format
            title = iss.title
            if title[-1:] == ")":
                start_i = title.rfind("(")
                if start_i == -1:
                    self._log_error("issue title of %s has a closeing bracket, but no opening bracket", html_url)
                    continue
                story_title = title[start_i + 1 : -1]
                story_desc = title[:start_i].strip()
                stories.append(
                    Story(
                        title=story_title,
                        url=html_url,
                        description=story_desc,
                        state=iss.state,
                        update_func=self._update_iss_func(iss.number, reponame, repoowner),
                        body=iss.body,
                    )
                )

        return stories

    def find_tasks_and_link(self, stories=None):
        """Loop over all provided repos and see if there are any issues related to provided stories.
        Link them if so.

        Keyword Arguments:
            stories [Story] -- List of stories (default: None)

        Returns:
            [Task] -- List of tasks (Task) found in the provided Gitea repos
        """
        self._log_info("Linking tasks on Gitea to stories...")

        if not stories:
            self._log_info("No stories provided to link Gitea issues with")
            return
        if not self.repos:
            self._log_info("No repos provided to the Gitea bot")
            return

        gls = []
        for repo in self.repos:
            gls.append(gevent.spawn(self._link_issues_stories_repo, repo, stories))
        gevent.joinall(gls)
        tasks = []
        for gl in gls:
            tasks.extend(gl.value)

        self._log_info("Done linking tasks on Gitea to stories!")

        return tasks

    def _link_issues_stories_repo(self, repo, stories):
        """links issues from a single repo with stories

        Arguments:
            repo str -- Name of Gitea repo
            stories [Story] --List of stories (Story) to link with

        Returns:
            [Task] -- List of tasks (Task) found in the provided repo
        """
        self._log_debug("checking repo '%s'" % repo)
        tasks = []
        repoowner, reponame = _repoowner_reponame(repo, self.username)
        # skip wildcard repos
        if reponame == "*":
            return tasks

        try:
            issues = self.client.api.repos.issueListIssues(reponame, repoowner, query_params={"state": "all"})[0]
        except Exception as err:
            self._log_error("Could not fetch Gitea repo '%s': %s" % (repo, err))
            return tasks

        for iss in issues:
            title = iss.title
            html_url = self._parse_html_url(repoowner, reponame, iss.number)

            self._log_debug("checking issue: %s" % html_url)
            end_i = title.find(":")
            if end_i == -1:
                self._log_debug("issue is not a story task")
                continue
            found_titles = [item.strip() for item in title[:end_i].split(",")]
            data = {}
            data["body"] = iss.body
            for story_title in found_titles:
                story_i = _index_story(stories, story_title)
                story = stories[story_i]
                if story_i == -1:
                    self._log_debug("Story title was not in story list")
                    continue
                # update task body
                self._log_debug("Parsing task issue body")
                try:
                    data["body"] = _parse_body(data["body"], story)
                except RuntimeError as err:
                    self._log_error("Something went wrong parsing body for %s:\n%s" % (html_url, err))
                    continue
                self.client.api.repos.issueEditIssue(data, str(iss.number), reponame, repoowner)

                # update story with task
                self._log_debug("Parsing story issue body")
                desc = title[end_i + 1 :].strip()
                task = Task(
                    url=html_url,
                    description=desc,
                    state=iss.state,
                    body=data["body"],
                    update_func=self._update_iss_func(iss.number, reponame, repoowner),
                )
                try:
                    story.update_list(task)
                except RuntimeError as err:
                    self._log_error("Something went wrong parsing body for %s:\n%s" % (task.url, err))
                    continue
                # if task already present replace it with current task
                if task in tasks:
                    tasks[tasks.index(task)] = task
                # if not, add task to list
                else:
                    tasks.append(task)

        return tasks

    def _update_iss_func(self, iss_number, repo, owner):
        def updater(body):
            data = {}
            data["body"] = body
            self.client.api.repos.issueEditIssue(data, str(iss_number), repo, owner)

        return updater

    def _parse_html_url(self, owner, repo, iss_number):
        """Tries to parse a html page url for a Gitea issue
        
        Arguments:
            issue clients.gitea.client.Issue.Issue -- Gitea Issue
            owner str -- repo owner
            repo str -- repo name
            iss_number int/str -- issue number of repo
        """
        url = self.base_url
        if url == "":
            self._logger("Gitea base url not found, trying to parse it from api url")
            url = self.api_url
            if url.endswith("/"):
                url = url[:-1]
            if url.endswith("/api/v1"):
                url = url[:-7]
            url = url.replace("api.", "")

            self.base_url = url

        if url.endswith("/"):
            url = url[:-1]

        url += "/%s/%s/issues/%s" % (owner, repo, str(iss_number))

        return url
