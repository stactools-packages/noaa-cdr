import stactools.core
from stactools.cli.registry import Registry

stactools.core.use_fsspec()


def register_plugin(registry: Registry) -> None:
    from stactools.noaa_cdr import commands

    registry.register_subcommand(commands.create_noaa_cdr_command)


__version__ = "0.1.0"
