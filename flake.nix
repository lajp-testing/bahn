{
  description = "Spread (Bahn challenge at Junction 2026): dispatcher dev environment";

  # The same nixpkgs revision as the system flake in /etc/nixos, so the shell reuses the store.
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/4fe25e12eb9f4c744966dd3de5a05246cf098601";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAll = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAll (pkgs: {
        # The dispatcher itself uses only the standard library, so it runs on any Python 3.9+.
        # numpy and pandas are for the analysis of reveals; pytest and ruff for the code.
        default = pkgs.mkShell {
          packages = [
            (pkgs.python3.withPackages (ps: [ ps.numpy ps.pandas ps.pytest ]))
            pkgs.ruff
            pkgs.jq
            pkgs.curl
          ];
          shellHook = ''
            # The team key lives in .env, which git ignores.
            if [ -f .env ]; then set -a; . ./.env; set +a; fi
            export PYTHONPATH="$PWD''${PYTHONPATH:+:$PYTHONPATH}"
          '';
        };
      });
    };
}
