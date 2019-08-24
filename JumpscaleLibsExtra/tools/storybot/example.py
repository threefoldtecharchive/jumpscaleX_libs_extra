from Jumpscale import j

# Get the storybot instance and ask for the configuration settings interactively
bot = j.tools.storybot.get(instance="main", interactive=True)


# Run the storybot once
bot.link_stories()

# Add a github repository
bot.add_github_repos("chrisvdg/storybot_test")

# List github repositories
bot.github_repos

# remove github repo
bot.remove_github_repos("chrisvdg/storybot_test")

# List github repositories
bot.github_repos

# Run with interval and check for broken item urls
# Stop by pressing ctrl+c
bot.link_stories_interval(interval=30, check_broken_urls=True)
