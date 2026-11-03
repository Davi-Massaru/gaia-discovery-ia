Class Gaia.Science.ReportEmbedding Extends %RegisteredObject
{
ClassMethod Embed(text As %String) As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    import json
    from gaia.embedding import embed
    return json.dumps(embed(text))
}
ClassMethod Search(text As %String) As %String [ Language = python ]
{
    import sys, iris
    home = iris.gref("^GaiaConfig").get(["home"]) or "/opt/gaia"
    if home+"/backend" not in sys.path:
        sys.path.insert(0, home+"/backend")
    import json
    from gaia.embedding import search_previous
    return json.dumps(search_previous(text))
}
}
