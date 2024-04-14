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
      in
      {
        packages = rec {
          run = pkgs.writeShellScriptBin "run" ''
            SERVER_SCRIPT=${server}/bin/server \
            PATH=$PATH:${python}/bin:${pkgs.quarto}/bin:${pkgs.texliveFull}/bin ${./run.sh};
          '';
          server = pkgs.writers.writePython3Bin "server"
            {
              libraries = with
                pkgs.python3Packages; [ flask marimo matplotlib ];
              flakeIgnore = [ "E501" "E265" ];
            } ./server.py;
          convert = pkgs.writers.writePython3Bin "convert"
            {
              libraries = with
                pkgs.python3Packages; [ marimo ];
              flakeIgnore = [ "E265" ];
            } ./convert.py;
        };
      });
}
