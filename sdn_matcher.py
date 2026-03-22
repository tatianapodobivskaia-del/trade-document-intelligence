"""
AI-Powered Trade Document Screening System
OFAC SDN Fuzzy Matching Engine with Cyrillic Transliteration Support

Author: Tatiana Pankratova
Project: AI-Powered Trade Document Intelligence for Cross-Border Procurement Compliance

Description:
    Loads consolidated sanctions data (OFAC SDN, EU, UN, UK OFSI) via
    sanctions_lists, parses entity names and aliases, and performs fuzzy
    matching against vendor/supplier names from trade documents. Includes
    Cyrillic-to-Latin transliteration for Russian-language variations.

Dependencies:
    pip install requests fuzzywuzzy python-Levenshtein transliterate pandas
"""

import requests
import csv
import io
import re
import json
import pandas as pd
from datetime import datetime
from fuzzywuzzy import fuzz, process
from transliterate import translit

from sanctions_lists import load_all_sanctions_lists


# =============================================================================
# 1. OFAC SDN LIST LOADER (legacy single-list helpers)
# =============================================================================

def download_sdn_list(url="https://www.treasury.gov/ofac/downloads/sdn.csv"):
    """Download the official OFAC SDN list from U.S. Treasury."""
    print("[*] Downloading OFAC SDN list from U.S. Treasury...")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        print(f"[+] Downloaded successfully ({len(resp.content)} bytes)")
        return resp.text
    except requests.RequestException as e:
        print(f"[!] Error downloading SDN list: {e}")
        return None


def parse_sdn_list(raw_csv):
    """Parse SDN CSV into list of entity names."""
    entities = []
    reader = csv.reader(io.StringIO(raw_csv))
    for row in reader:
        if len(row) >= 2:
            name = row[1].strip()
            if name and name != "-0-":
                ent_type = row[2].strip() if len(row) >= 3 else "unknown"
                entities.append({
                    "sdn_name": name,
                    "type": ent_type,
                    "program": row[3].strip() if len(row) >= 4 else ""
                })
    print(f"[+] Parsed {len(entities)} entities from SDN list")
    return entities


def unified_entities_to_matcher_rows(unified_entities):
    """
    Expand sanctions_lists unified records into rows with sdn_name/type/program
    for screen_vendor (primary name + deduplicated aliases).
    """
    rows = []
    for e in unified_entities:
        names = [e.get("name", "")] + list(e.get("aliases") or [])
        seen = set()
        for n in names:
            n = (n or "").strip()
            if not n:
                continue
            key = n.lower()
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "sdn_name": n,
                "type": e.get("entity_type", "unknown"),
                "program": e.get("program", ""),
                "list_source": e.get("list_source", ""),
            })
    return rows


# =============================================================================
# 2. CYRILLIC TRANSLITERATION ENGINE
# =============================================================================

CYRILLIC_VARIANTS = {
    "щ": ["shch", "sch", "chtch", "stch"],
    "ш": ["sh", "ch"],
    "ч": ["ch", "tch", "č"],
    "ж": ["zh", "j", "ž"],
    "ц": ["ts", "tz", "c"],
    "х": ["kh", "h", "x"],
    "ю": ["yu", "iu", "ju"],
    "я": ["ya", "ia", "ja"],
    "ё": ["yo", "io", "jo", "e"],
    "э": ["e", "eh"],
    "й": ["y", "i", "j"],
    "ы": ["y", "i"],
    "ъ": ["", "ie"],
    "ь": ["", "'"],
}

ENTITY_SUFFIXES = {
    "ООО": ["OOO", "LLC"],
    "ОАО": ["OAO", "OJSC", "JSC"],
    "ЗАО": ["ZAO", "CJSC"],
    "ПАО": ["PAO", "PJSC"],
    "АО": ["AO", "JSC"],
    "ИП": ["IP", "IE", "Individual Entrepreneur"],
}


def generate_transliteration_variants(cyrillic_name):
    """
    Generate multiple Latin-script variants of a Cyrillic name.
    
    Standard tools produce ONE transliteration. This function produces
    multiple variants based on different transliteration systems
    (ISO 9, BGN/PCGN, popular/informal, passport-style).
    """
    variants = set()
    
    # Variant 1: Standard library transliteration
    try:
        v1 = translit(cyrillic_name, "ru", reversed=True)
        variants.add(v1.lower())
    except Exception:
        pass
    
    # Variant 2: Simplified (drop soft/hard signs, simplify clusters)
    simplified = cyrillic_name.lower()
    simple_map = {
        "щ": "shch", "ш": "sh", "ч": "ch", "ж": "zh",
        "ц": "ts", "х": "kh", "ю": "yu", "я": "ya",
        "ё": "yo", "э": "e", "й": "y", "ы": "y",
        "ъ": "", "ь": "",
        "а": "a", "б": "b", "в": "v", "г": "g",
        "д": "d", "е": "e", "з": "z", "и": "i",
        "к": "k", "л": "l", "м": "m", "н": "n",
        "о": "o", "п": "p", "р": "r", "с": "s",
        "т": "t", "у": "u", "ф": "f",
    }
    v2 = ""
    for ch in simplified:
        v2 += simple_map.get(ch, ch)
    variants.add(v2)
    
    # Variant 3: Passport-style
    passport_map = dict(simple_map)
    passport_map.update({"щ": "shch", "ё": "e", "й": "i", "ц": "tc"})
    v3 = ""
    for ch in simplified:
        v3 += passport_map.get(ch, ch)
    variants.add(v3)
    
    # Variant 4: German-influenced (common in older documents)
    german_map = dict(simple_map)
    german_map.update({
        "щ": "schtsch", "ш": "sch", "ч": "tsch",
        "ж": "sh", "ц": "z", "х": "ch",
        "ю": "ju", "я": "ja", "й": "j"
    })
    v4 = ""
    for ch in simplified:
        v4 += german_map.get(ch, ch)
    variants.add(v4)
    
    # Check for entity type suffixes
    for cyr_suffix, lat_variants in ENTITY_SUFFIXES.items():
        if cyr_suffix in cyrillic_name:
            for lat_var in lat_variants:
                for v in list(variants):
                    try:
                        variants.add(v.replace(
                            translit(cyr_suffix, "ru", reversed=True).lower(),
                            lat_var.lower()
                        ))
                    except Exception:
                        pass
    
    return list(variants)


# =============================================================================
# 3. FUZZY MATCHING ENGINE
# =============================================================================

def calculate_match_score(vendor_name, sdn_name):
    """Calculate composite similarity score using multiple algorithms."""
    vendor_clean = vendor_name.lower().strip()
    sdn_clean = sdn_name.lower().strip()
    
    if vendor_clean == sdn_clean:
        return 100, "exact"
    
    token_sort = fuzz.token_sort_ratio(vendor_clean, sdn_clean)
    token_set = fuzz.token_set_ratio(vendor_clean, sdn_clean)
    partial = fuzz.partial_ratio(vendor_clean, sdn_clean)
    standard = fuzz.ratio(vendor_clean, sdn_clean)
    
    composite = (
        token_sort * 0.30 +
        token_set * 0.30 +
        partial * 0.25 +
        standard * 0.15
    )
    
    scores = {
        "token_sort": token_sort,
        "token_set": token_set,
        "partial": partial,
        "standard": standard
    }
    best_method = max(scores, key=scores.get)
    
    return round(composite, 1), best_method


def screen_vendor(vendor_name, sdn_entities, threshold_high=85,
                  threshold_medium=50, cyrillic_name=None):
    """Screen a single vendor against the SDN list."""
    best_match = None
    best_score = 0
    best_method = ""
    
    names_to_check = [vendor_name]
    
    if cyrillic_name:
        variants = generate_transliteration_variants(cyrillic_name)
        names_to_check.extend(variants)
    
    for name in names_to_check:
        for entity in sdn_entities:
            score, method = calculate_match_score(name, entity["sdn_name"])
            if score > best_score:
                best_score = score
                best_match = entity
                best_method = method
    
    if best_score >= threshold_high:
        risk = "HIGH"
        action = "BLOCK — Escalate for manual review"
    elif best_score >= threshold_medium:
        risk = "MEDIUM"
        action = "FLAG — Requires compliance officer review"
    else:
        risk = "LOW"
        action = "APPROVE — Auto-cleared"
    
    return {
        "vendor_name": vendor_name,
        "cyrillic_name": cyrillic_name or "N/A",
        "best_sdn_match": best_match["sdn_name"] if best_match else "None",
        "matched_list_source": (
            best_match.get("list_source", "") if best_match else "N/A"
        ),
        "sdn_type": best_match["type"] if best_match else "N/A",
        "sdn_program": best_match["program"] if best_match else "N/A",
        "similarity_score": best_score,
        "match_method": best_method,
        "risk_level": risk,
        "action": action,
        "transliteration_variants": (
            generate_transliteration_variants(cyrillic_name)
            if cyrillic_name else []
        ),
        "timestamp": datetime.now().isoformat()
    }


# =============================================================================
# 4. BATCH SCREENING
# =============================================================================

def screen_vendor_file(filepath, sdn_entities):
    """Screen a CSV file of vendors against SDN list."""
    df = pd.read_csv(filepath)
    results = []
    
    for _, row in df.iterrows():
        vendor = row.get("vendor_name", "").strip()
        cyrillic = row.get("cyrillic_name", None)
        if pd.isna(cyrillic):
            cyrillic = None
        
        if vendor:
            result = screen_vendor(vendor, sdn_entities, cyrillic_name=cyrillic)
            result["country"] = row.get("country", "N/A")
            result["amount"] = row.get("amount", 0)
            result["document_type"] = row.get("document_type", "N/A")
            results.append(result)
    
    return pd.DataFrame(results)


# =============================================================================
# 5. SAMPLE DATA & DEMO
# =============================================================================

SAMPLE_VENDORS = [
    {
        "vendor_name": "Global Energy Trading Ltd",
        "country": "UAE",
        "amount": 250000,
        "document_type": "Invoice",
        "cyrillic_name": None
    },
    {
        "vendor_name": "Shcherbakov Import Export",
        "country": "Turkey",
        "amount": 180000,
        "document_type": "Bill of Lading",
        "cyrillic_name": "Щербаков Импорт Экспорт"
    },
    {
        "vendor_name": "Vneshtorgbank International",
        "country": "Cyprus",
        "amount": 500000,
        "document_type": "Certificate of Origin",
        "cyrillic_name": "Внешторгбанк Интернэшнл"
    },
    {
        "vendor_name": "Sunny Day Flowers Co",
        "country": "Colombia",
        "amount": 12000,
        "document_type": "Invoice",
        "cyrillic_name": None
    },
    {
        "vendor_name": "Rosoboronexport Trading",
        "country": "Russia",
        "amount": 750000,
        "document_type": "Bill of Lading",
        "cyrillic_name": "Рособоронэкспорт Трейдинг"
    },
    {
        "vendor_name": "Miami Fresh Produce LLC",
        "country": "USA",
        "amount": 8500,
        "document_type": "Invoice",
        "cyrillic_name": None
    },
    {
        "vendor_name": "Zhukovsky Aviation Corp",
        "country": "UAE",
        "amount": 320000,
        "document_type": "Certificate of Origin",
        "cyrillic_name": "Жуковский Авиация Корп"
    },
]


def run_demo():
    """Run full demonstration of the screening system."""
    print("=" * 70)
    print("  AI-POWERED TRADE DOCUMENT SCREENING SYSTEM")
    print("  Multi-list sanctions screening (OFAC / EU / UN / UK OFSI)")
    print("  Author: Tatiana Pankratova")
    print("=" * 70)
    print()
    
    # Step 1: Load all sanctions lists
    loaded = load_all_sanctions_lists()
    sdn_entities = unified_entities_to_matcher_rows(loaded["entities"])
    print(f"[+] Matcher rows (names + aliases): {len(sdn_entities)}")
    if not sdn_entities:
        print("[!] Cannot proceed without sanctions data")
        return
    
    # Step 2: Demonstrate Cyrillic transliteration
    print("\n" + "=" * 70)
    print("  CYRILLIC TRANSLITERATION DEMO")
    print("=" * 70)
    
    demo_names = ["Щербаков", "Внешторгбанк", "Рособоронэкспорт", "Жуковский"]
    for name in demo_names:
        variants = generate_transliteration_variants(name)
        print(f"\n  {name}:")
        for v in variants:
            print(f"    -> {v}")
    
    # Step 3: Screen sample vendors
    print("\n" + "=" * 70)
    print("  VENDOR SCREENING RESULTS")
    print("=" * 70)
    
    results = []
    for vendor in SAMPLE_VENDORS:
        result = screen_vendor(
            vendor["vendor_name"],
            sdn_entities,
            cyrillic_name=vendor.get("cyrillic_name")
        )
        result["country"] = vendor["country"]
        result["amount"] = vendor["amount"]
        result["document_type"] = vendor["document_type"]
        results.append(result)
        
        risk_icon = {"HIGH": "[!!!]", "MEDIUM": "[!!]", "LOW": "[OK]"}.get(
            result["risk_level"], "[--]"
        )
        
        print(f"\n  {risk_icon} {result['vendor_name']}")
        print(f"     Country: {result['country']}")
        print(f"     Amount: ${result['amount']:,.0f}")
        print(f"     Document: {result['document_type']}")
        src = result.get("matched_list_source", "N/A")
        print(f"     Best match: {result['best_sdn_match']} [{src}]")
        print(f"     Similarity: {result['similarity_score']}%")
        print(f"     Risk: {result['risk_level']}")
        print(f"     Action: {result['action']}")
        if result['transliteration_variants']:
            print(f"     Cyrillic variants checked: "
                  f"{len(result['transliteration_variants'])}")
    
    # Step 4: Summary
    df = pd.DataFrame(results)
    print("\n" + "=" * 70)
    print("  SCREENING SUMMARY")
    print("=" * 70)
    print(f"\n  Total vendors screened: {len(df)}")
    print(f"  HIGH risk (blocked):    "
          f"{len(df[df['risk_level'] == 'HIGH'])}")
    print(f"  MEDIUM risk (flagged):  "
          f"{len(df[df['risk_level'] == 'MEDIUM'])}")
    print(f"  LOW risk (approved):    "
          f"{len(df[df['risk_level'] == 'LOW'])}")
    print(f"\n  Total value screened:   ${df['amount'].sum():,.0f}")
    print(f"  High-risk value:        "
          f"${df[df['risk_level'] == 'HIGH']['amount'].sum():,.0f}")
    
    # Step 5: Export
    output_file = "screening_results.csv"
    df.to_csv(output_file, index=False)
    print(f"\n  Results exported to: {output_file}")
    
    json_file = "screening_results.json"
    df.to_json(json_file, orient="records", indent=2)
    print(f"  JSON export for Power BI: {json_file}")
    
    print("\n" + "=" * 70)
    print("  SCREENING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
