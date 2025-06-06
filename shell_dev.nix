{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs.python3Packages; [
    pkgs.python3
    flask
    tkinter
    yt-dlp
    cloudscraper
    httpx
    pydantic
    flask_sqlalchemy
  ];
}

