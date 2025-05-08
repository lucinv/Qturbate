{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs.python3Packages; [
    pkgs.python3
    flask
    tkinter
  ];
}

