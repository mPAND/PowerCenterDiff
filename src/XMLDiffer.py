import PowercenterXmlTree as pxt

import argparse
import os
import sys
import difflib
import json

def main(*args):
    parser = argparse.ArgumentParser(
        description="Python Script to compare two PowerCenter XML Files and display differences."
        , epilog="Generates HTML output if no optional arguments are passed."
        , formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-m', action='store_true', default=False
                        ,
                        help='Produce HTML page containing side-by-side comparison with change highlights\n(can be used along with -c and -l)')

    parser.add_argument('-u', action='store_true', default=False
                        , help='Produce a unified format. \n Show clusters of changes in an inline format')

    parser.add_argument('-n', action='store_true', default=False
                        , help='Produce a ndiff Format. \n Show every line and highlights interline changes')

    parser.add_argument('-c', action='store_true', default=False
                        , help="Produce a context format diff.\n Show clusters of changes in a before/after format")

    parser.add_argument('-l', type=int, default=3
                        ,
                        help='Set number of context lines. Applicable for Unified, HTML and Context diff. Defaults to 3')

    parser.add_argument('-s', type=argparse.FileType("w", encoding="UTF-8"),
                        help='Generates a output file named S with summary of differences')

    parser.add_argument('leftfile', help='Path to Left File', type=argparse.FileType('r', encoding="UTF-8"))
    parser.add_argument('rightfile', help='Path to Right File', type=argparse.FileType('r', encoding="UTF-8"))

    options = parser.parse_args(*args)

    pwcxml_operator = pxt.PowercenterXmlTree()

    var_left_file_as_xml = pwcxml_operator.get_xml_tree(options.leftfile.name)
    var_right_file_as_xml = pwcxml_operator.get_xml_tree(options.rightfile.name)

    var_left_file_as_xml.sort_xml_tree()
    var_right_file_as_xml.sort_xml_tree()

    # write sorted xml to temporary file for diff purpose
    tmp_left_file = var_left_file_as_xml.export_to_file()
    tmp_right_file = var_right_file_as_xml.export_to_file()


    with open(tmp_left_file) as file_pointer_to_leftfile:
        var_sorted_left_file = file_pointer_to_leftfile.readlines()

    with open(tmp_right_file) as file_pointer_to_rightfile:
        var_sorted_right_file = file_pointer_to_rightfile.readlines()

    if options.u:
        diff = difflib.unified_diff(var_sorted_left_file, var_sorted_right_file, options.leftfile.name,
                                    options.rightfile.name, n=options.l)
    elif options.n:
        diff = difflib.ndiff(var_sorted_left_file, var_sorted_right_file)
    elif options.m:
        diff = difflib.HtmlDiff(wrapcolumn=60).make_file(var_sorted_left_file, var_sorted_right_file,
                                                         fromdesc=options.leftfile.name, todesc=options.rightfile.name,
                                                         context=options.c, numlines=options.l)
    else:
        diff = difflib.context_diff(var_sorted_left_file, var_sorted_right_file, fromfile=options.leftfile.name,
                                    tofile=options.rightfile.name, n=options.l)

    if options.s: # Calculate summary of difference

        with open(tmp_left_file) as file_pointer_to_leftfile:
            var_sorted_right_file = file_pointer_to_leftfile.readlines()

        with open(tmp_right_file) as file_pointer_to_rightfile:
            var_sorted_right_file = file_pointer_to_rightfile.readlines()

        var_ndiff_changes = difflib.ndiff(var_sorted_right_file, var_sorted_right_file)
        deletions = 0
        additions = 0
        common = 0
        for line in var_ndiff_changes:
            if line[0] == "-":
                deletions += 1
            if line[0] == "+":
                additions += 1
            if line[0] == " ":
                common += 1

        num_lines_file1 = sum(1 for line in open(options.leftfile.name))
        num_lines_file2 = sum(1 for line in open(options.rightfile.name))

        summary = {}

        summary['leftfile_name'] = options.leftfile.name
        summary['rightfile_name'] = options.rightfile.name

        summary['line_count_leftfile'] = num_lines_file1
        summary['line_count_rightfile'] = num_lines_file2

        summary['common_lines'] = common
        summary['deletions_in_leftfile'] = deletions
        summary['additons_in_rightfile'] = additions

        with open(options.s.name, "w") as file:
            file.write(json.dumps(summary, indent=4))
            file.write("\n")

    if __name__ != "__main__":
        return diff
    else:
        sys.stdout.writelines(diff)

    os.unlink(tmp_left_file)
    os.unlink(tmp_right_file)

if __name__ == '__main__':
    main()