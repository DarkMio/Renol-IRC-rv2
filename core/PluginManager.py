from logging import getLogger
import pkgutil
from abc import ABCMeta, abstractmethod
from inspect import getargspec

class PluginManager:
    def __init__(self, plugin_path='./plugins/'):
        self._path = plugin_path
        self.logger = getLogger('PluginManager')
        self._plugins = []
        self._commands = {}

    def load_responders(self):
        """
        Loads all plugins from ./plugins/, appends them to a list of responders and verifies that they're properly setup
        and working for the main bot process.
        """
        # preparing the right sub path.
        package = self._path
        prefix = package.__name__ + "."

        # we're running through all
        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
            module = __import__(modname, fromlist="dummy")
            # every sub module has to have an object provider,
            # this makes importing the object itself easy and predictable.
            module_object = module.init()
            try:
                if not isinstance(module_object, PluginBase):
                    raise ImportError('Module {} does not inherit from PluginBase class'.format(
                        module_object.__class__.__name__))
                # could / should fail due to variable validation
                # (aka: is everything properly set to even function remotely.)
                module_object.integrity_check()
                self.logger.info('Module "{}" is initialized and ready.'.format(module_object.__class__.__name__))
            except Exception as e:
                # Catches _every_ error and skips the module. The import will now be reversed.
                self.logger.error("{}: {}".format(module_object.__class__.__name__, e))
                del module, module_object
                continue
            # If nothing failed, it's fine to import.
            # First register the module,
            self._plugins.append(module_object)
            # then register the command.
            module_commands = module_object.commands
            for k, v in module_commands.items():
                if k not in self._commands:
                    self._commands.update({k: v})
                else:
                    self.logger.error("Command {cmd} is already mapped, "
                                      "{mdl}:{cmd} not imported.".format(cmd=k, mdl=module_object.__name__))
        self.logger.info("Imported a total of {} object(s).".format(len(self._plugins)))


class PluginBase(metaclass=ABCMeta):
    command_args = ('name', 'params', 'channel', 'user_data', 'rank')

    def __init__(self):
        self.logger = getLogger('plugin')
        self._commands = {}
        self.commands_verified = False

    def integrity_check(self):
        assert self._commands, "No command mapping"

    @property
    def commands(self):
        """
        Filters out unmapped commands, possibly broken commands as well later
        :return: Dict with ``{command: function}``
        """
        if not self._commands:
            self.logger.warn("{} has no commands or aliases".format(self.__class__.__name__))
        functions = {}
        for k, v in self._commands.items():
            if v and type(v) is 'function':
                argspec = getargspec(v)
                # either all params or kwargs are implemented
                if argspec.keywords or all(arg in argspec.args for arg in self.command_args):
                    functions.update({k: v})
                else:
                    self.logger.error("{}:{} does not implement parameters or **kwargs".format(self.__class__.__name__,
                                                                                               v.__name__))
        self.commands_verified = True
        return functions
