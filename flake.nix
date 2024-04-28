{
  description = "Marimo-Quarto scripts";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        python = pkgs.python3.withPackages (ps: with ps; [ jupyter ]);
        marimoQuarto = { tex ? false, ... }@opts:
          pkgs.writeShellScriptBin ''marimo-quarto${if tex then "-tex" else ""}'' (''
            if [ "$1" = "convert" ]; then
              if [[ "$2" == *.py ]] || [[ "$2" == *.ipynb ]]; then
                exec ${convert}/bin/convert "$2"

              # if qmd convert back to marimo app
              elif [[ "$2" == *.qmd ]]; then
                  ${convert}/bin/convert ''
          + ''<(${pkgs.quarto}/bin/quarto convert ''
          + ''  <(${pkgs.toybox}/bin/sed "s/{marimo}/{python}/g" "$2") ''
          + ''-o /dev/stdout 2> /dev/null) --to-marimo
              else
                echo "Unknown file type: $2"
                echo "Wanted py, ipynb or qmd"
                exit 1
              fi
              exit 0
            fi
            PATH_EXTRA=${
            if tex then "${pkgs.texliveFull}/bin" else ""
          } ${run}/bin/run $@'');
        run = pkgs.writeShellScriptBin "run" ''
          SERVER_SCRIPT=${server}/bin/server \
          PATH=$PATH:${pkgs.toybox}/bin:${python}/bin:${pkgs.quarto}/bin:$PATH_EXTRA $BASH ${pkgs.copyPathToStore ./run.sh} $@
        '';
        server = pkgs.writers.writePython3Bin "server"
          {
            libraries = with
              pkgs.python3Packages; [ flask marimo matplotlib sympy numpy scipy scikit-learn ];
            flakeIgnore = [ "E501" "E265" ];
          } ./server.py;
        convert = pkgs.writers.writePython3Bin "convert"
          {
            libraries = with
              pkgs.python3Packages; [ marimo ];
            flakeIgnore = [ "E265" ];
          } ./convert.py;
      in
      {
        packages = rec {
          inherit run server convert;
          marimo-quarto = marimoQuarto {};
          marimo-quarto-tex = marimoQuarto {tex = true;};
          default = marimo-quarto;
        };
      });
}
