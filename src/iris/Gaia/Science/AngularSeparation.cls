Class Gaia.Science.AngularSeparation Extends %RegisteredObject
{
ClassMethod Arcsec(ra1 As %Double, dec1 As %Double, ra2 As %Double, dec2 As %Double) As %Double [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    from gaia.science import separation
    return separation(ra1, dec1, ra2, dec2)
}
}
