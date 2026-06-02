"""CallRowMapper: normalized call record -> sheet row (contract 24)."""
from mastertracker.call_row_mapper import CallRowMapper, AUTO_COLUMNS
from tests.sample_calls import make_call


def test_each_field_maps_to_its_column():
    # contract 24 - date, prospect, disposition, and additional fields land in the right column
    call = make_call(
        date="2026-05-20",
        prospect="Jane Doe",
        disposition="Interested",
        phone="+15551230001",
        duration_sec=142,
        id="call_99",
        recording_url="https://rec/99",
    )
    row = CallRowMapper().to_row(call)
    assert row.values["Date"] == "2026-05-20"
    assert row.values["Prospect"] == "Jane Doe"
    assert row.values["Disposition"] == "Interested"
    assert row.values["Phone"] == "+15551230001"
    assert row.values["Duration (sec)"] == 142
    assert row.values["Call ID"] == "call_99"
    assert row.values["Recording URL"] == "https://rec/99"


def test_row_exposes_dedup_key_of_date_and_lowercased_prospect():
    call = make_call(date="2026-05-20", prospect="Jane DOE")
    row = CallRowMapper().to_row(call)
    assert row.key == ("2026-05-20", "jane doe")


def test_manual_columns_are_present_but_blank_on_a_fresh_row():
    mapper = CallRowMapper(manual_columns=["Notes", "Next Step"])
    row = mapper.to_row(make_call())
    assert row.values["Notes"] == ""
    assert row.values["Next Step"] == ""


def test_as_list_orders_values_by_header():
    mapper = CallRowMapper(manual_columns=["Notes"])
    row = mapper.to_row(make_call(date="2026-05-20", prospect="Jane Doe"))
    header = AUTO_COLUMNS + ["Notes"]
    values = row.as_list(header)
    assert values[header.index("Date")] == "2026-05-20"
    assert values[header.index("Prospect")] == "Jane Doe"
    assert values[-1] == ""  # the manual column
