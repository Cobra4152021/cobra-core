# SDK Compatibility Policy

- Domain pack manifests use semver `x.y.z`.
- Packs built against core 1.0.x must not require Worker breaking changes.
- Marketplace install validates pack id/version; signing may be required by flag.
- Research pack (`cobra.research`) is the reference SDK-based pack.
