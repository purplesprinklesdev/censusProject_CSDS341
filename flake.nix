{
  description = "Python dev environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python313
          python313Packages.pip
          python313Packages.virtualenv

          stdenv.cc.cc.lib
          libGL
          glib
        ];
        shellHook = ''
          export LD_LIBRARY_PATH=${pkgs.libz}/lib:${pkgs.glib.out}/lib:${pkgs.libGL}/lib:${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
        '';
      };
    };
}
