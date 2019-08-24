from Jumpscale import j
import unittest, uuid, requests
from github import Github
from testconfig import config


class GitHubTests(unittest.TestCase):
    @classmethod
    def random_string(cls):
        return str(uuid.uuid4()).replace("-", "")[:5]

    @classmethod
    def create_repo(cls):
        repo_name = "storybot-test-repo-{}".format(cls.random_string())
        response = cls.session.post("https://api.github.com/user/repos", json={"name": repo_name})
        response.raise_for_status
        return response.json()["full_name"]

    @classmethod
    def delete_repo(cls, repo_name):
        response = cls.session.delete("https://api.github.com/repos/{}".format(repo_name))
        response.raise_for_status

    @classmethod
    def setUpClass(cls):
        token = config["Github"]["token"]
        cls.session = requests.Session()
        cls.session.headers.update({"Authorization": "token {}".format(token)})

        # create testing repo
        repo = cls.create_repo()

        # configure the bot
        data = {"github_repos": repo, "github_token_": token}
        cls.bot = j.tools.storybot.get("storybot-test", data=data, interactive=False)

        # configure github client
        cls.github = Github(token)
        cls.repo = cls.github.get_repo(repo)
        cls.type_story_label = cls.repo.create_label(name="type_story", color="2471A3")

    def create_story(self, name):
        description = self.random_string()
        body = self.random_string()
        title = "{} ({})".format(description, name)
        return self.repo.create_issue(title, labels=[self.type_story_label], body=body)

    def create_task(self, name, stories):
        title = "{}: {}".format(",".join(stories), name)
        body = self.random_string()
        return self.repo.create_issue(title, body=body)

    @classmethod
    def tearDownClass(cls):
        cls.delete_repo(cls.repo.full_name)

    def test01_link_stories(self):
        """SBT-001

        #. Create story 1.
        #. Create task 1 under Story 1.
        #. Link stories.
        #. Check that Story 1 and task are linked to each other.
        """

        # create story 1
        story_name = self.random_string()
        story = self.create_story(name=story_name)

        # create story 2
        task_name = self.random_string()
        task = self.create_task(name=task_name, stories=[story_name])

        # link stories
        self.bot.link_stories()

        # check that Story 1 and task are linked to each other
        story = self.repo.get_issue(number=story.number)
        task = self.repo.get_issue(number=task.number)

        self.assertIn("[ ] [{}".format(story_name), task.body)
        self.assertIn("[ ] [{}]".format(task_name), story.body)

    def test02_multiple_stories(self):
        """SBT-002

        #. Create story 1.
        #. Create story 2.        
        #. Create task 1 under Story 1 and Story 2.
        #. Link stories.
        #. Check that Story 1, Story 2 and task 1 are linked to each other.
        """

        # create story 1
        story_1_name = self.random_string()
        story_1 = self.create_story(name=story_1_name)

        # create story 2
        story_2_name = self.random_string()
        story_2 = self.create_story(name=story_2_name)

        # create task 1
        task_name = self.random_string()
        task = self.create_task(name=task_name, stories=[story_1_name, story_2_name])

        # link stories
        self.bot.link_stories()

        # Check that Story 1, Story 2 and task 1 are linked to each other
        story_1 = self.repo.get_issue(number=story_1.number)
        story_2 = self.repo.get_issue(number=story_2.number)
        task = self.repo.get_issue(number=task.number)

        self.assertIn("[ ] [{}".format(story_1_name), task.body)
        self.assertIn("[ ] [{}".format(story_2_name), task.body)

        self.assertIn("[ ] [{}]".format(task_name), story_1.body)
        self.assertIn("[ ] [{}]".format(task_name), story_2.body)

    def test03_test_close_reopen_task(self):
        """SBT-003

        #. Create story 1.
        #. Create task 1 under Story 1.
        #. Link stories.
        #. Check that Story 1 and task are linked to each other.
        #. Close task 1, check that task 1 checkbox is checked.
        #. Reopen task 1, check that task 1 checkbox is unchecked.
        """

        # create story 1
        story_name = self.random_string()
        story = self.create_story(name=story_name)

        # create task 1
        task_name = self.random_string()
        task = self.create_task(name=task_name, stories=[story_name])

        # link stories
        self.bot.link_stories()

        # check that stories have been linked
        story = self.repo.get_issue(number=story.number)
        task = self.repo.get_issue(number=task.number)
        self.assertIn("[ ] [{}]".format(task_name), story.body)

        # close task 1
        task.edit(state="closed")

        # link stories
        self.bot.link_stories()

        # check that task checkbox is checked in story page
        story = self.repo.get_issue(number=story.number)
        self.assertIn("[x] [{}]".format(task_name), story.body)

        # reopen task 1
        task.edit(state="open")

        # link stories
        self.bot.link_stories()

        # check that task 1 checkbox is ubchecked in story page
        story = self.repo.get_issue(number=story.number)
        self.assertIn("[ ] [{}]".format(task_name), story.body)
