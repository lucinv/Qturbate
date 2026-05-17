{
  description = "Vids — Stream viewer application (Flask web + PyQt6 desktop)";

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

        # Dépendances Python communes au runtime et au dev
        baseDeps = with pythonPkgs; [
          # Web
          flask
          flask-sqlalchemy

          # Stream / scraping
          yt-dlp
          cloudscraper

          # Modèles & data
          pydantic
          pillow
          requests

          # PyQt6 desktop GUI
          pyqt6
        ];

        # Dépendances de dev (tests, outils)
        devDeps = with pythonPkgs; [
          pytest
          pytest-mock
        ];

      in
      {
        packages.default = pythonPkgs.buildPythonApplication {
          pname = "vids";
          version = "0.1.0";

          src = ./.;

          dontUseSetuptoolsCheck = true;

          propagatedBuildInputs = baseDeps;

          doCheck = false;

          # Meta information
          meta = with nixpkgs.lib; {
            description = "Stream viewer application";
            license = licenses.mit;
            maintainers = [ ];
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = baseDeps ++ devDeps ++ [ python ];

          shellHook = ''
            echo ""
            echo "╔══════════════════════════════════════╗"
            echo "║  Vids — environnement de développement ║"
            echo "╚══════════════════════════════════════╝"
            echo ""
            echo "  Flask web  : python app.py"
            echo "  PyQt6 GUI  : python main_tk.py"
            echo "  Tests      : python -m pytest"
            echo ""
          '';
        };
      }
    );
}
