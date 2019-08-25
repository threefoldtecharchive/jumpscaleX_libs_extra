from .StoryBot import StoryBot

from Jumpscale import j

JSConfigBaseFactory = j.baseclasses.object_config_collection


class StoryBotFactory(JSConfigBaseFactory):
    __jslocation__ = "j.tools.storybot"
