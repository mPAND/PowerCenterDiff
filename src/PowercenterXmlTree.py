import logging

logging.basicConfig( format='%(asctime)s [%(levelname)s] : %(message)s'
                   , datefmt='%m/%d/%Y %I:%M:%S %p'
                   , level=logging.DEBUG
                   )

logging.disable(logging.INFO)


class _XMLSingleNode:
    """
    Internal call to hold Data Structure representing single XML tag

    XML tag contains Tag Name, Tag Atrribute and Chile Tags

    Example

    XML Snippet
    <INSTANCE DESCRIPTION ="" NAME ="SQ_Long_Running_Job_Source" REUSABLE ="NO" TRANSFORMATION_NAME ="SQ_Long_Running_Job_Source" TRANSFORMATION_TYPE ="Source Qualifier" TYPE ="TRANSFORMATION">
            <ASSOCIATED_SOURCE_INSTANCE NAME ="Long_Running_Job_Source"/>
     </INSTANCE>

    Tag Name   = INSTANCE
    Tag Attributes =  DESCRIPTION : "" NAME:"SQ_Long_Running_Job_Source" ..
    Child = Array containing list of _XMLSingleNode(<ASSOCIATED_SOURCE_INSTANCE NAME ="Long_Running_Job_Source"/>)

    """

    def __init__(self, tag, attrib, text=None):

        self.tag = tag
        self._children = []
        self.attrib = attrib

    def __repr__(self):
        tmp_display_string = "TAG NAME : %s " % self.tag

        if self.attrib:
            for attribute, value in self.attrib.items():
                tmp_display_string = tmp_display_string + "%s : %s " % (attribute, str(value))
        return tmp_display_string

    def set_attrib(self, attrib):
        self.attrib = attrib

    def add_child_node(self, child):
        self._children.append(child)

    def remove_child_node(self):
        self._children = []

    def print_current_node(self):

        tmp_attribute_string = ""

        if self.attrib:
            for i, k in self.attrib.items():
                tmp_attribute_string = tmp_attribute_string + ' %s: "%s"' % (i, k)

        if len(self._children) == 0:
            tmp_full_string = "<%s%s/>\n" % (self.tag, tmp_attribute_string)
        else:
            tmp_full_string = "<%s%s>\n" % (self.tag, tmp_attribute_string)

        return tmp_full_string

    def print_node_and_child(self):
        print(self)

        if len(self._children) > 0:
            print("CHILD NODES :-")

        for c in self._children:
            c.print_node_and_child()

        print("END OF TAG %s" % self.tag)


    " Implementing dunder methods lt and eq for sort capability "

    def __lt__(self, other):
        if self.tag < other.tag:
            return True

        elif self.tag == other.tag and str(self.attrib) < str(other.attrib):
            return True
        else:
            return False

    def __eq__(self, other):
        return self.tag == other.tag and str(self.attrib) == str(other.attrib)


    def sort_xml_tree(self):

        if len(self._children) == 0:
            return

        for i in self._children:
            i.sort_xml_tree()
            i._children = sorted(i._children)

    def export_to_file(self, file=None):

        if not file:
            import tempfile
            file = tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="UTF-8")

        file.write(self.print_current_node())
        for i in self._children:
            i.export_to_file(file)
        if len(self._children) > 0:
            file.write("</%s>\n" % self.tag)

        # file.close()

        return file.name


class PowercenterXmlTree:

    def __init__(self):

        self._filepath = None
        self.top = None
        self.pointer = None
        self.pointerparent = []

    def get_xml_tree(self, path):

        self._filepath = path
        self.top = _XMLSingleNode("root", None)

        self.pointer = self.top
        self.pointerparent.append(self.pointer)

        counter = 0

        with open(path) as fp:
            line = fp.readline()
            while line:
                line = line.lstrip(' \t\n\r')
                line = line.rstrip(' \t\n\r')

                counter += 1
                logging.debug("LINE NO : %05d" % counter)
                logging.debug("RAW TEXT : %s" % line)

                (first, *rest) = line.split(maxsplit=1)
                if rest:
                    rest = rest[0]
                else:
                    rest = None

                if first[:2] == "<?":
                    tag = first[2:]
                    logging.debug("DETECTED: Prolog Tag")
                    logging.debug("TAGNAME: %s" % tag)
                    tagtype = "PROLOG TAG"
                    rest = None

                    line = fp.readline()
                    continue

                if first[:2] == "<!":
                    tag = first[2:]
                    logging.debug("DETECTED: Comment Tag")
                    logging.debug("TAGNAME: %s" % tag)
                    tagtype = "COMMENT TAG"
                    rest = None

                    line = fp.readline()
                    continue

                if first[:2] == "</":
                    logging.debug("DETECTED: End Tag")
                    tag = first[2:-1]
                    logging.debug("TAGNAME: %s" % (tag))
                    tagtype = "ENDTAG"
                    rest = None

                if rest:
                    if rest[-2:] == "/>":
                        tagtype = "BEGINANDENDTAG"
                        tag = first[1:]
                        logging.debug("DETECTED : BEGIN AND END TAG")

                    elif rest[-1:] == ">" and rest[-2:] != "/>":
                        tagtype = "BEGINTAG"
                        tag = first[1:]

                        logging.debug("TAGNAME: %s " % (tag))
                        logging.debug("DETECTED : BEGIN TAG")

                if rest and tagtype == "BEGINANDENDTAG":
                    rest = rest[:-2]
                    import re
                    attrib = dict(re.findall(r'(\w+) ?="([^"]+)?"', rest))
                    logging.debug("List of Attributes : %s" % (attrib))

                if rest and tagtype == "BEGINTAG":
                    rest = rest[:-1]
                    import re
                    attrib = dict(re.findall(r'(\w+) ?="([^"]+)?"', rest))
                    logging.debug("List of Attributes : %s" % (attrib))

                if tagtype == "BEGINTAG":
                    self.temp = _XMLSingleNode(tag, attrib)

                    self.pointerparent[-1].add_child_node(self.temp)
                    self.pointerparent.append(self.temp)

                if tagtype == "BEGINANDENDTAG":
                    self.temp = _XMLSingleNode(tag, attrib)
                    self.pointerparent[-1].add_child_node(self.temp)

                if tagtype == "ENDTAG":
                    self.pointerparent.pop()

                line = fp.readline()
        return self.top

    def dump_to_temp_file(self):

        import tempfile
        tp = tempfile.NamedTemporaryFile()
        n = self.top

        tp.write(b'hello')
        tp.seek(0)
        print(tp.read())
        tp.close()
