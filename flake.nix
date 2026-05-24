{
  description = "qturbate — Chaturbate stream viewer (PyQt6)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
        pythonPkgs = python.pkgs;

        runtimeDeps = with pythonPkgs; [
          yt-dlp
          cloudscraper
          pydantic
          pillow
          requests
          pyqt6
        ];

        devDeps = with pythonPkgs; [
          flask
          flask-sqlalchemy
          pytest
          pytest-mock
        ];

      in
      {
        packages.default = pythonPkgs.buildPythonApplication {
          pname = "qturbate";
          version = "0.1.0";
          format = "pyproject";

          src = builtins.path { path = ./.; name = "qturbate-source"; };

          nativeBuildInputs = with pkgs.qt6; [
            qtbase
            wrapQtAppsHook
          ] ++ (with pythonPkgs; [
            setuptools
          ]);

          propagatedBuildInputs = runtimeDeps;

          postFixup = ''
            wrapQtApp $out/bin/qturbate \
              --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.yt-dlp pkgs.mpv ]} \
              --unset QT_STYLE_OVERRIDE
          '';

          doCheck = false;

          meta = with nixpkgs.lib; {
            description = "Chaturbate stream viewer";
            license = licenses.mit;
            maintainers = [ ];
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = runtimeDeps ++ devDeps ++ [ python ];

          shellHook = ''
            echo ""
            echo "╔══════════════════════════════════════╗"
            echo "║  qturbate — environnement de développement ║"
            echo "╚══════════════════════════════════════╝"
            echo ""
            echo "  PyQt6 GUI  : python main_tk.py"
            echo "  Tests      : python -m pytest"
            echo ""
          '';
        };
      }
    );
}
