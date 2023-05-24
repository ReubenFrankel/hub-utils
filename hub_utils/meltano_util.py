import json
import pathlib
import subprocess
import tempfile

import typer


class MeltanoUtil:
    def __init__(self):
        pass

    @staticmethod
    def get_cwd():
        return pathlib.Path(__file__).parent.resolve()

    @staticmethod
    def add(plugin_name, namespace, executable, pip_url, plugin_type):
        python_version = subprocess.run(
            "which python".split(" "), stdout=subprocess.PIPE, universal_newlines=True
        ).stdout.replace("\n", "")
        subprocess.run(
            f"pipx uninstall {plugin_name}".split(" "),
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        subprocess.run(
            f"pipx install {pip_url} --python {python_version}".split(" "),
            stdout=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )

    @staticmethod
    def help_test(plugin_name, config=None):
        if config:
            with tempfile.NamedTemporaryFile(mode="w+") as tmp:
                json.dump(config, tmp)
                tmp.flush()
                subprocess.run(
                    f"{plugin_name} --help --config {tmp.name}".split(" "),
                    stdout=subprocess.PIPE,
                    universal_newlines=True,
                    check=True,
                )
        else:
            subprocess.run(
                f"{plugin_name} --help".split(" "),
                stdout=subprocess.PIPE,
                universal_newlines=True,
                check=True,
            )

    @staticmethod
    def sdk_about(plugin_name, config=None):
        if config:
            with tempfile.NamedTemporaryFile(mode="w+") as tmp:
                json.dump(config, tmp)
                tmp.flush()
                about_content = subprocess.run(
                    f"{plugin_name} --about --format=json --config {tmp.name}".split(
                        " "
                    ),
                    stdout=subprocess.PIPE,
                    universal_newlines=True,
                    check=True,
                )
                about_json_str = about_content.stdout.split("Setup Instructions:")[0]
                return json.loads(about_json_str)
        else:
            about_content = subprocess.run(
                f"{plugin_name} --about --format=json".split(" "),
                stdout=subprocess.PIPE,
                universal_newlines=True,
                check=True,
            )
            return json.loads(about_content.stdout)

    @staticmethod
    def _get_maintainer(
        variant,
    ):
        maintainer = "community"
        if variant in ["meltano", "meltanolabs"]:
            maintainer = "official"
        elif variant in ["matatika", "autoidm", "hotglue", "hotgluexyz"]:
            maintainer = "partner"
        return maintainer

    @staticmethod
    def get_quality(variant, is_sdk_based, usage_count, responsiveness):
        maintainer = MeltanoUtil._get_maintainer(variant)
        quality = "unknown"

        if maintainer == "official":
            quality = "gold"
        elif maintainer == "partner" and is_sdk_based:
            quality = "gold"
        elif (
            maintainer == "partner"
            and usage_count >= 1
            and responsiveness in ["medium", "high"]
        ):
            quality = "silver"
        elif maintainer == "partner":
            quality = "bronze"
        elif maintainer == "community" and is_sdk_based:
            quality = "silver"
        elif (
            maintainer == "community"
            and usage_count >= 1
            and responsiveness in ["medium", "high"]
        ):
            quality = "silver"
        elif maintainer == "community" and usage_count >= 1:
            quality = "bronze"
        return quality

    @staticmethod
    def _get_label(name):
        new_label = []
        for label_word in (
            name.replace("_", " ").replace("-", " ").replace(".", " ").split(" ")
        ):
            label_word = label_word.title()
            new_label.append(
                label_word.replace("Aws", "AWS")
                .replace("Url", "URL")
                .replace("Id", "ID")
                .replace("Db", "Database")
                .replace("Api", "API")
                .replace("Oauth", "OAuth")
            )
        return " ".join(new_label)

    @staticmethod
    def _parse_kind(kind, settings, format=None):
        setting = settings.get("name")
        setting = setting.lower()
        if kind == "string":
            if format in ("date-time", "date") or setting in ("start_date", "end_date"):
                return "date_iso8601", None
            if (
                any(
                    id_str.lower() in setting
                    for id_str in ["password", "id", "token", "key", "secret"]
                )
                or format == "airbyte_secret"
            ):
                return "password", None
            if settings.get("enum"):
                option_parsed = [
                    {"label": MeltanoUtil._get_label(val), "value": val}
                    for val in settings.get("enum")
                ]
                return "options", option_parsed
            return "string", None
        if kind == "number":
            return "integer", None
        # TODO: Meltano doesnt support array enums as of today
        # if kind == 'array':
        #     enum = settings.get('items', {}).get('enum')
        #     if enum:
        # option_parsed = [
        #     {'label': MeltanoUtil._get_label(val), 'value': val}
        #      for val in enum
        # ]
        #         return 'options', option_parsed
        #     return 'array', None
        else:
            return kind, None

    @staticmethod
    def _default_description(setting):
        setting = setting.lower()
        if setting == "start_date":
            return (
                "Determines how much historical data will be extracted. "
                "Please be aware that the larger the time period and amount "
                "of data, the longer the initial extraction can be expected "
                "to take."
            )
        if setting == "end_date":
            return "Date up to when historical data will be extracted."
        else:
            return None

    @staticmethod
    def _dedup_settings(reformatted_settings):
        reformatted_settings_2 = {}
        for setting in reformatted_settings:
            name = setting.get("name")
            if name in reformatted_settings_2:
                existing_setting = reformatted_settings_2.get(name)
                existing_setting["description"] = ", ".join(
                    [existing_setting["description"], setting.get("description")]
                )
            else:
                reformatted_settings_2[name] = setting
        return [value for key, value in reformatted_settings_2.items()]

    @staticmethod
    def _handle_description(description, name, enforce_desc):
        if not description:
            if enforce_desc:
                description = typer.prompt(
                    f"[{name}] `description`",
                    default=MeltanoUtil._default_description(name),
                )
            else:
                if name == "tag":
                    description = "Airbyte image tag"
                else:
                    description = ""
        return description

    @staticmethod
    def _get_kind_from_type(type, name, enforce_desc):
        if isinstance(type, list):
            kind = [s_type for s_type in type if s_type != "null"][0]
        else:
            kind = type

        if not kind:
            if enforce_desc:
                kind = typer.prompt(f"[{name}] `kind`", default="string")
            else:
                name = name
                print(f"No type found for: {name}. Defaulting to string")
                kind = "string"
        return kind

    @staticmethod
    def _parse_sdk_about_settings(sdk_about_dict, enforce_desc=False):
        settings_raw = sdk_about_dict.get("settings", {})
        reformatted_settings = []
        settings_group_validation = []
        base_required = settings_raw.get("required", [])
        for settings in MeltanoUtil._traverse_schema_properties(settings_raw):
            name = settings.get("name")
            description = MeltanoUtil._handle_description(
                settings.get("description"), name, enforce_desc
            )
            setting_details = {
                "name": name,
                "label": MeltanoUtil._get_label(name),
                "description": description,
            }
            kind = MeltanoUtil._get_kind_from_type(
                settings.get("type"), name, enforce_desc
            )

            kind, options = MeltanoUtil._parse_kind(kind, settings)
            setting_details["kind"] = kind
            if options:
                setting_details["options"] = options
            if settings.get("default"):
                if kind != "date_iso8601":
                    setting_details["value"] = settings.get("default")
            reformatted_settings.append(setting_details)
            if settings.get("required"):
                settings_group_validation.append(settings.get("name"))
        deduped_settings = MeltanoUtil._dedup_settings(reformatted_settings)
        return (
            deduped_settings,
            [list(set(settings_group_validation + base_required))],
            sdk_about_dict.get("capabilities"),
        )

    @staticmethod
    def _traverse_schema_properties(schema, field_sep="."):
        fields = []
        for key, value in schema.get("properties", {}).items():
            val_type = value.get("type", "string")
            if (val_type == "object" or "object" in val_type) and (
                value.get("properties") or value.get("oneOf")
            ):
                for subfield in MeltanoUtil._traverse_schema_properties(value):
                    sub_name = subfield.get("name")
                    full_name = f"{key}{field_sep}{sub_name}"
                    reqs = value.get("required", [])
                    field = {
                        "name": full_name,
                        "description": subfield.get("description"),
                        "default": subfield.get("default"),
                        "type": subfield.get("type"),
                        "title": subfield.get("title"),
                        "const": subfield.get("const"),
                        "items": subfield.get("items"),
                        "enum": subfield.get("enum"),
                    }
                    if "required" in subfield:
                        # accept parent if it was set already
                        field["required"] = subfield["required"]
                    else:
                        field["required"] = sub_name in reqs

                    fields.append(field)
            else:
                fields.append(
                    {
                        "name": key,
                        "description": value.get("description"),
                        "default": value.get("default"),
                        "type": value.get("type"),
                        "title": value.get("title"),
                        "const": value.get("const"),
                        "items": value.get("items"),
                        "enum": value.get("enum"),
                    }
                )
        for item in schema.get("oneOf", []):
            for i in MeltanoUtil._traverse_schema_properties(item):
                if i.get("const"):
                    i["description"] = i.get("const") or item.get("title")
                fields.append(i)
        return fields


if __name__ == "__main__":
    m = MeltanoUtil()

    # plugin_name = "tap-amazon-sp"
    # namespace = "tap_amazon_sp",
    # pip_url = "git+https://github.com/singer-io/tap-amazon-sp.git"
    # plugin_type = "extractors"
    # is_meltano_sdk = False

    plugin_name = "tap-cqc-org-uk"
    namespace = ("tap_cqc_org_uk",)
    pip_url = "git+https://github.com/birdiecare/tap-cqc-org-uk.git"
    plugin_type = "extractors"
    is_meltano_sdk = False

    MeltanoUtil.add(plugin_name, namespace, pip_url, plugin_type)
    MeltanoUtil.help_test(plugin_name)
    if is_meltano_sdk:
        MeltanoUtil.sdk_about(plugin_name)
