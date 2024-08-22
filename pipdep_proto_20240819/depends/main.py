import os
from os.path import join as path_join

from pipdep_proto_20240819._internals.utils import print_banner
from pipdep_proto_20240819._internals.dependency_graph import DependencyGraph


if __name__ == "__main__":
    print_banner()
    workspace_dir = os.getcwd()
    source_dir = path_join(workspace_dir, "data/mock/google_colab_python3.10_20240819")
    dg = DependencyGraph(source_dir)
    print_banner()
    for pkinfo in dg.installed:
        print(pkinfo)
    print_banner()
