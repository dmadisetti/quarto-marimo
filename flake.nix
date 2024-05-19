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
        python = pkgs.python3.withPackages (ps: with ps; [ ]);
        marimoQuarto = { tex ? false, ... }@opts:
          pkgs.writeShellScriptBin ''marimo-quarto${if tex then "-tex" else ""}'' (''
            PATH_EXTRA=${
            if tex then "${pkgs.texliveFull}/bin" else ""
          } ${run}/bin/run $@'');
        run = pkgs.writeShellScriptBin "run" ''
          PATH=$PATH:${pkgs.toybox}/bin:${python}/bin:${pkgs.quarto}/bin:$PATH_EXTRA $BASH ${pkgs.copyPathToStore ./run.sh} $@
        '';
      in
      {
        packages = rec {
          inherit run;
          marimo-quarto = marimoQuarto {};
          marimo-quarto-tex = marimoQuarto {tex = true;};
          default = marimo-quarto;
        };
      });
}
