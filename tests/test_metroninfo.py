import xml.etree.ElementTree as ET  # noqa: N817
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from lxml import etree

from darkseid.metadata import GTIN, Arc, Basic, Credit, Metadata, Price, Role, Series, Universe
from darkseid.metroninfo import MetronInfo

MI_XSD = "tests/test_files/MetronInfo.xsd"


@pytest.fixture()
def metron_info():
    return MetronInfo()


@pytest.mark.parametrize(
    ("xml", "expected_root_tag"),
    [
        # Happy path
        ("<MetronInfo></MetronInfo>", "MetronInfo"),
        # Edge case: empty XML
        ("", "MetronInfo"),
    ],
    ids=["happy_path", "empty_xml"],
)
def test_get_root(metron_info, xml, expected_root_tag):
    # Act
    result = metron_info._get_root(xml)  # noqa: SLF001

    # Assert
    assert result.tag == expected_root_tag


@pytest.mark.parametrize(
    ("val", "expected_result"),
    [
        # Happy path
        (Basic(name="Marvel"), True),
        # Edge case: None value
        (None, False),
        # Error case: invalid source
        (Basic(name="InvalidSource"), False),
    ],
    ids=["valid_source", "none_value", "invalid_source"],
)
def test_valid_info_source(metron_info, val, expected_result):
    # Act
    result = metron_info.valid_info_source(val)

    # Assert
    assert result == expected_result


@pytest.mark.parametrize(
    ("vals", "expected_result"),
    [
        # Happy path
        ([Basic(name="Fantasy")], True),
        # Edge case: empty list
        ([], False),
        # Error case: invalid genre
        ([Basic(name="InvalidGenre")], False),
    ],
    ids=["valid_genre", "empty_list", "invalid_genre"],
)
def test_list_contains_valid_genre(metron_info, vals, expected_result):
    # Act
    result = metron_info.list_contains_valid_genre(vals)

    # Assert
    assert result == expected_result


@pytest.mark.parametrize(
    ("val", "expected_result"),
    [
        # Happy path
        ("Teen", "Teen"),
        # Edge case: None value
        (None, None),
        # Error case: invalid rating
        ("InvalidRating", "Unknown"),
    ],
    ids=["valid_rating", "none_value", "invalid_rating"],
)
def test_valid_age_rating(metron_info, val, expected_result):
    # Act
    result = metron_info.valid_age_rating(val)

    # Assert
    assert result == expected_result


def test_convert_metadata_to_xml(metron_info):
    # Arrange
    metadata = Metadata(
        info_source=Basic("Metron", id_=54),
        alt_sources=[Basic("Comic Vine", id_=90)],
        publisher=Basic("Marvel", id_=1),
        series=Series(name="Spider-Man", volume=1, format="Single Issue", id_=50, language="en"),
        issue="50",
        story_arcs=[Arc("Final Crisis, Inc", id_=80, number=1)],
        cover_date=date(2020, 1, 1),
        store_date=date(2020, 1, 1),
        characters=[Basic("Aquaman", 1)],
        genres=[Basic("Humor"), Basic("Super-Hero", id_=10)],
        teams=[Basic("Justice League"), Basic("Infinity, Inc")],
        universes=[Universe(id_=25, name="ABC", designation="Earth 25")],
        prices=[Price(amount=Decimal("3.99"), country="US")],
        gtin=GTIN(isbn=1234567890123, upc=76194130593600111),
        credits=[Credit(person="Stan Lee", role=[Role(name="Writer", id_=5)], id_=10)],
        tags=[Basic("Good", id_=1)],
        locations=[Basic("Atlantis", id_=90)],
        reprints=[Basic("Action Comics #1", id_=1)],
    )

    # Act
    result = metron_info.convert_metadata_to_xml(metadata)

    # Assert
    assert isinstance(result, ET.ElementTree)
    assert result.getroot().tag == "MetronInfo"


def test_metadata_from_string(metron_info):
    # Arrange
    xml_string = """
    <MetronInfo>
         <ID>
            <Primary source="Metron">290431</Primary>
            <Alternative source="Comic Vine">12345</Alternative>
            <Alternative source="Grand Comics Database">543</Alternative>
        </ID>
        <Publisher>Marvel</Publisher>
        <Series id="65478" lang="en">
            <Name>Spider-Man</Name>
            <SortName>Spider-Man</SortName>
            <Volume>1</Volume>
            <Format>Omnibus</Format>
        </Series>
        <Prices>
            <Price country="US">3.99</Price>
        </Prices>
        <CoverDate>2011-10-01</CoverDate>
        <StoreDate>2011-08-31</StoreDate>
        <GTIN>
            <ISBN>1234567890123</ISBN>
            <UPC>76194130593600111</UPC>
        </GTIN>
        <Arcs>
            <Arc>
                <Name>Arc1</Name>
            </Arc>
        </Arcs>
        <Credits>
            <Credit>
                <Creator id="123">Stan Lee</Creator>
                <Roles>
                    <Role>Writer</Role>
                </Roles>
            </Credit>
        </Credits>
        <Pages>
            <Page Image="0" Type="FrontCover" ImageSize="1733120" ImageHeight="2951" ImageWidth="1920" />
            <Page Image="1" ImageSize="1320938" ImageHeight="2951" ImageWidth="1920" />
            <Page Image="2" ImageSize="1298224" ImageHeight="2951" ImageWidth="1920" />
            <Page Image="3" ImageSize="1587983" ImageHeight="2951" ImageWidth="1920" />
        </Pages>
    </MetronInfo>
    """
    # Act
    result = metron_info.metadata_from_string(xml_string)

    # Assert
    assert result.info_source.name == "Metron"
    assert result.info_source.id_ == 290431
    assert result.alt_sources[0].name == "Comic Vine"
    assert result.alt_sources[0].id_ == 12345
    assert result.publisher.name == "Marvel"
    assert result.series.name == "Spider-Man"
    assert result.series.format == "Omnibus"
    assert result.prices[0].amount == Decimal("3.99")
    assert result.gtin.isbn == 1234567890123
    assert result.gtin.upc == 76194130593600111
    assert result.story_arcs[0].name == "Arc1"
    assert result.credits[0].person == "Stan Lee"
    assert result.credits[0].id_ == 123
    assert result.credits[0].role[0].name == "Writer"


def validate(xml_path: str, xsd_path: str) -> bool:
    xmlschema_doc = etree.parse(xsd_path)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    xml_doc = etree.parse(xml_path)
    return xmlschema.validate(xml_doc)


def test_write_xml(fake_metadata, metron_info, tmp_path):
    # Arrange
    filename = tmp_path / "test.xml"

    # Act
    metron_info.write_xml(filename, fake_metadata)

    # Assert
    assert filename.exists()
    assert validate(str(filename), MI_XSD) is True


def test_read_xml(metron_info, tmp_path):
    # Arrange
    xml_string = "<MetronInfo><Publisher>Marvel</Publisher></MetronInfo>"
    filename = tmp_path / "test.xml"
    with Path.open(filename, "w") as f:
        f.write(xml_string)

    # Act
    result = metron_info.read_xml(filename)

    # Assert
    assert result.publisher.name == "Marvel"