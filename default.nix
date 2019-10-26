{ pkgs ? import <nixpkgs> {}
}:

let
  inherit (pkgs) ;
  pythonPackages = pkgs.python3Packages;
in pythonPackages.buildPythonPackage rec {
  name = "py3buddy";
  src = ./.;
  propagatedBuildInputs =
    with pythonPackages;
    [ pydbus
      pyusb
      twitter
      pkgs.gobject-introspection
    ];
  postInstall = ''
    mkdir -p $out/etc/udev/rules.d
    cp ./etc/udev/rules.d/* $out/etc/udev/rules.d
  '';
}
