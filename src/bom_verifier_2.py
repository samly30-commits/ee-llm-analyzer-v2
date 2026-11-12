import re
import pandas as pd


def expand_refdes_string(text):
    """'R1-R5, C1, U1' 형태의 비정형 문자열을 개별 부품 부호 리스트로 확장합니다."""
    if not isinstance(text, str):
        return []

    text = text.upper()
    expanded = []

    range_pattern = r"\b([A-Z]+)(\d+)\s*-\s*([A-Z]+)?(\d+)\b"
    ranges = re.findall(range_pattern, text)
    for pref1, start, pref2, end in ranges:
        prefix = pref2 if pref2 else pref1
        s_num, e_num = int(start), int(end)
        if s_num <= e_num:
            for i in range(s_num, e_num + 1):
                expanded.append(f"{prefix}{i}")

    cleaned_text = re.sub(range_pattern, "", text)
    singles = re.findall(r"\b[A-Z]+\d+\b", cleaned_text)

    return sorted(list(set(expanded + singles)))


def parse_gerber_bom_text(raw_text):
    """Gerber Pick-and-Place 텍스트(부품명:패키지 또는 단순 나열)를 딕셔너리로 구조화합니다."""
    gerber_map = {}
    lines = raw_text.strip().splitlines()

    for line in lines:
        pair_match = re.findall(r"\b([A-Z]+\d+)\s*[:\s]\s*([A-Z0-9_-]+)\b", line.upper())
        if pair_match:
            for ref, pkg in pair_match:
                gerber_map[ref] = pkg
        else:
            refs = expand_refdes_string(line)
            for ref in refs:
                if ref not in gerber_map:
                    gerber_map[ref] = "UNKNOWN"

    return gerber_map


def verify_design_integrity(gerber_raw_text, bom_file):
    """Gerber 데이터와 Excel BOM 간의 수량, 누락, 패키지 불일치를 정밀 검증합니다."""
    gerber_map = parse_gerber_bom_text(gerber_raw_text)
    df_bom = pd.read_excel(bom_file)

    ref_col = next((c for c in df_bom.columns if any(k in c.lower() for k in ["designator", "ref", "부품"])), None)
    pkg_col = next((c for c in df_bom.columns if any(k in c.lower() for k in ["footprint", "package", "패키지", "규격"])), None)

    if not ref_col:
        return {"error": "BOM 파일에서 부품 참조 부호(Designator/RefDes) 열을 찾을 수 없습니다."}

    bom_map = {}
    for _, row in df_bom.iterrows():
        refs = expand_refdes_string(str(row[ref_col]))
        pkg = str(row[pkg_col]).strip().upper() if pkg_col and pd.notna(row[pkg_col]) else "UNKNOWN"
        for r in refs:
            bom_map[r] = pkg

    gerber_set = set(gerber_map.keys())
    bom_set = set(bom_map.keys())

    missing_in_bom = sorted(list(gerber_set - bom_set))
    extra_in_bom = sorted(list(bom_set - gerber_set))

    pkg_mismatches = []
    for common_ref in sorted(list(gerber_set & bom_set)):
        g_pkg = gerber_map[common_ref]
        b_pkg = bom_map[common_ref]
        if g_pkg != "UNKNOWN" and b_pkg != "UNKNOWN" and g_pkg != b_pkg:
            pkg_mismatches.append({
                "RefDes": common_ref,
                "Gerber_Footprint": g_pkg,
                "BOM_Package": b_pkg
            })

    return {
        "total_gerber": len(gerber_set),
        "total_bom": len(bom_set),
        "missing_in_bom": missing_in_bom,
        "extra_in_bom": extra_in_bom,
        "pkg_mismatches": pkg_mismatches,
    }
