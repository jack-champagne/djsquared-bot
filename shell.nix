{ pkgs ? import <nixpkgs> {} }:
let
  my-python-packages = ps: with ps; [
    pygame
    tabulate
    numpy
    (
    buildPythonPackage rec {
      pname = "compress_json";
      version = "1.0.10";
      src = fetchPypi {
        inherit pname version;
        sha256 = "sha256-LUlRdBe9vxAsGKr+DW1iGXFgW7wTaJIF4ELbzF6Hw48=";
      };
      doCheck = false;
    }
  )
    # other python packages
  ];
  my-python = pkgs.python310.withPackages my-python-packages;
in my-python.env
