import dataclasses
from dataclasses import dataclass
from typing import NewType

VerStr = NewType("VerStr", str)

@dataclass
class PackageInfo:
    """Information about a package, as seen in the json output from the 
    command "pip show".

    Attributes:
        name: str
            Name of installed package, as it appears on the json.
        version: VerStr
            Version string of the installed package.
        aliases: set[str]
            List of strings that map to the same package. This is used
            for handling non-standard package names which require normalization.
        dependencies: set[str]
            List of package names that this package depends on.
            The names are not normalized; each name is used as it appears on the json.
        _internal_id: int = -1
            Internal identifier for the package.
    """
    name: str
    version: VerStr = None
    aliases: set[str] = dataclasses.field(default_factory=set[str])
    dependencies: set[str] = dataclasses.field(default_factory=set[str])
    _internal_id: int = -1
