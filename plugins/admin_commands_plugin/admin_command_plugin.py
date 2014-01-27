from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import permissions, UserLevels
import packets
from utility_functions import give_item_to_player


class UserCommandPlugin(SimpleCommandPlugin):
    """
    Provides a simple chat interface to the user manager.
    """
    name = "user_management_commands"
    depends = ['command_dispatcher', 'player_manager']
    commands = ["who", "whois", "kick", "ban", "kickban", "give_item"]
    auto_activate = True

    def activate(self):
        super(UserCommandPlugin, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager
        self.godmode = {}

    @staticmethod
    def extract_name(l):
        name = []
        if l[0][0] not in ["'", '"']:
            return l[0], l[1:]
        name.append(l[0][1:])
        terminator = l[0][0]
        for idx, s in enumerate(l[1:]):
            if s[-1] == terminator:
                name.append(s[:-1])
                if idx + 2 != len(l):
                    return " ".join(name), l[idx + 2:]
                else:
                    return " ".join(name), None
            else:
                name.append(s)
        raise ValueError("Final terminator character of <%s> not found" %
                         terminator)

    def who(self, data):
        who = [w.colored_name(self.config.colors) for w in self.player_manager.who()]
        self.protocol.send_chat_message("Players online: %s" % " ".join(who))
        return False

    @permissions(UserLevels.ADMIN)
    def whois(self, data):
        name = " ".join(data)
        info = self.player_manager.whois(name)
        if info:
            self.protocol.send_chat_message(
                "Name: %s\nUserlevel: %s\nUUID: %s\nIP address: %s""" % (
                    info.colored_name(self.config.colors), UserLevels(info.access_level), info.uuid, info.ip))
        else:
            self.protocol.send_chat_message("Player not found!")
        return False

    @permissions(UserLevels.MODERATOR)
    def kick(self, data):
        """Kicks a user from the server. Syntax: /kick [username] [reason]"""
        name, reason = self.extract_name(data)
        if reason is None:
            reason = "no reason given"
        info = self.player_manager.whois(name)
        if info and info.logged_in:
            tp = self.protocol.factory.protocols[info.protocol]
            tp.die()
            self.protocol.factory.broadcast("%s kicked %s (reason: %s)" %
                                            (self.protocol.player.name,
                                             info.name,
                                             " ".join(reason)))
        return False

    @permissions(UserLevels.ADMIN)
    def ban(self, data):
        """Bans an IP. Syntax: /ban [ip address]"""
        ip = data[0]
        self.player_manager.ban(ip)
        self.protocol.send_chat_message("Banned IP: %s" % ip)
        return False

    @permissions(UserLevels.ADMIN)
    def kickban(self, data):
        """Kicks a player and then bans their IP. Syntax: /kickban [username] [reason]"""
        player, reason = self.extract_name(data)
        return False

    @permissions(UserLevels.ADMIN)
    def bans(self, data):
        """Lists the currently banned IPs. Syntax: /bans"""
        self.protocol.send_chat_message("\n".join(
            "IP: %s " % self.player_manager.bans))

    @permissions(UserLevels.ADMIN)
    def unban(self, data):
        """Unbans an IP. Syntax: /unban [ip address]"""
        ip = data[0]
        for ban in self.player_manager.bans:
            if ban.ip == ip:
                self.player_manager.session.delete(ban)
                self.protocol.send_chat_message("Unbanned IP: %s" % ip)
                break
        else:
            self.protocol.send_chat_message("Couldn't find IP: %s" % ip)
        return False

    @permissions(UserLevels.ADMIN)
    def give_item(self, data):
        """Gives an item to a player. Syntax: /give [target player] [item name] [optional: item count]"""
        name, item = self.extract_name(data)
        target_player = self.player_manager.get_by_name(name)
        target_protocol = self.protocol.factory.protocols[target_player.protocol]
        if target_player is not None:
            if len(item) > 0:
                item_name = item[0]
                if len(item) > 1:
                    item_count = item[1]
                else:
                    item_count = 1
                give_item_to_player(target_protocol, item_name, item_count)
                target_protocol.send_chat_message(
                    "%s has given you: %s (count: %s)" % (
                    self.protocol.player.name, item_name, item_count))
                self.protocol.send_chat_message("Sent the item(s).")
            else:
                self.protocol.send_chat_message("You have to give an item name.")
        else:
            self.protocol.send_chat_message("Couldn't find name: %s" % name)
        return False

