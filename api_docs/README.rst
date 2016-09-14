The api-docs are seriealised from source
using sphinx for code gen and ".rst" for source formatting.

@pedromorgan admits that I hate both, but we have to live with ;-)

Snags...
- sphinx does not automatically load a whole path.. so the `fab
- Why not use readthedocs- because we cant load pyqt etc

So this set is generated locally,
and then uploaded.. idea is to NOT have ghpages,
but instead a decicated app, fast release, docs autgen etc..
developers and users heaven..

To build the docs.. we use "fabric" and "sphinx"

then on shell

## First we need to make an .rst file for each .py file in source.
> fab docs_gen_index

## then we generate docs at build/api-docs
> fab docs_build


