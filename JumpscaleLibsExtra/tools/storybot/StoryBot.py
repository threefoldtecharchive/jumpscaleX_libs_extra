# Docs can be found at docs/tools/StoryBot.md

import time
import signal

from .GithubBot import GithubBot
from .GiteaBot import GiteaBot
from .utils import _extend_stories

import gevent
from Jumpscale import j

TEMPLATE = """
github_token_ = ""
github_repos = ""
gitea_api_url = "https://docs.grid.tf/api/v1"
gitea_base_url = "https://docs.grid.tf/"
gitea_token_ = ""
gitea_repos = ""
"""

JSConfigBase = j.baseclasses.object


class StoryBot(JSConfigBase):
    """
    Story bot will automaticall link story issues and task/bug/FR issues with each other.

    For more higher level information on the tool, check StoryBot.md
    """

    def __init__(self, instance, data=None, parent=None, interactive=False):
        """StoryBot constructor
        """
        JSConfigBase.__init__(
            self, instance=instance, data=data, parent=parent, template=TEMPLATE, interactive=interactive
        )

    @property
    def github_repos(self):
        """Returns the Github repositories as comma seperated string
        (Returned directly from config)
        
        Returns:
            str -- Comma seperated list of Github repositories
        """
        return self.config.data["github_repos"]

    @property
    def github_repos_list(self):
        """Returns the Github repositories as list

        Returns:
            [str] -- List of Github repositories
        """
        return [item.strip() for item in self.config.data["github_repos"].split(",")]

    def add_github_repos(self, repos=""):
        """Add new Github repositories to the configuration
        
        Keyword Arguments:
            repos str -- comma seperated string of repositories (default: "")
        """
        repos = repos.strip()
        if not repos.startswith(","):
            repos = "," + repos

        data = self.config.data["github_repos"]
        if data != "":
            data += repos
        else:
            data += repos[1:]
        self.config.data_set("github_repos", data)

    def remove_github_repos(self, repos=""):
        """Remove Github repositories from the configuration
        
        Keyword Arguments:
            repos str -- comma seperated string of repositories (default: "")
        """
        repos_list = [x.strip() for x in repos.split(",")]
        new_list = self.github_repos_list

        for repo_to_remove in repos_list:
            # loop till all items are removed, just to make sure doubles are removed
            while True:
                try:
                    new_list.remove(repo_to_remove)
                # this is thrown when item was no in list
                except ValueError:
                    break

        data = self.config.data["github_repos"]
        data = ",".join(new_list)
        self.config.data_set("github_repos", data)

    @property
    def gitea_repos(self):
        """Returns the Gitea repositories as comma seperated string
        (Returned directly from config)
        
        Returns:
            str -- Comma seperated list of Gitea repositories
        """
        return self.config.data["gitea_repos"]

    @property
    def gitea_repos_list(self):
        """Returns the Gitea repositories as list

        Returns:
            [str] -- List of Gitea repositories
        """
        return [item.strip() for item in self.config.data["gitea_repos"].split(",")]

    def add_gitea_repos(self, repos=""):
        """Add new Gitea repositories to the configuration
        
        Keyword Arguments:
            repos str -- comma seperated string of repositories (default: "")
        """
        repos = repos.strip()
        if not repos.startswith(","):
            repos = "," + repos

        data = self.config.data["gitea_repos"]
        if data != "":
            data += repos
        else:
            data += repos[1:]
        self.config.data_set("gitea_repos", data)

    def remove_gitea_repos(self, repos=""):
        """Remove Gitea repositories from the configuration
        
        Keyword Arguments:
            repos str -- comma seperated string of repositories (default: "")
        """
        repos_list = [x.strip() for x in repos.split(",")]
        new_list = self.gitea_repos_list

        for repo_to_remove in repos_list:
            # loop till all items are removed, just to make sure doubles are removed
            while True:
                try:
                    new_list.remove(repo_to_remove)
                # this is thrown when item was no in list
                except ValueError:
                    break

        data = self.config.data["gitea_repos"]
        data = ",".join(new_list)
        self.config.data_set("gitea_repos", data)

    def link_stories_interval(self, interval=60, check_broken_urls=False):
        """Links stories and tasks from configured repositories together.
        Then waits the specified interval before running it again.

        Stop by pressing 'ctrl+c'.
        
        Keyword Arguments:
            interval int -- Wait interval in minutes (default: 60)
            check_broken_urls bool -- Check the story/task lists from broken links/URLs (default: False)
        """

        self._log_info("Running StoryBot every %s minutes.\nPress ctl+c to stop." % interval)
        try:
            while True:
                self.link_stories(check_broken_urls=check_broken_urls)

                time.sleep(interval * 60)
        except KeyboardInterrupt:
            self._log_info("Stopping StoryBot")

    def link_stories(self, check_broken_urls=False):
        """Link stories and tasks from all repos to eachother.
        Single run.
        
        Keyword Arguments:
            check_broken_urls bool -- Check the story/task lists from broken links/URLs (default: False)
        """

        gevent.signal(signal.SIGQUIT, gevent.kill)

        github_bot = None
        gitea_bot = None
        if self.config.data["github_repos"] != "":
            # create github bot
            token = self.config.data["github_token_"]
            repos = self.github_repos_list
            github_bot = GithubBot(token=token, repos=repos)

        if self.config.data["gitea_repos"] != "":
            # create gitea bot
            token = self.config.data["gitea_token_"]
            api_url = self.config.data["gitea_api_url"]
            base_url = self.config.data["gitea_base_url"]
            repos = self.gitea_repos_list
            gitea_bot = GiteaBot(token=token, api_url=api_url, base_url=base_url, repos=repos)

        # ask stories from bots
        start = time.time()
        gls = []
        if github_bot:
            gls.append(gevent.spawn(github_bot.get_stories))
        if gitea_bot:
            gls.append(gevent.spawn(gitea_bot.get_stories))

        # collect stories
        stories = []
        gevent.joinall(gls)
        for gl in gls:
            stories = _extend_stories(stories, gl.value)
        end = time.time()
        self._log_debug("Fetching stories took %ss" % (end - start))

        if not stories:
            self._log_debug("No stories were found, skipping linking task to stories")
            return
        self._log_debug("Found stories: %s", stories)

        # link task with stories with stories
        start = time.time()
        gls = []
        if github_bot:
            gls.append(gevent.spawn(github_bot.find_tasks_and_link, stories=stories))

        if gitea_bot:
            gls.append(gevent.spawn(gitea_bot.find_tasks_and_link, stories=stories))
        tasks = []
        gevent.joinall(gls)
        for gl in gls:
            tasks.extend(gl.value)
        end = time.time()
        self._log_debug("Linking stories took %ss" % (end - start))
        self._log_debug("Found tasks: %s", tasks)

        if check_broken_urls:
            start = time.time()
            gls = []
            self._log_info("Checking lists for broken urls...")
            # check story bodies
            for s in stories:
                gls.append(gevent.spawn(s.check_broken_urls))
            # check task bodies
            for t in tasks:
                gls.append(gevent.spawn(t.check_broken_urls))

            gevent.joinall(gls)
            end = time.time()
            self._log_info("Done checking lists for broken urls")
            self._log_debug("Checking lists for broken urls took %ss" % (end - start))
