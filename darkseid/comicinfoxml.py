"""A class to encapsulate ComicRack's ComicInfo.xml data"""

# Copyright 2012-2014 Anthony Beville
# Copyright 2020 Brian Pepple


import xml.etree.ElementTree as ET
from typing import List, Optional, Union

from .genericmetadata import GenericMetadata
from .issuestring import IssueString
from .utils import list_to_string, xlate


class ComicInfoXml:

    writer_synonyms: List[str] = [
        "writer",
        "plotter",
        "scripter",
        "script",
        "story",
        "plot",
    ]
    penciller_synonyms: List[str] = [
        "artist",
        "breakdowns",
        "illustrator",
        "layouts",
        "penciller",
        "penciler",
    ]
    inker_synonyms: List[str] = [
        "artist",
        "embellisher",
        "finishes",
        "illustrator",
        "ink assists",
        "inker",
    ]
    colorist_synonyms: List[str] = [
        "colorist",
        "colourist",
        "colorer",
        "colourer",
        "color assists",
        "color flats",
    ]
    letterer_synonyms: List[str] = ["letterer"]
    cover_synonyms: List[str] = ["cover", "covers", "coverartist", "cover artist"]
    editor_synonyms: List[str] = [
        "assistant editor",
        "associate editor",
        "consulting editor",
        "editor",
        "editor in chief",
        "executive editor",
        "group editor",
        "senior editor",
        "supervising editor",
    ]

    def metadata_from_string(self, string: str) -> GenericMetadata:

        tree = ET.ElementTree(ET.fromstring(string))
        return self.convert_xml_to_metadata(tree)

    def string_from_metadata(self, metadata: GenericMetadata) -> str:

        header = '<?xml version="1.0"?>\n'

        tree = self.convert_metadata_to_xml(metadata)
        tree_str = ET.tostring(tree.getroot()).decode()
        return header + tree_str

    def indent(self, elem: ET.Element, level: int = 0) -> None:
        # for making the XML output readable
        i = "\n" + level * "  "
        if elem:
            if not elem.text or not elem.text.strip():
                elem.text = f"{i}  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        elif level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

    def convert_metadata_to_xml(self, metadata: GenericMetadata) -> ET.ElementTree:

        # build a tree structure
        root = ET.Element("ComicInfo")
        root.attrib["xmlns:xsi"] = "https://www.w3.org/2001/XMLSchema-instance"
        root.attrib["xmlns:xsd"] = "https://www.w3.org/2001/XMLSchema"
        # helper func

        def assign(cix_entry: str, md_entry: Optional[Union[str, int]]) -> None:
            if md_entry is not None and md_entry:
                et_entry = root.find(cix_entry)
                if et_entry is not None:
                    et_entry.text = str(md_entry)
                else:
                    ET.SubElement(root, cix_entry).text = str(md_entry)
            else:
                et_entry = root.find(cix_entry)
                if et_entry is not None:
                    et_entry.clear()

        assign("Title", metadata.title)
        assign("Series", metadata.series)
        assign("Number", metadata.issue)
        assign("Count", metadata.issue_count)
        assign("Volume", metadata.volume)
        assign("AlternateSeries", metadata.alternate_series)
        assign("AlternateNumber", metadata.alternate_number)
        assign("StoryArc", metadata.story_arc)
        assign("SeriesGroup", metadata.series_group)
        assign("AlternateCount", metadata.alternate_count)
        assign("Summary", metadata.comments)
        assign("Notes", metadata.notes)
        assign("Year", metadata.year)
        assign("Month", metadata.month)
        assign("Day", metadata.day)

        # need to specially process the credits, since they are structured
        # differently than CIX
        credit_writer_list: List[str] = []
        credit_penciller_list: List[str] = []
        credit_inker_list: List[str] = []
        credit_colorist_list: List[str] = []
        credit_letterer_list: List[str] = []
        credit_cover_list: List[str] = []
        credit_editor_list: List[str] = []

        # first, loop thru credits, and build a list for each role that CIX
        # supports
        for credit in metadata.credits:

            if credit["role"].lower() in set(self.writer_synonyms):
                credit_writer_list.append(credit["person"].replace(",", ""))

            if credit["role"].lower() in set(self.penciller_synonyms):
                credit_penciller_list.append(credit["person"].replace(",", ""))

            if credit["role"].lower() in set(self.inker_synonyms):
                credit_inker_list.append(credit["person"].replace(",", ""))

            if credit["role"].lower() in set(self.colorist_synonyms):
                credit_colorist_list.append(credit["person"].replace(",", ""))

            if credit["role"].lower() in set(self.letterer_synonyms):
                credit_letterer_list.append(credit["person"].replace(",", ""))

            if credit["role"].lower() in set(self.cover_synonyms):
                credit_cover_list.append(credit["person"].replace(",", ""))

            if credit["role"].lower() in set(self.editor_synonyms):
                credit_editor_list.append(credit["person"].replace(",", ""))

        # second, convert each list to string, and add to XML struct
        assign("Writer", list_to_string(credit_writer_list))
        assign("Penciller", list_to_string(credit_penciller_list))
        assign("Inker", list_to_string(credit_inker_list))
        assign("Colorist", list_to_string(credit_colorist_list))
        assign("Letterer", list_to_string(credit_letterer_list))
        assign("CoverArtist", list_to_string(credit_cover_list))
        assign("Editor", list_to_string(credit_editor_list))

        assign("Publisher", metadata.publisher)
        assign("Imprint", metadata.imprint)
        assign("Genre", metadata.genre)
        assign("Web", metadata.web_link)
        assign("PageCount", metadata.page_count)
        assign("LanguageISO", metadata.language)
        assign("Format", metadata.format)
        assign("AgeRating", metadata.maturity_rating)
        assign("BlackAndWhite", "Yes" if metadata.black_and_white else None)
        assign("Manga", metadata.manga)
        assign("Characters", metadata.characters)
        assign("Teams", metadata.teams)
        assign("Locations", metadata.locations)
        assign("ScanInformation", metadata.scan_info)

        #  loop and add the page entries under pages node
        if len(metadata.pages) > 0:
            pages_node = ET.SubElement(root, "Pages")
            for page_dict in metadata.pages:
                page_node = ET.SubElement(pages_node, "Page")
                page_node.attrib = page_dict

        # self pretty-print
        self.indent(root)

        # wrap it in an ElementTree instance, and save as XML
        tree = ET.ElementTree(root)
        return tree

    @classmethod
    def convert_xml_to_metadata(cls, tree: ET.ElementTree) -> GenericMetadata:

        root = tree.getroot()

        if root.tag != "ComicInfo":
            raise ValueError("Metadata is not ComicInfo format")

        def get(name):
            tag = root.find(name)
            if tag is None:
                return None
            return tag.text

        metadata = GenericMetadata()
        metadata.series = xlate(get("Series"))
        metadata.title = xlate(get("Title"))
        metadata.issue = IssueString(xlate(get("Number"))).as_string()
        metadata.issue_count = xlate(get("Count"), True)
        metadata.volume = xlate(get("Volume"), True)
        metadata.alternate_series = xlate(get("AlternateSeries"))
        metadata.alternate_number = IssueString(xlate(get("AlternateNumber"))).as_string()
        metadata.alternate_count = xlate(get("AlternateCount"), True)
        metadata.comments = xlate(get("Summary"))
        metadata.notes = xlate(get("Notes"))
        metadata.year = xlate(get("Year"), True)
        metadata.month = xlate(get("Month"), True)
        metadata.day = xlate(get("Day"), True)
        metadata.publisher = xlate(get("Publisher"))
        metadata.imprint = xlate(get("Imprint"))
        metadata.genre = xlate(get("Genre"))
        metadata.web_link = xlate(get("Web"))
        metadata.language = xlate(get("LanguageISO"))
        metadata.format = xlate(get("Format"))
        metadata.manga = xlate(get("Manga"))
        metadata.characters = xlate(get("Characters"))
        metadata.teams = xlate(get("Teams"))
        metadata.locations = xlate(get("Locations"))
        metadata.page_count = xlate(get("PageCount"), True)
        metadata.scan_info = xlate(get("ScanInformation"))
        metadata.story_arc = xlate(get("StoryArc"))
        metadata.series_group = xlate(get("SeriesGroup"))
        metadata.maturity_rating = xlate(get("AgeRating"))

        tmp = xlate(get("BlackAndWhite"))
        metadata.black_and_white = False
        if tmp is not None and tmp.lower() in ["yes", "true", "1"]:
            metadata.black_and_white = True
        # Now extract the credit info
        for credit_node in root:
            if (
                credit_node.tag == "Writer"
                or credit_node.tag == "Penciller"
                or credit_node.tag == "Inker"
                or credit_node.tag == "Colorist"
                or credit_node.tag == "Letterer"
                or credit_node.tag == "Editor"
            ) and credit_node.text is not None:
                for name in credit_node.text.split(","):
                    metadata.add_credit(name.strip(), credit_node.tag)

            if credit_node.tag == "CoverArtist" and credit_node.text is not None:
                for name in credit_node.text.split(","):
                    metadata.add_credit(name.strip(), "Cover")

        # parse page data now
        pages_node = root.find("Pages")
        if pages_node is not None:
            for page in pages_node:
                metadata.pages.append(page.attrib)
                # print page.attrib

        metadata.is_empty = False

        return metadata

    def write_to_external_file(self, filename: str, metadata: GenericMetadata) -> None:

        tree = self.convert_metadata_to_xml(metadata)
        # ET.dump(tree)
        tree.write(filename, encoding="utf-8")

    def read_from_external_file(self, filename: str) -> GenericMetadata:

        tree = ET.parse(filename)
        return self.convert_xml_to_metadata(tree)
