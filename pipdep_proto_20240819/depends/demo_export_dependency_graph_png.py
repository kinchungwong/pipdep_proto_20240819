from pathlib import Path

from pipdep_proto_20240819._internals.utils import print_banner
from pipdep_proto_20240819._internals.package_info import PackageInfo
from pipdep_proto_20240819._internals.package_set import PackageSet
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
        "requests",
    ]
    png_output_dir = "do_not_commit/outputs"
    fn_png_output_name = lambda name: (name + "_deps")
    for package in packages:
        included = PackageSet()
        included.add_resolved(dg, package)
        png_output_name = fn_png_output_name(included._infos[0].path_safe_name)
        dg_exp = DependencyGraphExporter(dg, included)
        dot = dg_exp.export_digraph()
        dot.render(
            directory=png_output_dir, 
            filename=png_output_name, 
            format="png", 
            cleanup=False,
        )

    print_banner()
