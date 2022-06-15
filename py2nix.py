#! /usr/bin/env python
"Generate a flake.nix for Python package using setuptools metadata"
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, ArgumentTypeError
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from textwrap import dedent
from typing import Any, Optional, Sequence

from setuptools.config.setupcfg import read_configuration


def indent(s: str, levels: int = 1) -> str:
	return ("\n" + "\t" * levels).join(s.splitlines())


@dataclass
class NixPyProj:
	path: Path

	@cached_property
	def conf(self) -> dict[str, Any]:
		return read_configuration(self.path)

	@property
	def deps(self) -> list[str]:
		return [n.replace('.', '-') for n in self.conf["options"].get("install_requires", [])]

	def __getattr__(self, attr: str) -> Optional[str]:
		return self.conf["metadata"].get(attr)

	def pkg(self) -> str:
		return dedent(f"""\
			{self.name} = python.pkgs.buildPythonPackage rec {{
				pname = "{self.name}";
				version = "{self.version}";
				src = {self.path.resolve().parent};
				propagatedBuildInputs = with python.pkgs; [ {' '.join(self.deps)} ];

				doCheck = false;

				meta = with lib; {{
					homepage = "{self.url}";
					description = "{self.description}";
					maintainers = with maintainers; [ padhia ];
				}};
			}};""")


def gen_flake(letvars: str, nixpkgs: str) -> str:
	return dedent(f"""\
		{{
		description = "Flake to manage python workspace";

		inputs = {{
			nixpkgs.url = "github:nixos/nixpkgs/{nixpkgs}";
			flake-utils.url = "github:numtide/flake-utils";
		}};

		outputs = {{ self, nixpkgs, flake-utils }}:
			flake-utils.lib.eachDefaultSystem (system:
				with nixpkgs.legacyPackages.${{system}};
				{indent(letvars, 4)}

				in {{
					inherit defaultPackage devShell;
				}}
			);
		}}""")


def gen_shell(letvars: str) -> str:
	return dedent(f"""\
		{{ pkgs ? import <nixpkgs> {{}} }}:
		with pkgs;
		{indent(letvars, 2)}

		in
			devShell""")


def let_vars(name: str, pyver: str, projs: list[NixPyProj]) -> str:
	xs = "\n\n".join(p.pkg() for p in projs)

	return dedent(f"""\
		let
			python = python{pyver};

			{indent(xs, 3)}

			defaultPackage = python.withPackages (p: with p; [
				pip setuptools wheel pytest mypy twine
				{' '.join((p.name or '') for p in projs)}
			]);

			devShell = mkShell {{
				name = "{name}";
				buildInputs = with python.pkgs; [
					python
					pip setuptools wheel pytest mypy twine
					{' '.join((p.name or '') for p in projs)}
				];
			}};
		""")


def main(inputs: Sequence[Path], name: str, pyver: str, shell: bool, nixpkgs: str) -> None:
	"script entrypoint"
	let = let_vars(name, pyver, [NixPyProj(p) for p in inputs])
	nix_script = gen_shell(let) if shell else gen_flake(let, nixpkgs)
	print(nix_script.rstrip().replace('\t', '  '))


def getargs():
	"run-time arguments"
	parser = ArgumentParser(description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)

	def pyproj(s: str) -> Path:
		proj = Path(s)
		if proj.is_dir():
			cfg = proj / "setup.cfg"
			if cfg.is_file():
				return cfg
		elif proj.name == "setup.cfg":
			return proj
		raise ArgumentTypeError("Invalid python project")

	parser.add_argument('inputs', metavar='PATH', type=pyproj, nargs='+', help='Python project setup.cfg file or a directory containing one')
	parser.add_argument('--pyver', default="310", help='Python version')
	parser.add_argument('--name', default="my", help='shell name')
	parser.add_argument('--nixpkgs', default="nixos-unstable", help='nixpkgs branch')
	parser.add_argument('--shell', action='store_true', help='generate script for shell.nix')

	return parser.parse_args()


def cli() -> Any:
	"cli entry-point"
	main(**vars(getargs()))


if __name__ == '__main__':
	cli()
