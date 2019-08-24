from .StoryBot import StoryBot

from Jumpscale import j

JSConfigBaseFactory = j.application.JSFactoryConfigsBaseClass


class StoryBotFactory(JSConfigBaseFactory):
    def __init__(self):
        self.__jslocation__ = "j.tools.storybot"
        JSConfigBaseFactory.__init__(self, StoryBot)
