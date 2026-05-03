A ReaxFF force field file, CHONSSiCaCsKSrNaMgAlCuFeCl.ff, has been tailored for reactive molecular simulations under complex conditions, such as screening organic corrosion inhibitors for black rebars and modeling the hydration of various cement clinker minerals. This force field was derived from the existing FeOCHCl.ff and CHONSSiCaCsKSrNaMgAlCu.ff force fields provided in the official ReaxFF distribution (https://www.scm.com/doc/ReaxFF/Included\_Forcefields.html) .



It has been preliminarily tested on a set of simple systems, including pure metals, cement minerals, water, several organic molecules, and some of their mixtures. Its applicability limits, however, still require more extensive validation. Further validation on more challenging systems is welcome, and any feedback or correction would be greatly appreciated.



Recommended usage in LAMMPS:

1. Modern Version

pair_style reaxff control.params

pair_coeff * * CHONSSiCaCsKSrNaMgAlCuFeCl.ff X X X  # Replace X with your actual element names



fix qeq all qeq/reaxff 1 0.0 10.0 1e-6



2. Legacy Version

pair_style reax/c control.params

pair_coeff * * CHONSSiCaCsKSrNaMgAlCuFeCl.ff X X X  # Replace X with your actual elements



fix qeq all qeq/reax 1 0.0 10.0 1e-6 reax/c
