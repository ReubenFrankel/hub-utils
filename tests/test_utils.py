from unittest.mock import patch

import pytest

from hub_utils.utilities import Utilities


def test_get_plugin_type_from_suffix():
    utils = Utilities()
    plugin_type = utils.get_plugin_type_from_suffix("extractors/tap-csv/meltanolabs")
    assert plugin_type == "extractors"


def test_get_plugin_variant_from_suffix():
    utils = Utilities()
    variant = utils.get_plugin_variant_from_suffix("extractors/tap-csv/meltanolabs")
    assert variant == "meltanolabs"


@patch.object(Utilities, "_write_updated_def")
def test_merge_and_update(patch):
    utils = Utilities()
    variant = utils.merge_and_update(
        {
            "keywords": ["keys"],
            "maintenance_status": "active",
            "settings": [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
        },
        "tap-csv",
        "extractors",
        "meltanolabs",
        [
            {
                "name": "add_metadata_columns",
                "description": "The description",
                "label": "Add Metadata Columns",
                "kind": "boolean",
            }
        ],
        ["catalog", "discover"],
        [
            [
                "files",
            ],
            [
                "csv_files_definition",
            ],
        ],
    )
    patch.assert_called_with(
        "tap-csv",
        "meltanolabs",
        "extractors",
        {
            "capabilities": ["catalog", "discover"],
            "keywords": ["keys"],
            "maintenance_status": "active",
            "settings": [
                {
                    "description": "The description",
                    "kind": "boolean",
                    "label": "Add Metadata Columns",
                    "name": "add_metadata_columns",
                }
            ],
            "settings_group_validation": [["files"], ["csv_files_definition"]],
        },
    )


@pytest.mark.parametrize(
    "existing,new,expected",
    [
        # Nothing changes
        [
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
        ],
        # Setting removed
        [
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
            [],
            [],
        ],
        # Setting added
        [
            [],
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
        ],
        # Description changed
        [
            [
                {
                    "name": "add_metadata_columns",
                    "description": "Original",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
            [
                {
                    "name": "add_metadata_columns",
                    "description": "New",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
            [
                {
                    "name": "add_metadata_columns",
                    "description": "New",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
        ],
        # Preserve manually added value
        [
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                    "value": "$MELTANO_EXTRACT__LOAD_SCHEMA",
                }
            ],
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                    "value": "$MELTANO_EXTRACT__LOAD_SCHEMA",
                }
            ],
        ],
        # Preserve attributes
        [
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                    "value": "$MELTANO_EXTRACT__LOAD_SCHEMA",
                    "placeholder": "foo",
                    "documentation": "bar"
                }
            ],
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                }
            ],
            [
                {
                    "name": "add_metadata_columns",
                    "description": "The description",
                    "label": "Add Metadata Columns",
                    "kind": "boolean",
                    "value": "$MELTANO_EXTRACT__LOAD_SCHEMA",
                    "placeholder": "foo",
                    "documentation": "bar"
                }
            ],
        ],
    ],
)
def test_merge_settings(existing, new, expected):
    utils = Utilities()
    merged_settings = utils._merge_settings(existing, new)
    assert merged_settings == expected
