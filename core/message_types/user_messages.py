from .irc_module_template import IRCModule
from .numeric_replies import Reply

class UserMessages(IRCModule):
    def __init__(self):
        pass

    def privmsg_handler(self, bot,
                        cmd, pref, args, text):
        channel = args[0]
        if "lowercase" in text:
            name, sep, rest = pref.partition("!")
            ident, sep, host = rest.partition("@")


            bot.irc_networking.send_msg("PRIVMSG", [channel],
                                        "Uppercase: {0}, lowercase: {1}".format(
                                            bot.tools.name_upper(name),
                                            bot.tools.name_lower(name)
                                        ))
        elif text.startswith("say "):
            start, rest = text.split("say ", 1)
            bot.irc_networking.send_msg("PRIVMSG", [channel], rest+" ")

        elif text.startswith("shutdown"):
            raise RuntimeError("Shutting down")

    def set_message_handlers(self, set_handler):
        set_handler("PRIVMSG", self.privmsg_handler)