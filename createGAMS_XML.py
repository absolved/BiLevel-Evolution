#create GAMS xml file using template for submission to NEOS server.
def create_xml(model,gdxfile):
    return '''
    <document>
    <category>milp</category>
    <solver>CPLEX</solver>
    <inputMethod>GAMS</inputMethod>
    <model><![CDATA[''' + model + ''']]></model>
    <options><![CDATA[]]></options>
    <gdx><base64><![CDATA[''' + gdxfile + ''']]></base64></gdx>
    <wantgdx><![CDATA[yes]]></wantgdx>
    <wantlog><![CDATA[yes]]></wantlog>
    <comments><![CDATA[]]></comments>
    <email>ricenaros@gmail.com</email>
    </document>
    '''