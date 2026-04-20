from utils.streams import parse_range


class TestParseRange:
    """Test suite for the parse_range function."""

    def test_parse_range_valid_start_and_end(self):
        """Test parsing a valid range with both start and end."""
        start, end = parse_range("bytes=0-499")
        assert start == 0
        assert end == 499

    def test_parse_range_valid_start_only(self):
        """Test parsing a valid range with only a start."""
        start, end = parse_range("bytes=500-")
        assert start == 500
        assert end is None

    def test_parse_range_valid_end_only(self):
        """Test parsing a valid range with only an end."""
        start, end = parse_range("bytes=-100")
        assert start is None
        assert end == 100

    def test_parse_range_empty(self):
        """Test parsing an empty range."""
        start, end = parse_range("bytes=")
        assert start is None
        assert end is None

    def test_parse_range_invalid_unit(self):
        """Test parsing a range with an invalid unit."""
        start, end = parse_range("invalid=0-499")
        assert start is None
        assert end is None

    def test_parse_range_malformed(self):
        """Test parsing a malformed range."""
        start, end = parse_range("bytes=invalid")
        assert start is None
        assert end is None

    def test_parse_range_none(self):
        """Test parsing a None header."""
        start, end = parse_range(None)
        assert start is None
        assert end is None

    def test_parse_range_empty_string(self):
        """Test parsing an empty string."""
        start, end = parse_range("")
        assert start is None
        assert end is None

    def test_parse_range_negative_values(self):
        """Test parsing a range with negative values."""
        start, end = parse_range("bytes=-500-1000")
        assert start is None
        assert end is None

    def test_parse_range_non_numeric(self):
        """Test parsing a range with non-numeric values."""
        start, end = parse_range("bytes=abc-def")
        assert start is None
        assert end is None

    def test_parse_range_missing_separator(self):
        """Test parsing a range with a missing separator."""
        start, end = parse_range("bytes=0")
        assert start is None
        assert end is None

    def test_parse_range_extra_equals(self):
        """Test parsing a range with extra equals signs."""
        start, end = parse_range("bytes=0-499-extra")
        assert start is None
        assert end is None

    def test_parse_range_whitespace(self):
        """Test parsing a range with whitespace."""
        start, end = parse_range("bytes= 0 - 499 ")
        assert start == 0
        assert end == 499

    def test_parse_range_large_numbers(self):
        """Test parsing a range with large numbers."""
        start, end = parse_range("bytes=1000000-9999999")
        assert start == 1000000
        assert end == 9999999

    def test_parse_range_zero_values(self):
        """Test parsing a range with zero values."""
        start, end = parse_range("bytes=0-0")
        assert start == 0
        assert end == 0
