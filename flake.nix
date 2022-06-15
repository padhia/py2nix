{
description = "Generate a flake.nix for Python package using setuptools metadata";

inputs = {
  nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  flake-utils.url = "github:numtide/flake-utils";
};

outputs = { self, nixpkgs, flake-utils }:
  flake-utils.lib.eachDefaultSystem (system:
    with nixpkgs.legacyPackages.${system};
    let
      python = python310;

      defaultApp = python.pkgs.buildPythonApplication rec {
        pname = "py2nix";
        version = "0.1.0";
        src = ./.;
        propagatedBuildInputs = with python.pkgs; [ setuptools ];

        doCheck = false;

        meta = with lib; {
          homepage = "https://github.com/padhia/py2nix";
          description = "Generate a flake.nix for Python package using setuptools metadata";
          maintainers = with maintainers; [ padhia ];
        };
      };

    in {
      inherit defaultApp;
    }
  );
}
