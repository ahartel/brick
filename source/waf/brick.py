def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
            return ''.join(rc)

def getTextNodeValue(tree,nodeName):
    return getText(tree.getElementsByTagName(nodeName)[0].childNodes).encode('ascii')

