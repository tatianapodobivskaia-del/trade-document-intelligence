"""
Multi-Sanctions List Loader
Downloads and parses OFAC SDN, EU Consolidated, UN Security Council,
and UK OFSI sanctions lists into a unified format.

Author: Tatiana Podobivskaia
Project: TradeScreenAI - AI-Powered Trade Document Intelligence

Sources:
    - OFAC SDN: https://www.treasury.gov/ofac/downloads/sdn.csv
    - EU Consolidated: https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content
    - UN Security Council: https://scsanctions.un.org/resources/xml/en/consolidated.xml
    - UK OFSI: https://ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.csv
"""

import requests
import csv
import io
import xml.etree.ElementTree as ET
from datetime import datetime


# =============================================================================
# UNIFIED ENTITY FORMAT
# =============================================================================
# Every parser returns a list of dicts with these keys:
#   {
#       "name": str,           # Entity name (primary)
#       "aliases": list[str],  # Alternative names
#       "entity_type": str,    # "individual" | "entity" | "vessel" | "aircraft" | "unknown"
#       "program": str,        # Sanctions program (e.g., "UKRAINE-EO13661")
#       "list_source": str,    # "OFAC_SDN" | "EU" | "UN" | "UK_OFSI"
#       "country": str,        # Associated country (if available)
#       "remarks": str,        # Additional info
#   }


def _make_entity(name, aliases=None, entity_type="unknown", program="",
                 list_source="", country="", remarks=""):
    """Create a standardized entity dict."""
    return {
        "name": name.strip(),
        "aliases": aliases or [],
        "entity_type": entity_type,
        "program": program,
        "list_source": list_source,
        "country": country,
        "remarks": remarks,
    }


# =============================================================================
# 1. OFAC SDN LIST
# =============================================================================

OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
OFAC_ALT_URL = "https://www.treasury.gov/ofac/downloads/alt.csv"


def load_ofac_sdn():
    """Download and parse the OFAC SDN list."""
    print("[*] Loading OFAC SDN list...")
    try:
        resp = requests.get(OFAC_SDN_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] Error downloading OFAC SDN: {e}")
        return []

    # Load aliases
    aliases_map = {}
    try:
        alt_resp = requests.get(OFAC_ALT_URL, timeout=30)
        alt_resp.raise_for_status()
        reader = csv.reader(io.StringIO(alt_resp.text))
        for row in reader:
            if len(row) >= 4:
                ent_num = row[0].strip()
                alt_name = row[3].strip()
                if alt_name and alt_name != "-0-":
                    aliases_map.setdefault(ent_num, []).append(alt_name)
    except Exception:
        print("[!] Could not load OFAC aliases file, continuing without aliases")

    entities = []
    reader = csv.reader(io.StringIO(resp.text))
    for row in reader:
        if len(row) >= 2:
            ent_num = row[0].strip()
            name = row[1].strip()
            if name and name != "-0-":
                ent_type_raw = row[2].strip() if len(row) >= 3 else ""
                ent_type = {
                    "individual": "individual",
                    "": "unknown",
                    "-0-": "entity",
                }.get(ent_type_raw.lower(), "entity")

                entities.append(_make_entity(
                    name=name,
                    aliases=aliases_map.get(ent_num, []),
                    entity_type=ent_type,
                    program=row[3].strip() if len(row) >= 4 else "",
                    list_source="OFAC_SDN",
                    country=row[4].strip() if len(row) >= 5 else "",
                    remarks=row[5].strip() if len(row) >= 6 else "",
                ))

    print(f"[+] OFAC SDN: {len(entities)} entities loaded")
    return entities


# =============================================================================
# 2. EU CONSOLIDATED SANCTIONS LIST
# =============================================================================

EU_SANCTIONS_URL = (
    "https://webgate.ec.europa.eu/fsd/fsf/public/files/"
    "xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw"
)


def load_eu_sanctions():
    """Download and parse the EU Consolidated Sanctions List (XML)."""
    print("[*] Loading EU Consolidated Sanctions list...")
    try:
        resp = requests.get(EU_SANCTIONS_URL, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] Error downloading EU sanctions: {e}")
        return []

    entities = []
    try:
        root = ET.fromstring(resp.content)
        # EU XML namespace
        ns = {"eu": "http://eu.europa.ec/fpi/fsd/export"}

        for entity_el in root.findall(".//eu:sanctionEntity", ns):
            # Get regulation info
            reg_el = entity_el.find(".//eu:regulation", ns)
            program = ""
            if reg_el is not None:
                prog_el = reg_el.find("eu:programme", ns)
                if prog_el is not None and prog_el.text:
                    program = prog_el.text.strip()

            # Get subject type
            subject_type_el = entity_el.find(".//eu:subjectType", ns)
            ent_type = "unknown"
            if subject_type_el is not None:
                code = (subject_type_el.get("code") or "").lower()
                if "person" in code:
                    ent_type = "individual"
                elif "enterprise" in code or "entity" in code:
                    ent_type = "entity"

            # Get names
            names = []
            for name_alias in entity_el.findall(".//eu:nameAlias", ns):
                whole_name = name_alias.get("wholeName", "").strip()
                if whole_name:
                    names.append(whole_name)

            if not names:
                continue

            primary_name = names[0]
            aliases = names[1:] if len(names) > 1 else []

            # Get citizenship/country
            country = ""
            citizen_el = entity_el.find(".//eu:citizenship", ns)
            if citizen_el is not None:
                country = citizen_el.get("countryDescription", "")
            if not country:
                addr_el = entity_el.find(".//eu:address", ns)
                if addr_el is not None:
                    country = addr_el.get("countryDescription", "")

            entities.append(_make_entity(
                name=primary_name,
                aliases=aliases,
                entity_type=ent_type,
                program=program,
                list_source="EU",
                country=country,
            ))

    except ET.ParseError as e:
        print(f"[!] Error parsing EU XML: {e}")
        return []

    print(f"[+] EU Sanctions: {len(entities)} entities loaded")
    return entities


# =============================================================================
# 3. UN SECURITY COUNCIL SANCTIONS
# =============================================================================

UN_SANCTIONS_URL = (
    "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
)


def load_un_sanctions():
    """Download and parse the UN Security Council Consolidated List (XML)."""
    print("[*] Loading UN Security Council Sanctions list...")
    try:
        resp = requests.get(UN_SANCTIONS_URL, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] Error downloading UN sanctions: {e}")
        return []

    entities = []
    try:
        root = ET.fromstring(resp.content)

        # Process individuals
        for indiv in root.findall(".//INDIVIDUAL"):
            first = (indiv.findtext("FIRST_NAME") or "").strip()
            second = (indiv.findtext("SECOND_NAME") or "").strip()
            third = (indiv.findtext("THIRD_NAME") or "").strip()

            name_parts = [p for p in [first, second, third] if p]
            if not name_parts:
                continue

            primary_name = " ".join(name_parts)

            # Aliases
            aliases = []
            for alias_el in indiv.findall(".//INDIVIDUAL_ALIAS"):
                alias_name = (alias_el.findtext("ALIAS_NAME") or "").strip()
                if alias_name and alias_name.upper() not in ("NA", "N/A", ""):
                    aliases.append(alias_name)

            # Country (nationality)
            country = ""
            nat_el = indiv.find(".//NATIONALITY/VALUE")
            if nat_el is not None and nat_el.text:
                country = nat_el.text.strip()

            # Program / list reference
            ref_num = (indiv.findtext("REFERENCE_NUMBER") or "").strip()
            list_type = (indiv.findtext("UN_LIST_TYPE") or "").strip()
            program = f"{list_type} {ref_num}".strip()

            entities.append(_make_entity(
                name=primary_name,
                aliases=aliases,
                entity_type="individual",
                program=program,
                list_source="UN",
                country=country,
            ))

        # Process entities
        for ent in root.findall(".//ENTITY"):
            name = (ent.findtext("FIRST_NAME") or "").strip()
            if not name:
                continue

            aliases = []
            for alias_el in ent.findall(".//ENTITY_ALIAS"):
                alias_name = (alias_el.findtext("ALIAS_NAME") or "").strip()
                if alias_name and alias_name.upper() not in ("NA", "N/A", ""):
                    aliases.append(alias_name)

            country = ""
            addr_el = ent.find(".//ENTITY_ADDRESS")
            if addr_el is not None:
                country = (addr_el.findtext("COUNTRY") or "").strip()

            ref_num = (ent.findtext("REFERENCE_NUMBER") or "").strip()
            list_type = (ent.findtext("UN_LIST_TYPE") or "").strip()
            program = f"{list_type} {ref_num}".strip()

            entities.append(_make_entity(
                name=name,
                aliases=aliases,
                entity_type="entity",
                program=program,
                list_source="UN",
                country=country,
            ))

    except ET.ParseError as e:
        print(f"[!] Error parsing UN XML: {e}")
        return []

    print(f"[+] UN Sanctions: {len(entities)} entities loaded")
    return entities


# =============================================================================
# 4. UK OFSI CONSOLIDATED LIST
# =============================================================================

UK_OFSI_URL = (
    "https://ofsistorage.blob.core.windows.net/publishlive/"
    "2022format/ConList.csv"
)


def load_uk_ofsi():
    """Download and parse the UK OFSI Consolidated List (CSV)."""
    print("[*] Loading UK OFSI Consolidated list...")
    try:
        resp = requests.get(UK_OFSI_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] Error downloading UK OFSI: {e}")
        return []

    entities = []
    try:
        # Full text + StringIO so quoted fields with newlines parse correctly.
        text = resp.content.decode("utf-8-sig")
        first_nl = text.find("\n")
        if first_nl != -1:
            head = text[:first_nl].strip()
            if head and not head.startswith("Name"):
                text = text[first_nl + 1 :]
        reader = csv.DictReader(io.StringIO(text))

        def cell(row, key):
            # DictReader uses None for short rows; .get(k, "") still returns None.
            v = row.get(key)
            return (v if v is not None else "").strip()

        for row in reader:
            # Build name from available fields
            name_parts = []
            for field in ["Name 6", "Name 1", "Name 2", "Name 3",
                          "Name 4", "Name 5"]:
                val = cell(row, field)
                if val:
                    name_parts.append(val)

            if not name_parts:
                continue

            primary_name = " ".join(name_parts)

            # Entity type
            group_type = cell(row, "Group Type").lower()
            if "individual" in group_type:
                ent_type = "individual"
            elif "entity" in group_type or "ship" in group_type:
                ent_type = "entity"
            else:
                ent_type = "unknown"

            # Aliases from alias fields
            aliases = []
            for i in range(1, 7):
                # OFSI has various alias columns; try common patterns
                for alias_key in [f"Alias {i}", f"Name (Alias {i})"]:
                    alias_val = cell(row, alias_key)
                    if alias_val:
                        aliases.append(alias_val)

            # Country
            country = cell(row, "Country")
            if not country:
                country = cell(row, "Country of Birth")

            # Regime / program
            program = cell(row, "Regime")
            if not program:
                program = cell(row, "Listed On")

            entities.append(_make_entity(
                name=primary_name,
                aliases=aliases,
                entity_type=ent_type,
                program=program,
                list_source="UK_OFSI",
                country=country,
            ))

    except Exception as e:
        print(f"[!] Error parsing UK OFSI CSV: {e}")
        return []

    print(f"[+] UK OFSI: {len(entities)} entities loaded")
    return entities


# =============================================================================
# 5. UNIFIED LOADER
# =============================================================================

def load_all_sanctions_lists(lists=None):
    """
    Load all (or selected) sanctions lists and return unified entity list.

    Args:
        lists: List of list names to load. None = all.
               Options: "OFAC_SDN", "EU", "UN", "UK_OFSI"

    Returns:
        dict with:
            "entities": list of unified entity dicts
            "metadata": dict with list counts, timestamps, etc.
    """
    loaders = {
        "OFAC_SDN": load_ofac_sdn,
        "EU": load_eu_sanctions,
        "UN": load_un_sanctions,
        "UK_OFSI": load_uk_ofsi,
    }

    if lists is None:
        lists = list(loaders.keys())

    all_entities = []
    metadata = {
        "loaded_at": datetime.now().isoformat(),
        "lists": {},
        "total_entities": 0,
    }

    for list_name in lists:
        loader = loaders.get(list_name)
        if loader is None:
            print(f"[!] Unknown list: {list_name}")
            continue

        entities = loader()
        all_entities.extend(entities)
        metadata["lists"][list_name] = {
            "count": len(entities),
            "loaded_at": datetime.now().isoformat(),
        }

    metadata["total_entities"] = len(all_entities)

    print(f"\n[+] TOTAL: {len(all_entities)} entities across "
          f"{len(metadata['lists'])} sanctions lists")

    return {
        "entities": all_entities,
        "metadata": metadata,
    }


# =============================================================================
# 6. QUICK TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  MULTI-SANCTIONS LIST LOADER TEST")
    print("  TradeScreenAI")
    print("=" * 70)

    result = load_all_sanctions_lists()

    print(f"\n  Summary:")
    for list_name, info in result["metadata"]["lists"].items():
        print(f"    {list_name}: {info['count']} entities")
    print(f"    TOTAL: {result['metadata']['total_entities']} entities")

    # Show sample from each list
    for list_name in ["OFAC_SDN", "EU", "UN", "UK_OFSI"]:
        samples = [e for e in result["entities"]
                   if e["list_source"] == list_name][:3]
        if samples:
            print(f"\n  Sample {list_name} entries:")
            for s in samples:
                aliases_str = f" (aliases: {len(s['aliases'])})" if s['aliases'] else ""
                print(f"    - {s['name']}{aliases_str} [{s['entity_type']}]")
