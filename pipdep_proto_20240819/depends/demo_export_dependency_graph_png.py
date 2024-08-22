from pathlib import Path

from pipdep_proto_20240819._internals.utils import print_banner
from pipdep_proto_20240819._internals.dependency_graph import DependencyGraph
from pipdep_proto_20240819._internals.dependency_graph_exporter import DependencyGraphExporter


if __name__ == "__main__":
    print_banner()

    workspace_dir = Path.cwd()
    source_dir = workspace_dir / "data/mock/google_colab_python3.10_20240819"
    dg = DependencyGraph(source_dir)

    packages = [
        # "opencv",
        "numpy",
        "opencv-python",
        "opencv-contrib-python",
        "numba",
        "Cython",
        "pandas",
    ]

    dg_exp = DependencyGraphExporter(dg, packages)
    dot = dg_exp.export_digraph()
    dot.render(filename="dependency_graph", format="png", cleanup=False)

    print_banner()
