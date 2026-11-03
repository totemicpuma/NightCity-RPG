#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
COMPILADOR OFFLINE DO APK STANDALONE — NIGHT CITY RPG MOBILE (ANDROID)
=============================================================================
Gera o instalador nativo Android (dist/NightCityRPG-Standalone.apk) 100%
offline usando:
- Ícone Cyberpunk 2077 personalizado em alta definição (res/drawable/icon.png)
  compilado em resources.arsc (0x7f010000)
- Banco de dados inicial completo embutido (Obsidian + SUAP + Classroom + P&D)
- Notificações nativas padrão do sistema Android (na barra de notificações do
  celular, SEM pop-up flutuante atrapalhando as telas do app!) com botões de
  ação direta na notificação: [✔ Concluir (+10 XP)] e [🔕 Silenciar]
- Classes nativas Android (MainActivity + AndroidBridge + NotificationActionReceiver)
  compiladas em Dalvik Bytecode (classes.dex) via smali.jar
- AndroidManifest.xml (AXML binário) + resources.arsc
- Assinatura oficial Android v1 + v2 + v3 + zipalign via uber-apk-signer.jar
=============================================================================
"""

import io
import json
import os
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
TOOLS_DIR = BASE_DIR / "tools"
SMALI_DIR = BASE_DIR / "smali_src"
DIST_DIR = BASE_DIR / "dist"
WWW_DIR = BASE_DIR / "www"

JAVA_EXE = r"C:\Program Files\Java\jre1.8.0_481\bin\java.exe"
if not os.path.exists(JAVA_EXE):
    JAVA_EXE = shutil.which("java") or "java"

SMALI_JAR = TOOLS_DIR / "smali.jar"
SIGNER_JAR = TOOLS_DIR / "uber-apk-signer.jar"

APP_ICON_RES_ID = 0x7F010000
WIDGET_LAYOUT_RES_ID = 0x7F020000
WIDGET_INFO_RES_ID = 0x7F030000


# ---------------------------------------------------------------------------
# 0. GERADOR DO ÍCONE CYBERPUNK 2077 PERSONALIZADO (PNG 256x256)
# ---------------------------------------------------------------------------
def generate_cyberpunk_icon_png(size: int = 256) -> bytes:
    # Renderiza em 512x512 com supersampling 2x para bordas ultra nítidas
    W = 512
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Placa de fundo chanfrada estilo Cyberpunk 2077 (Preto Obsidiana + Borda Amarelo Neon)
    cut = 68
    pad = 16
    outer_poly = [
        (pad + cut, pad),
        (W - pad - 24, pad),
        (W - pad, pad + 24),
        (W - pad, W - pad - cut),
        (W - pad - cut, W - pad),
        (pad + 24, W - pad),
        (pad, W - pad - 24),
        (pad, pad + cut),
    ]
    # Sombra externa neon ciano/rosa
    glow_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer)
    gdraw.polygon(outer_poly, fill=(0, 240, 255, 90), outline=(252, 238, 10, 255))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(10))
    img = Image.alpha_composite(img, glow_layer)
    draw = ImageDraw.Draw(img)

    # Moldura externa Amarelo Cyberpunk (#fcee0a)
    draw.polygon(outer_poly, fill=(252, 238, 10, 255))

    # Miolo escuro Night City (#080911)
    b = 14
    inner_poly = [
        (pad + cut + 6, pad + b),
        (W - pad - 24 - 6, pad + b),
        (W - pad - b, pad + 24 + 6),
        (W - pad - b, W - pad - cut - 6),
        (W - pad - cut - 6, W - pad - b),
        (pad + 24 + 6, W - pad - b),
        (pad + b, W - pad - 24 - 6),
        (pad + b, pad + cut + 6),
    ]
    draw.polygon(inner_poly, fill=(9, 11, 20, 255))

    # 2. Grade e trilhas de circuito Netrunner (Ciano #00f0ff e Rosa #ff003c)
    for y_line in range(80, 430, 38):
        draw.line([(44, y_line), (W - 44, y_line)], fill=(0, 240, 255, 22), width=2)
    for x_line in range(80, 430, 38):
        draw.line([(x_line, 44), (x_line, W - 44)], fill=(0, 240, 255, 22), width=2)

    # Trilhas superiores direitas (Ciano Neon)
    draw.line([(110, 56), (340, 56), (370, 86), (445, 86)], fill=(0, 240, 255, 210), width=5)
    draw.ellipse((438, 79, 452, 93), fill=(0, 240, 255, 255))

    # Trilhas inferiores esquerdas (Magenta/Vermelho Trauma Team #ff003c)
    draw.line([(68, 416), (140, 416), (170, 448), (375, 448)], fill=(255, 0, 60, 235), width=6)
    draw.ellipse((61, 409, 75, 423), fill=(255, 0, 60, 255))

    # 3. Emblema "V" Metálico / Neon de fundo
    v_left = [(108, 128), (168, 128), (256, 336), (256, 396)]
    v_right = [(404, 128), (344, 128), (256, 336), (256, 396)]
    draw.polygon(v_left, fill=(0, 240, 255, 55), outline=(0, 240, 255, 190))
    draw.polygon(v_right, fill=(255, 0, 60, 55), outline=(255, 0, 60, 190))

    # 4. Raio Central Cyberpunk (Glitch Rosa + Glitch Ciano + Raio Principal Amarelo #fcee0a)
    bolt = [
        (286, 78),
        (146, 268),
        (248, 268),
        (210, 426),
        (374, 224),
        (268, 224),
    ]
    bolt_pink = [(x - 10, y + 6) for x, y in bolt]
    bolt_cyan = [(x + 10, y - 6) for x, y in bolt]

    draw.polygon(bolt_pink, fill=(255, 0, 60, 220))
    draw.polygon(bolt_cyan, fill=(0, 240, 255, 220))
    draw.polygon(bolt, fill=(252, 238, 10, 255), outline=(255, 255, 255, 255))

    # 5. Barra de XP Neon Verde (#00ff9f) na base do ícone
    bar_x1, bar_y1, bar_x2, bar_y2 = 104, 418, 408, 434
    draw.rectangle([bar_x1, bar_y1, bar_x2, bar_y2], fill=(18, 24, 38, 255), outline=(0, 240, 255, 200), width=2)
    draw.rectangle([bar_x1 + 3, bar_y1 + 3, bar_x1 + 235, bar_y2 - 3], fill=(0, 255, 159, 255))

    # Detalhes de canto tecnológico (Kiroshi HUD)
    draw.rectangle([48, 102, 60, 154], fill=(252, 238, 10, 255))
    draw.rectangle([452, 350, 464, 402], fill=(0, 240, 255, 255))

    final_img = img.resize((size, size), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    final_img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. GERADOR DE STRING POOL E RESOURCES.ARSC (0x7f010000 -> res/drawable/icon.png)
# ---------------------------------------------------------------------------
def build_string_pool(strings_list: list) -> bytes:
    encoded_strings = []
    offsets = []
    cur_offset = 0
    for s in strings_list:
        offsets.append(cur_offset)
        u16 = s.encode("utf-16le")
        char_len = len(u16) // 2
        entry = struct.pack("<H", char_len) + u16 + struct.pack("<H", 0)
        encoded_strings.append(entry)
        cur_offset += len(entry)

    str_blob = b"".join(encoded_strings)
    while len(str_blob) % 4 != 0:
        str_blob += b"\x00"

    strings_start = 28 + 4 * len(strings_list)
    sp_chunk_size = strings_start + len(str_blob)
    sp_header = struct.pack(
        "<HHIIIIII",
        0x0001,  # RES_STRING_POOL_TYPE
        28,
        sp_chunk_size,
        len(strings_list),
        0,
        0,       # UTF-16LE
        strings_start,
        0,
    )
    sp_offsets = b"".join(struct.pack("<I", off) for off in offsets)
    return sp_header + sp_offsets + str_blob


def build_resources_arsc(package_name="com.cyberdeck.nightcityrpg") -> bytes:
    # Global String Pool (caminhos dos recursos empacotados no APK)
    # 0 -> res/drawable/icon.png        (0x7f010000)
    # 1 -> res/layout/quest_widget.xml  (0x7f020000)
    # 2 -> res/xml/quest_widget_info.xml(0x7f030000)
    global_sp = build_string_pool([
        "res/drawable/icon.png",
        "res/layout/quest_widget.xml",
        "res/xml/quest_widget_info.xml",
    ])

    # Type String Pool (id 1="drawable", id 2="layout", id 3="xml")
    type_sp = build_string_pool(["drawable", "layout", "xml"])
    # Key String Pool (0="icon", 1="quest_widget", 2="quest_widget_info")
    key_sp = build_string_pool(["icon", "quest_widget", "quest_widget_info"])

    config_bytes = struct.pack("<I", 36) + (b"\x00" * 32)
    type_header_size = 20 + len(config_bytes)  # 56 bytes
    entries_start = type_header_size + 4       # 60 bytes

    type_chunks_list = []
    for type_id, key_idx, global_str_idx in [(1, 0, 0), (2, 1, 1), (3, 2, 2)]:
        type_spec = struct.pack(
            "<HHIBBHII",
            0x0202,   # RES_TABLE_TYPE_SPEC_TYPE
            16,       # headerSize
            20,       # size (16 + 4*1)
            type_id,  # id (1-based)
            0,
            0,
            1,        # entryCount = 1
            0,        # flags[0] = 0
        )
        entry_and_val = struct.pack("<HHIHBBI", 8, 0, key_idx, 8, 0, 0x03, global_str_idx)
        type_chunk_size = entries_start + len(entry_and_val)  # 76 bytes
        type_chunk = (
            struct.pack(
                "<HHIBBHII",
                0x0201,  # RES_TABLE_TYPE_TYPE
                type_header_size,
                type_chunk_size,
                type_id,
                0,
                0,
                1,       # entryCount = 1
                entries_start,
            )
            + config_bytes
            + struct.pack("<I", 0)  # offset[0] = 0
            + entry_and_val
        )
        type_chunks_list.append(type_spec + type_chunk)

    # ResTable_package (0x0200)
    pkg_header_size = 288
    name_u16 = package_name.encode("utf-16le")[:254]
    name_padded = name_u16 + (b"\x00" * (256 - len(name_u16)))

    type_strings_offset = pkg_header_size
    key_strings_offset = pkg_header_size + len(type_sp)
    pkg_body = type_sp + key_sp + b"".join(type_chunks_list)
    pkg_total_size = pkg_header_size + len(pkg_body)

    pkg_header = (
        struct.pack("<HHII", 0x0200, pkg_header_size, pkg_total_size, 0x7F)
        + name_padded
        + struct.pack(
            "<IIIII",
            type_strings_offset,
            3,  # lastPublicType
            key_strings_offset,
            3,  # lastPublicKey
            0,  # typeIdOffset
        )
    )
    pkg_chunk = pkg_header + pkg_body

    total_size = 12 + len(global_sp) + len(pkg_chunk)
    table_header = struct.pack("<HHII", 0x0002, 12, total_size, 1)
    return table_header + global_sp + pkg_chunk


# ---------------------------------------------------------------------------
# 2. GERADORES DE AXML BINÁRIO (AndroidManifest.xml + Widget XMLs)
# ---------------------------------------------------------------------------
def build_binary_android_manifest(package_name="com.cyberdeck.nightcityrpg", version_code=2087, version_name="2.0.87") -> bytes:
    attr_defs = [
        ("theme", 0x01010000),
        ("label", 0x01010001),
        ("icon", 0x01010002),
        ("name", 0x01010003),
        ("exported", 0x01010010),
        ("configChanges", 0x0101001f),
        ("resource", 0x01010025),
        ("minSdkVersion", 0x0101020c),
        ("versionCode", 0x0101021b),
        ("versionName", 0x0101021c),
        ("targetSdkVersion", 0x01010270),
        ("hardwareAccelerated", 0x010102d3),
        ("usesCleartextTraffic", 0x010104ec),
    ]

    strings = [name for name, _ in attr_defs]
    res_ids = [rid for _, rid in attr_defs]

    def get_str_idx(s: str) -> int:
        if s not in strings:
            strings.append(s)
        return strings.index(s)

    NS_PREFIX = "android"
    NS_URI = "http://schemas.android.com/apk/res/android"
    for s in [
        NS_PREFIX,
        NS_URI,
        "manifest",
        "package",
        package_name,
        version_name,
        "uses-sdk",
        "uses-permission",
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE",
        "android.permission.VIBRATE",
        "android.permission.POST_NOTIFICATIONS",
        "application",
        "Night City RPG",
        "activity",
        f"{package_name}.MainActivity",
        "intent-filter",
        "action",
        "android.intent.action.MAIN",
        "category",
        "android.intent.category.LAUNCHER",
        "receiver",
        f"{package_name}.NotificationActionReceiver",
        f"{package_name}.QuestWidgetProvider",
        "⚡ Night City Quests",
        "android.appwidget.action.APPWIDGET_UPDATE",
        "com.cyberdeck.nightcityrpg.WIDGET_COMPLETE",
        "com.cyberdeck.nightcityrpg.WIDGET_NEXT",
        "com.cyberdeck.nightcityrpg.WIDGET_REFRESH",
        "meta-data",
        "android.appwidget.provider",
    ]:
        get_str_idx(s)

    TYPE_REFERENCE = 0x01
    TYPE_STRING = 0x03
    TYPE_INT_DEC = 0x10
    TYPE_INT_HEX = 0x11
    TYPE_INT_BOOLEAN = 0x12

    def make_attr(ns_str, name_str, val_type, data_val, raw_str=None):
        ns_i = get_str_idx(ns_str) if ns_str else 0xFFFFFFFF
        name_i = get_str_idx(name_str)
        if val_type == TYPE_STRING:
            raw_i = get_str_idx(raw_str if raw_str is not None else str(data_val))
            data_v = raw_i
        else:
            raw_i = 0xFFFFFFFF
            data_v = data_val & 0xFFFFFFFF
        return (name_i, struct.pack("<IIIHBBI", ns_i, name_i, raw_i, 8, 0, val_type, data_v))

    def start_element(tag: str, attrs_list: list, line: int = 1) -> bytes:
        sorted_attrs = [b for _, b in sorted(attrs_list, key=lambda x: x[0])]
        attr_bytes = b"".join(sorted_attrs)
        chunk_size = 36 + len(attr_bytes)
        header = struct.pack(
            "<HHIIIIIHHHHHH",
            0x0102,
            16,
            chunk_size,
            line,
            0xFFFFFFFF,
            0xFFFFFFFF,
            get_str_idx(tag),
            20,
            20,
            len(sorted_attrs),
            0,
            0,
            0,
        )
        return header + attr_bytes

    def end_element(tag: str, line: int = 1) -> bytes:
        return struct.pack(
            "<HHIIIII",
            0x0103,
            16,
            24,
            line,
            0xFFFFFFFF,
            0xFFFFFFFF,
            get_str_idx(tag),
        )

    xml_chunks = []

    xml_chunks.append(
        struct.pack(
            "<HHIIIII",
            0x0100,
            16,
            24,
            1,
            0xFFFFFFFF,
            get_str_idx(NS_PREFIX),
            get_str_idx(NS_URI),
        )
    )

    xml_chunks.append(
        start_element(
            "manifest",
            [
                make_attr(NS_URI, "versionCode", TYPE_INT_DEC, version_code),
                make_attr(NS_URI, "versionName", TYPE_STRING, 0, version_name),
                make_attr(None, "package", TYPE_STRING, 0, package_name),
            ],
            line=2,
        )
    )

    xml_chunks.append(
        start_element(
            "uses-sdk",
            [
                make_attr(NS_URI, "minSdkVersion", TYPE_INT_DEC, 21),
                make_attr(NS_URI, "targetSdkVersion", TYPE_INT_DEC, 33),
            ],
            line=3,
        )
    )
    xml_chunks.append(end_element("uses-sdk", line=3))

    for perm in [
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE",
        "android.permission.VIBRATE",
        "android.permission.POST_NOTIFICATIONS",
    ]:
        xml_chunks.append(
            start_element(
                "uses-permission",
                [make_attr(NS_URI, "name", TYPE_STRING, 0, perm)],
                line=4,
            )
        )
        xml_chunks.append(end_element("uses-permission", line=4))

    # <application> usando nosso ícone Cyberpunk personalizado (APP_ICON_RES_ID = 0x7f010000)
    xml_chunks.append(
        start_element(
            "application",
            [
                make_attr(NS_URI, "theme", TYPE_REFERENCE, 0x01030006),
                make_attr(NS_URI, "label", TYPE_STRING, 0, "Night City RPG"),
                make_attr(NS_URI, "icon", TYPE_REFERENCE, APP_ICON_RES_ID),
                make_attr(NS_URI, "hardwareAccelerated", TYPE_INT_BOOLEAN, 0xFFFFFFFF),
                make_attr(NS_URI, "usesCleartextTraffic", TYPE_INT_BOOLEAN, 0xFFFFFFFF),
            ],
            line=8,
        )
    )

    # <activity> também com o ícone Cyberpunk personalizado
    xml_chunks.append(
        start_element(
            "activity",
            [
                make_attr(NS_URI, "theme", TYPE_REFERENCE, 0x01030006),
                make_attr(NS_URI, "label", TYPE_STRING, 0, "Night City RPG"),
                make_attr(NS_URI, "icon", TYPE_REFERENCE, APP_ICON_RES_ID),
                make_attr(NS_URI, "name", TYPE_STRING, 0, f"{package_name}.MainActivity"),
                make_attr(NS_URI, "exported", TYPE_INT_BOOLEAN, 0xFFFFFFFF),
                make_attr(NS_URI, "configChanges", TYPE_INT_HEX, 0x000004A0),
            ],
            line=9,
        )
    )

    xml_chunks.append(start_element("intent-filter", [], line=10))
    xml_chunks.append(
        start_element("action", [make_attr(NS_URI, "name", TYPE_STRING, 0, "android.intent.action.MAIN")], line=11)
    )
    xml_chunks.append(end_element("action", line=11))
    xml_chunks.append(
        start_element("category", [make_attr(NS_URI, "name", TYPE_STRING, 0, "android.intent.category.LAUNCHER")], line=12)
    )
    xml_chunks.append(end_element("category", line=12))
    xml_chunks.append(end_element("intent-filter", line=13))
    xml_chunks.append(end_element("activity", line=14))

    xml_chunks.append(
        start_element(
            "receiver",
            [
                make_attr(NS_URI, "name", TYPE_STRING, 0, f"{package_name}.NotificationActionReceiver"),
                make_attr(NS_URI, "exported", TYPE_INT_BOOLEAN, 0x00000000),
            ],
            line=15,
        )
    )
    xml_chunks.append(end_element("receiver", line=15))

    # <receiver> do Widget de Quests para a Tela Inicial (AppWidgetProvider)
    xml_chunks.append(
        start_element(
            "receiver",
            [
                make_attr(NS_URI, "label", TYPE_STRING, 0, "⚡ Night City Quests"),
                make_attr(NS_URI, "icon", TYPE_REFERENCE, APP_ICON_RES_ID),
                make_attr(NS_URI, "name", TYPE_STRING, 0, f"{package_name}.QuestWidgetProvider"),
                make_attr(NS_URI, "exported", TYPE_INT_BOOLEAN, 0xFFFFFFFF),
            ],
            line=16,
        )
    )
    xml_chunks.append(start_element("intent-filter", [], line=17))
    for act_name in [
        "android.appwidget.action.APPWIDGET_UPDATE",
        "com.cyberdeck.nightcityrpg.WIDGET_COMPLETE",
        "com.cyberdeck.nightcityrpg.WIDGET_NEXT",
        "com.cyberdeck.nightcityrpg.WIDGET_REFRESH",
    ]:
        xml_chunks.append(
            start_element("action", [make_attr(NS_URI, "name", TYPE_STRING, 0, act_name)], line=18)
        )
        xml_chunks.append(end_element("action", line=18))
    xml_chunks.append(end_element("intent-filter", line=19))
    xml_chunks.append(
        start_element(
            "meta-data",
            [
                make_attr(NS_URI, "name", TYPE_STRING, 0, "android.appwidget.provider"),
                make_attr(NS_URI, "resource", TYPE_REFERENCE, WIDGET_INFO_RES_ID),
            ],
            line=20,
        )
    )
    xml_chunks.append(end_element("meta-data", line=20))
    xml_chunks.append(end_element("receiver", line=21))

    xml_chunks.append(end_element("application", line=22))
    xml_chunks.append(end_element("manifest", line=23))

    xml_chunks.append(
        struct.pack(
            "<HHIIIII",
            0x0101,
            16,
            24,
            24,
            0xFFFFFFFF,
            get_str_idx(NS_PREFIX),
            get_str_idx(NS_URI),
        )
    )

    sp_chunk = build_string_pool(strings)
    res_map_size = 8 + 4 * len(res_ids)
    res_map_chunk = struct.pack("<HHI", 0x0180, 8, res_map_size) + b"".join(
        struct.pack("<I", rid) for rid in res_ids
    )

    body = sp_chunk + res_map_chunk + b"".join(xml_chunks)
    file_header = struct.pack("<HHI", 0x0003, 8, 8 + len(body))
    return file_header + body


def build_binary_widget_info_xml() -> bytes:
    """
    Gera res/xml/quest_widget_info.xml (AXML binário para <appwidget-provider>).
    IDs oficiais android.R.attr:
      - minWidth           = 0x0101013f (16843071)
      - minHeight          = 0x01010140 (16843072)
      - updatePeriodMillis = 0x01010250 (16843344)
      - initialLayout      = 0x01010251 (16843345)
      - previewImage       = 0x010102da (16843482)
      - resizeMode         = 0x01010363 (16843619)
      - minResizeWidth     = 0x01010395 (16843669)
      - minResizeHeight    = 0x01010396 (16843670)
      - widgetCategory     = 0x010103c4 (16843716)
    """
    attr_defs = [
        ("minWidth", 0x0101013F),
        ("minHeight", 0x01010140),
        ("updatePeriodMillis", 0x01010250),
        ("initialLayout", 0x01010251),
        ("previewImage", 0x010102DA),
        ("resizeMode", 0x01010363),
        ("minResizeWidth", 0x01010395),
        ("minResizeHeight", 0x01010396),
        ("widgetCategory", 0x010103C4),
    ]
    strings = [name for name, _ in attr_defs]
    res_ids = [rid for _, rid in attr_defs]

    def get_str_idx(s: str) -> int:
        if s not in strings:
            strings.append(s)
        return strings.index(s)

    NS_PREFIX = "android"
    NS_URI = "http://schemas.android.com/apk/res/android"
    for s in [NS_PREFIX, NS_URI, "appwidget-provider"]:
        get_str_idx(s)

    TYPE_REFERENCE = 0x01
    TYPE_DIMENSION = 0x05
    TYPE_INT_DEC = 0x10
    TYPE_INT_HEX = 0x11

    def dp_val(v: int) -> int:
        return (v << 8) | 1  # COMPLEX_UNIT_DIP = 1

    def make_attr(name_str, val_type, data_val):
        ns_i = get_str_idx(NS_URI)
        name_i = get_str_idx(name_str)
        return (name_i, struct.pack("<IIIHBBI", ns_i, name_i, 0xFFFFFFFF, 8, 0, val_type, data_val & 0xFFFFFFFF))

    attrs = [
        make_attr("minWidth", TYPE_DIMENSION, dp_val(250)),
        make_attr("minHeight", TYPE_DIMENSION, dp_val(110)),
        make_attr("updatePeriodMillis", TYPE_INT_DEC, 1800000),
        make_attr("initialLayout", TYPE_REFERENCE, WIDGET_LAYOUT_RES_ID),
        make_attr("previewImage", TYPE_REFERENCE, APP_ICON_RES_ID),
        make_attr("resizeMode", TYPE_INT_HEX, 0x3),       # horizontal | vertical
        make_attr("minResizeWidth", TYPE_DIMENSION, dp_val(180)),
        make_attr("minResizeHeight", TYPE_DIMENSION, dp_val(90)),
        make_attr("widgetCategory", TYPE_INT_HEX, 0x1),   # home_screen
    ]
    sorted_attrs = [b for _, b in sorted(attrs, key=lambda x: x[0])]
    attr_bytes = b"".join(sorted_attrs)

    xml_chunks = [
        struct.pack("<HHIIIII", 0x0100, 16, 24, 1, 0xFFFFFFFF, get_str_idx(NS_PREFIX), get_str_idx(NS_URI)),
        struct.pack(
            "<HHIIIIIHHHHHH",
            0x0102,
            16,
            36 + len(attr_bytes),
            2,
            0xFFFFFFFF,
            0xFFFFFFFF,
            get_str_idx("appwidget-provider"),
            20,
            20,
            len(sorted_attrs),
            0,
            0,
            0,
        )
        + attr_bytes,
        struct.pack("<HHIIIII", 0x0103, 16, 24, 3, 0xFFFFFFFF, 0xFFFFFFFF, get_str_idx("appwidget-provider")),
        struct.pack("<HHIIIII", 0x0101, 16, 24, 4, 0xFFFFFFFF, get_str_idx(NS_PREFIX), get_str_idx(NS_URI)),
    ]

    sp_chunk = build_string_pool(strings)
    res_map_chunk = struct.pack("<HHI", 0x0180, 8, 8 + 4 * len(res_ids)) + b"".join(
        struct.pack("<I", rid) for rid in res_ids
    )
    body = sp_chunk + res_map_chunk + b"".join(xml_chunks)
    return struct.pack("<HHI", 0x0003, 8, 8 + len(body)) + body


def build_binary_widget_layout_xml() -> bytes:
    """
    Gera res/layout/quest_widget.xml em AXML binário (RemoteViews compatível com Samsung One UI).
    IDs padrão android.R.id usados:
      - 0x01020000 (android.R.id.background): Card raiz do Widget
      - 0x01020006 (android.R.id.icon)      : Ícone Cyberpunk 2077
      - 0x01020016 (android.R.id.title)     : Cabeçalho Nível + XP ("⚡ NIGHT CITY RPG · LV 5 (520 XP)")
      - 0x01020010 (android.R.id.summary)   : Subtítulo Classe + Streak + Contagem de Quests
      - 0x01020014 (android.R.id.text1)     : Quest em Destaque (Spotlight)
      - 0x01020015 (android.R.id.text2)     : Lista das próximas Quests pendentes
      - 0x01020019 (android.R.id.button1)   : Botão [✔ CONCLUIR (+XP)]
      - 0x0102001a (android.R.id.button2)   : Botão [⏭ PRÓXIMA]
      - 0x0102001b (android.R.id.button3)   : Botão [⚡ ABRIR APP]
    """
    # IMPORTANTE: manter ordenado de forma crescente pelo resource ID (0x0101xxxx)!
    attr_defs = [
        ("textSize", 0x01010095),
        ("textStyle", 0x01010097),
        ("textColor", 0x01010098),
        ("gravity", 0x010100AF),
        ("orientation", 0x010100C4),
        ("id", 0x010100D0),
        ("background", 0x010100D4),
        ("padding", 0x010100D5),
        ("paddingLeft", 0x010100D6),
        ("paddingTop", 0x010100D7),
        ("paddingRight", 0x010100D8),
        ("paddingBottom", 0x010100D9),
        ("layout_width", 0x010100F4),
        ("layout_height", 0x010100F5),
        ("layout_marginLeft", 0x010100F7),
        ("layout_marginTop", 0x010100F8),
        ("layout_marginRight", 0x010100F9),
        ("layout_marginBottom", 0x010100FA),
        ("src", 0x01010119),
        ("text", 0x0101014F),
        ("maxLines", 0x01010153),
        ("singleLine", 0x0101015D),
        ("layout_weight", 0x01010181),
    ]
    strings = [name for name, _ in attr_defs]
    res_ids = [rid for _, rid in attr_defs]

    def get_str_idx(s: str) -> int:
        if s not in strings:
            strings.append(s)
        return strings.index(s)

    NS_PREFIX = "android"
    NS_URI = "http://schemas.android.com/apk/res/android"
    for s in [NS_PREFIX, NS_URI, "LinearLayout", "ImageView", "TextView", "Button"]:
        get_str_idx(s)

    TYPE_REFERENCE = 0x01
    TYPE_STRING = 0x03
    TYPE_FLOAT = 0x04
    TYPE_DIMENSION = 0x05
    TYPE_INT_DEC = 0x10
    TYPE_INT_HEX = 0x11
    TYPE_INT_BOOLEAN = 0x12
    TYPE_INT_COLOR_ARGB8 = 0x1C

    MATCH_PARENT = -1
    WRAP_CONTENT = -2

    def dp(v: int) -> int:
        return (v << 8) | 1  # COMPLEX_UNIT_DIP = 1

    def sp(v: int) -> int:
        return (v << 8) | 2  # COMPLEX_UNIT_SP = 2

    def make_attr(name_str, val_type, data_val, raw_str=None):
        ns_i = get_str_idx(NS_URI)
        name_i = get_str_idx(name_str)
        if val_type == TYPE_STRING:
            raw_i = get_str_idx(raw_str if raw_str is not None else str(data_val))
            data_v = raw_i
        else:
            raw_i = 0xFFFFFFFF
            data_v = data_val & 0xFFFFFFFF
        return (name_i, struct.pack("<IIIHBBI", ns_i, name_i, raw_i, 8, 0, val_type, data_v))

    def start_el(tag: str, attrs_list: list, line: int = 1) -> bytes:
        sorted_attrs = [b for _, b in sorted(attrs_list, key=lambda x: x[0])]
        attr_bytes = b"".join(sorted_attrs)
        return (
            struct.pack(
                "<HHIIIIIHHHHHH",
                0x0102,
                16,
                36 + len(attr_bytes),
                line,
                0xFFFFFFFF,
                0xFFFFFFFF,
                get_str_idx(tag),
                20,
                20,
                len(sorted_attrs),
                0,
                0,
                0,
            )
            + attr_bytes
        )

    def end_el(tag: str, line: int = 1) -> bytes:
        return struct.pack("<HHIIIII", 0x0103, 16, 24, line, 0xFFFFFFFF, 0xFFFFFFFF, get_str_idx(tag))

    chunks = [
        struct.pack("<HHIIIII", 0x0100, 16, 24, 1, 0xFFFFFFFF, get_str_idx(NS_PREFIX), get_str_idx(NS_URI)),
        # 1. Container Raiz Cyberpunk (id = android.R.id.background = 0x01020000)
        start_el(
            "LinearLayout",
            [
                make_attr("id", TYPE_REFERENCE, 0x01020000),
                make_attr("orientation", TYPE_INT_DEC, 1),  # vertical
                make_attr("background", TYPE_INT_COLOR_ARGB8, 0xF20B0C16),
                make_attr("padding", TYPE_DIMENSION, dp(10)),
                make_attr("layout_width", TYPE_INT_DEC, MATCH_PARENT),
                make_attr("layout_height", TYPE_INT_DEC, MATCH_PARENT),
            ],
            line=2,
        ),
        # 2. Barra Superior: Ícone + Nível/XP + Subtítulo
        start_el(
            "LinearLayout",
            [
                make_attr("gravity", TYPE_INT_HEX, 0x10),  # center_vertical
                make_attr("orientation", TYPE_INT_DEC, 0),  # horizontal
                make_attr("layout_width", TYPE_INT_DEC, MATCH_PARENT),
                make_attr("layout_height", TYPE_INT_DEC, WRAP_CONTENT),
                make_attr("layout_marginBottom", TYPE_DIMENSION, dp(6)),
            ],
            line=3,
        ),
        start_el(
            "ImageView",
            [
                make_attr("id", TYPE_REFERENCE, 0x01020006),
                make_attr("layout_width", TYPE_DIMENSION, dp(32)),
                make_attr("layout_height", TYPE_DIMENSION, dp(32)),
                make_attr("layout_marginRight", TYPE_DIMENSION, dp(8)),
                make_attr("src", TYPE_REFERENCE, APP_ICON_RES_ID),
            ],
            line=4,
        ),
        end_el("ImageView", line=4),
        start_el(
            "LinearLayout",
            [
                make_attr("orientation", TYPE_INT_DEC, 1),  # vertical
                make_attr("layout_width", TYPE_DIMENSION, dp(0)),
                make_attr("layout_height", TYPE_INT_DEC, WRAP_CONTENT),
                make_attr("layout_weight", TYPE_FLOAT, 0x3F800000),  # 1.0f
            ],
            line=5,
        ),
        start_el(
            "TextView",
            [
                make_attr("textSize", TYPE_DIMENSION, sp(12)),
                make_attr("textStyle", TYPE_INT_HEX, 1),  # bold
                make_attr("textColor", TYPE_INT_COLOR_ARGB8, 0xFFFCEE0A),
                make_attr("id", TYPE_REFERENCE, 0x01020016),  # android.R.id.title
                make_attr("layout_width", TYPE_INT_DEC, MATCH_PARENT),
                make_attr("layout_height", TYPE_INT_DEC, WRAP_CONTENT),
                make_attr("text", TYPE_STRING, 0, "⚡ NIGHT CITY RPG · LV 5 (520 XP)"),
                make_attr("singleLine", TYPE_INT_BOOLEAN, 0xFFFFFFFF),
            ],
            line=6,
        ),
        end_el("TextView", line=6),
        start_el(
            "TextView",
            [
                make_attr("textSize", TYPE_DIMENSION, sp(10)),
                make_attr("textColor", TYPE_INT_COLOR_ARGB8, 0xFF00F0FF),
                make_attr("id", TYPE_REFERENCE, 0x01020010),  # android.R.id.summary
                make_attr("layout_width", TYPE_INT_DEC, MATCH_PARENT),
                make_attr("layout_height", TYPE_INT_DEC, WRAP_CONTENT),
                make_attr("text", TYPE_STRING, 0, "🛹 Street Kid · 🔥 Streak 1d · 5 Dailies Pendentes"),
                make_attr("singleLine", TYPE_INT_BOOLEAN, 0xFFFFFFFF),
            ],
            line=7,
        ),
        end_el("TextView", line=7),
        end_el("LinearLayout", line=8),
        end_el("LinearLayout", line=9),
        # 3. Card da Missão em Foco (Spotlight) — id = android.R.id.text1 (0x01020014)
        start_el(
            "TextView",
            [
                make_attr("textSize", TYPE_DIMENSION, sp(12)),
                make_attr("textStyle", TYPE_INT_HEX, 1),  # bold
                make_attr("textColor", TYPE_INT_COLOR_ARGB8, 0xFFF2F4FA),
                make_attr("id", TYPE_REFERENCE, 0x01020014),
                make_attr("background", TYPE_INT_COLOR_ARGB8, 0xFF151828),
                make_attr("paddingLeft", TYPE_DIMENSION, dp(8)),
                make_attr("paddingTop", TYPE_DIMENSION, dp(6)),
                make_attr("paddingRight", TYPE_DIMENSION, dp(8)),
                make_attr("paddingBottom", TYPE_DIMENSION, dp(6)),
                make_attr("layout_width", TYPE_INT_DEC, MATCH_PARENT),
                make_attr("layout_height", TYPE_INT_DEC, WRAP_CONTENT),
                make_attr("layout_marginBottom", TYPE_DIMENSION, dp(5)),
                make_attr(
                    "text",
                    TYPE_STRING,
                    0,
                    "🎯 [1/5] 🔁 DAILY +10 XP · 🧠 INT\n☢️ RNA Reator PWR: Avançar 30 min no modelo MLP",
                ),
                make_attr("maxLines", TYPE_INT_DEC, 3),
            ],
            line=10,
        ),
        end_el("TextView", line=10),
        # 4. Próximas Missões da Fila — id = android.R.id.text2 (0x01020015)
        start_el(
            "TextView",
            [
                make_attr("textSize", TYPE_DIMENSION, sp(10)),
                make_attr("textColor", TYPE_INT_COLOR_ARGB8, 0xFF9BA3C2),
                make_attr("id", TYPE_REFERENCE, 0x01020015),
                make_attr("layout_width", TYPE_INT_DEC, MATCH_PARENT),
                make_attr("layout_height", TYPE_DIMENSION, dp(0)),
                make_attr("layout_marginBottom", TYPE_DIMENSION, dp(6)),
                make_attr(
                    "text",
                    TYPE_STRING,
                    0,
                    "• 🔁 SOMA: Ler artigo de cristais piezoelétricos (+10 XP)\n• 🔁 IFF: Revisar matéria do dia (+10 XP)",
                ),
                make_attr("maxLines", TYPE_INT_DEC, 3),
                make_attr("layout_weight", TYPE_FLOAT, 0x3F800000),  # 1.0f
            ],
            line=11,
        ),
        end_el("TextView", line=11),
        # 5. Barra de Ações Interativas na Tela Inicial (Concluir / Próxima / Abrir App)
        start_el(
            "LinearLayout",
            [
                make_attr("orientation", TYPE_INT_DEC, 0),  # horizontal
                make_attr("layout_width", TYPE_INT_DEC, MATCH_PARENT),
                make_attr("layout_height", TYPE_INT_DEC, WRAP_CONTENT),
            ],
            line=12,
        ),
        start_el(
            "TextView",
            [
                make_attr("textSize", TYPE_DIMENSION, sp(10)),
                make_attr("textStyle", TYPE_INT_HEX, 1),
                make_attr("textColor", TYPE_INT_COLOR_ARGB8, 0xFF00FF9F),
                make_attr("gravity", TYPE_INT_HEX, 0x11),  # center
                make_attr("id", TYPE_REFERENCE, 0x01020019),  # android.R.id.button1
                make_attr("background", TYPE_INT_COLOR_ARGB8, 0xFF102820),
                make_attr("paddingTop", TYPE_DIMENSION, dp(5)),
                make_attr("paddingBottom", TYPE_DIMENSION, dp(5)),
                make_attr("layout_width", TYPE_DIMENSION, dp(0)),
                make_attr("layout_height", TYPE_DIMENSION, dp(30)),
                make_attr("layout_marginRight", TYPE_DIMENSION, dp(4)),
                make_attr("text", TYPE_STRING, 0, "✔ CONCLUIR"),
                make_attr("singleLine", TYPE_INT_BOOLEAN, 0xFFFFFFFF),
                make_attr("layout_weight", TYPE_FLOAT, 0x3F800000),
            ],
            line=13,
        ),
        end_el("TextView", line=13),
        start_el(
            "TextView",
            [
                make_attr("textSize", TYPE_DIMENSION, sp(10)),
                make_attr("textStyle", TYPE_INT_HEX, 1),
                make_attr("textColor", TYPE_INT_COLOR_ARGB8, 0xFF00F0FF),
                make_attr("gravity", TYPE_INT_HEX, 0x11),
                make_attr("id", TYPE_REFERENCE, 0x0102001A),  # android.R.id.button2
                make_attr("background", TYPE_INT_COLOR_ARGB8, 0xFF102030),
                make_attr("paddingTop", TYPE_DIMENSION, dp(5)),
                make_attr("paddingBottom", TYPE_DIMENSION, dp(5)),
                make_attr("layout_width", TYPE_DIMENSION, dp(0)),
                make_attr("layout_height", TYPE_DIMENSION, dp(30)),
                make_attr("layout_marginRight", TYPE_DIMENSION, dp(4)),
                make_attr("text", TYPE_STRING, 0, "⏭ PRÓXIMA"),
                make_attr("singleLine", TYPE_INT_BOOLEAN, 0xFFFFFFFF),
                make_attr("layout_weight", TYPE_FLOAT, 0x3F800000),
            ],
            line=14,
        ),
        end_el("TextView", line=14),
        start_el(
            "TextView",
            [
                make_attr("textSize", TYPE_DIMENSION, sp(10)),
                make_attr("textStyle", TYPE_INT_HEX, 1),
                make_attr("textColor", TYPE_INT_COLOR_ARGB8, 0xFFFCEE0A),
                make_attr("gravity", TYPE_INT_HEX, 0x11),
                make_attr("id", TYPE_REFERENCE, 0x0102001B),  # android.R.id.button3
                make_attr("background", TYPE_INT_COLOR_ARGB8, 0xFF282410),
                make_attr("paddingTop", TYPE_DIMENSION, dp(5)),
                make_attr("paddingBottom", TYPE_DIMENSION, dp(5)),
                make_attr("layout_width", TYPE_DIMENSION, dp(0)),
                make_attr("layout_height", TYPE_DIMENSION, dp(30)),
                make_attr("text", TYPE_STRING, 0, "⚡ ABRIR"),
                make_attr("singleLine", TYPE_INT_BOOLEAN, 0xFFFFFFFF),
                make_attr("layout_weight", TYPE_FLOAT, 0x3F800000),
            ],
            line=15,
        ),
        end_el("TextView", line=15),
        end_el("LinearLayout", line=16),
        end_el("LinearLayout", line=17),
        struct.pack("<HHIIIII", 0x0101, 16, 24, 18, 0xFFFFFFFF, get_str_idx(NS_PREFIX), get_str_idx(NS_URI)),
    ]

    sp_chunk = build_string_pool(strings)
    res_map_chunk = struct.pack("<HHI", 0x0180, 8, 8 + 4 * len(res_ids)) + b"".join(
        struct.pack("<I", rid) for rid in res_ids
    )
    body = sp_chunk + res_map_chunk + b"".join(chunks)
    return struct.pack("<HHI", 0x0003, 8, 8 + len(body)) + body


# ---------------------------------------------------------------------------
# 3. CLASSES SMALI NATIVAS (MainActivity + AndroidBridge + NotificationActionReceiver)
# ---------------------------------------------------------------------------
MAIN_ACTIVITY_SMALI = r""".class public Lcom/cyberdeck/nightcityrpg/MainActivity;
.super Landroid/app/Activity;

.field private webView:Landroid/webkit/WebView;

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method

.method protected onCreate(Landroid/os/Bundle;)V
    .registers 7
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    const/4 v0, 0x1
    invoke-virtual {p0, v0}, Landroid/app/Activity;->requestWindowFeature(I)Z

    # Solicita permissão POST_NOTIFICATIONS no Android 13+ (SDK >= 33)
    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v2, 0x21
    if-lt v1, v2, :cond_perm_done
    new-array v2, v0, [Ljava/lang/String;
    const/4 v3, 0x0
    const-string v4, "android.permission.POST_NOTIFICATIONS"
    aput-object v4, v2, v3
    const/16 v3, 0x65
    invoke-virtual {p0, v2, v3}, Landroid/app/Activity;->requestPermissions([Ljava/lang/String;I)V
    :cond_perm_done

    new-instance v1, Landroid/webkit/WebView;
    invoke-direct {v1, p0}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V
    iput-object v1, p0, Lcom/cyberdeck/nightcityrpg/MainActivity;->webView:Landroid/webkit/WebView;

    const v2, -0xf9f8f5
    invoke-virtual {v1, v2}, Landroid/webkit/WebView;->setBackgroundColor(I)V

    invoke-virtual {v1}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v2

    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setDomStorageEnabled(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setDatabaseEnabled(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setAllowFileAccess(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setAllowContentAccess(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setAllowFileAccessFromFileURLs(Z)V
    invoke-virtual {v2, v0}, Landroid/webkit/WebSettings;->setAllowUniversalAccessFromFileURLs(Z)V

    new-instance v3, Landroid/webkit/WebChromeClient;
    invoke-direct {v3}, Landroid/webkit/WebChromeClient;-><init>()V
    invoke-virtual {v1, v3}, Landroid/webkit/WebView;->setWebChromeClient(Landroid/webkit/WebChromeClient;)V

    new-instance v3, Landroid/webkit/WebViewClient;
    invoke-direct {v3}, Landroid/webkit/WebViewClient;-><init>()V
    invoke-virtual {v1, v3}, Landroid/webkit/WebView;->setWebViewClient(Landroid/webkit/WebViewClient;)V

    new-instance v3, Lcom/cyberdeck/nightcityrpg/AndroidBridge;
    invoke-direct {v3, p0}, Lcom/cyberdeck/nightcityrpg/AndroidBridge;-><init>(Landroid/content/Context;)V
    const-string v4, "AndroidBridge"
    invoke-virtual {v1, v3, v4}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    invoke-virtual {p0, v1}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V

    const-string v3, "file:///android_asset/index.html"
    invoke-virtual {v1, v3}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V

    return-void
.end method

.method protected onResume()V
    .registers 3
    invoke-super {p0}, Landroid/app/Activity;->onResume()V
    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/MainActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :cond_done
    const-string v1, "javascript:if(window.consumeNativeNotificationActions)window.consumeNativeNotificationActions();if(window.syncAndroidSystemNotifications)window.syncAndroidSystemNotifications();"
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
    :cond_done
    return-void
.end method

.method public onRequestPermissionsResult(I[Ljava/lang/String;[I)V
    .registers 6
    invoke-super {p0, p1, p2, p3}, Landroid/app/Activity;->onRequestPermissionsResult(I[Ljava/lang/String;[I)V
    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/MainActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :cond_done
    const-string v1, "javascript:if(window.syncAndroidSystemNotifications)window.syncAndroidSystemNotifications();"
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
    :cond_done
    return-void
.end method

.method public onBackPressed()V
    .registers 3
    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/MainActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :cond_super
    invoke-virtual {v0}, Landroid/webkit/WebView;->canGoBack()Z
    move-result v1
    if-eqz v1, :cond_super
    invoke-virtual {v0}, Landroid/webkit/WebView;->goBack()V
    return-void
    :cond_super
    invoke-super {p0}, Landroid/app/Activity;->onBackPressed()V
    return-void
.end method
"""

ANDROID_BRIDGE_SMALI = r""".class public Lcom/cyberdeck/nightcityrpg/AndroidBridge;
.super Ljava/lang/Object;

.field private context:Landroid/content/Context;

.method public constructor <init>(Landroid/content/Context;)V
    .registers 2
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    return-void
.end method

.method public areNotificationsEnabled()Z
    .registers 4
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "notification"
    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Landroid/app/NotificationManager;

    sget v2, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v0, 0x18
    if-lt v2, v0, :cond_true
    invoke-virtual {v1}, Landroid/app/NotificationManager;->areNotificationsEnabled()Z
    move-result v0
    return v0

    :cond_true
    const/4 v0, 0x1
    return v0
.end method

.method public openNotificationSettings()V
    .registers 5
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    new-instance v1, Landroid/content/Intent;
    const-string v2, "android.settings.APP_NOTIFICATION_SETTINGS"
    invoke-direct {v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V
    const-string v2, "android.provider.extra.APP_PACKAGE"
    const-string v3, "com.cyberdeck.nightcityrpg"
    invoke-virtual {v1, v2, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    const/high16 v2, 0x10000000
    invoke-virtual {v1, v2}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;
    invoke-virtual {v0, v1}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V

    const-string v1, "\ud83d\udcf2 Ative a chave \'Permitir notifica\u00e7\u00f5es\' nesta tela do Samsung!"
    const/4 v2, 0x1
    invoke-static {v0, v1, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v1
    invoke-virtual {v1}, Landroid/widget/Toast;->show()V
    return-void
.end method

.method public showQuestNotification(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;I)V
    .registers 15
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "notification"
    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Landroid/app/NotificationManager;

    const-string v2, "nc_daily_channel_v3"
    sget v3, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v4, 0x1a
    if-lt v3, v4, :cond_legacy

    new-instance v4, Landroid/app/NotificationChannel;
    const-string v5, "Daily Quests // Night City RPG"
    const/4 v6, 0x4
    invoke-direct {v4, v2, v5, v6}, Landroid/app/NotificationChannel;-><init>(Ljava/lang/String;Ljava/lang/CharSequence;I)V
    invoke-virtual {v1, v4}, Landroid/app/NotificationManager;->createNotificationChannel(Landroid/app/NotificationChannel;)V

    new-instance v4, Landroid/app/Notification$Builder;
    invoke-direct {v4, v0, v2}, Landroid/app/Notification$Builder;-><init>(Landroid/content/Context;Ljava/lang/String;)V
    goto :goto_build

    :cond_legacy
    new-instance v4, Landroid/app/Notification$Builder;
    invoke-direct {v4, v0}, Landroid/app/Notification$Builder;-><init>(Landroid/content/Context;)V

    :goto_build
    const/high16 v5, 0x7f010000
    invoke-virtual {v4, v5}, Landroid/app/Notification$Builder;->setSmallIcon(I)Landroid/app/Notification$Builder;

    # Carrega o ícone Cyberpunk colorido também como LargeIcon na notificação Samsung One UI
    invoke-virtual {v0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;
    move-result-object v6
    invoke-static {v6, v5}, Landroid/graphics/BitmapFactory;->decodeResource(Landroid/content/res/Resources;I)Landroid/graphics/Bitmap;
    move-result-object v6
    if-eqz v6, :cond_no_large
    invoke-virtual {v4, v6}, Landroid/app/Notification$Builder;->setLargeIcon(Landroid/graphics/Bitmap;)Landroid/app/Notification$Builder;
    :cond_no_large
    invoke-virtual {v4, p2}, Landroid/app/Notification$Builder;->setContentTitle(Ljava/lang/CharSequence;)Landroid/app/Notification$Builder;
    invoke-virtual {v4, p3}, Landroid/app/Notification$Builder;->setContentText(Ljava/lang/CharSequence;)Landroid/app/Notification$Builder;
    const/4 v5, 0x1
    invoke-virtual {v4, v5}, Landroid/app/Notification$Builder;->setAutoCancel(Z)Landroid/app/Notification$Builder;

    # Estilo expansível BigTextStyle para ler toda a Daily Quest na barra de notificações
    new-instance v5, Landroid/app/Notification$BigTextStyle;
    invoke-direct {v5}, Landroid/app/Notification$BigTextStyle;-><init>()V
    invoke-virtual {v5, p3}, Landroid/app/Notification$BigTextStyle;->bigText(Ljava/lang/CharSequence;)Landroid/app/Notification$BigTextStyle;
    invoke-virtual {v4, v5}, Landroid/app/Notification$Builder;->setStyle(Landroid/app/Notification$Style;)Landroid/app/Notification$Builder;

    # Define flags do PendingIntent (FLAG_UPDATE_CURRENT | FLAG_IMMUTABLE no SDK >= 23)
    const/high16 v5, 0x08000000
    const/16 v6, 0x17
    if-lt v3, v6, :cond_flags_ok
    const/high16 v5, 0x0c000000
    :cond_flags_ok

    # Botão 1 na Notificação do Android: [✔ Concluir (+10 XP)]
    new-instance v6, Landroid/content/Intent;
    const-class v7, Lcom/cyberdeck/nightcityrpg/NotificationActionReceiver;
    invoke-direct {v6, v0, v7}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const-string v8, "com.cyberdeck.nightcityrpg.ACTION_COMPLETE"
    invoke-virtual {v6, v8}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_action"
    const-string v9, "complete"
    invoke-virtual {v6, v8, v9}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_quest_id"
    invoke-virtual {v6, v8, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_notif_id"
    invoke-virtual {v6, v8, p4}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;

    mul-int/lit8 v8, p4, 0x2
    invoke-static {v0, v8, v6, v5}, Landroid/app/PendingIntent;->getBroadcast(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v8
    const/4 v9, 0x0
    const-string v6, "\u2714 Concluir (+10 XP)"
    invoke-virtual {v4, v9, v6, v8}, Landroid/app/Notification$Builder;->addAction(ILjava/lang/CharSequence;Landroid/app/PendingIntent;)Landroid/app/Notification$Builder;

    # Botão 2 na Notificação do Android: [🔕 Silenciar]
    new-instance v6, Landroid/content/Intent;
    invoke-direct {v6, v0, v7}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const-string v8, "com.cyberdeck.nightcityrpg.ACTION_MUTE"
    invoke-virtual {v6, v8}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_action"
    const-string v9, "mute"
    invoke-virtual {v6, v8, v9}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_quest_id"
    invoke-virtual {v6, v8, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    const-string v8, "nc_notif_id"
    invoke-virtual {v6, v8, p4}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;

    mul-int/lit8 v8, p4, 0x2
    add-int/lit8 v8, v8, 0x1
    invoke-static {v0, v8, v6, v5}, Landroid/app/PendingIntent;->getBroadcast(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v8
    const/4 v9, 0x0
    const-string v6, "\ud83d\udd15 Silenciar"
    invoke-virtual {v4, v9, v6, v8}, Landroid/app/Notification$Builder;->addAction(ILjava/lang/CharSequence;Landroid/app/PendingIntent;)Landroid/app/Notification$Builder;

    # Toque no corpo da notificação abre o app
    new-instance v6, Landroid/content/Intent;
    const-class v7, Lcom/cyberdeck/nightcityrpg/MainActivity;
    invoke-direct {v6, v0, v7}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const/high16 v7, 0x24000000
    invoke-virtual {v6, v7}, Landroid/content/Intent;->setFlags(I)Landroid/content/Intent;
    invoke-static {v0, p4, v6, v5}, Landroid/app/PendingIntent;->getActivity(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v6
    invoke-virtual {v4, v6}, Landroid/app/Notification$Builder;->setContentIntent(Landroid/app/PendingIntent;)Landroid/app/Notification$Builder;

    invoke-virtual {v4}, Landroid/app/Notification$Builder;->build()Landroid/app/Notification;
    move-result-object v5
    invoke-virtual {v1, p4, v5}, Landroid/app/NotificationManager;->notify(ILandroid/app/Notification;)V

    return-void
.end method

.method public cancelNotification(I)V
    .registers 4
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "notification"
    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Landroid/app/NotificationManager;
    invoke-virtual {v1, p1}, Landroid/app/NotificationManager;->cancel(I)V
    return-void
.end method

.method public cancelAllNotifications()V
    .registers 3
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "notification"
    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Landroid/app/NotificationManager;
    invoke-virtual {v1}, Landroid/app/NotificationManager;->cancelAll()V
    return-void
.end method

.method public httpRequest(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .registers 12
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    :try_start_http
    new-instance v0, Ljava/net/URL;
    invoke-direct {v0, p1}, Ljava/net/URL;-><init>(Ljava/lang/String;)V
    invoke-virtual {v0}, Ljava/net/URL;->openConnection()Ljava/net/URLConnection;
    move-result-object v0
    check-cast v0, Ljava/net/HttpURLConnection;

    invoke-virtual {v0, p2}, Ljava/net/HttpURLConnection;->setRequestMethod(Ljava/lang/String;)V
    const/16 v1, 0x3a98
    invoke-virtual {v0, v1}, Ljava/net/HttpURLConnection;->setConnectTimeout(I)V
    const/16 v1, 0x4e20
    invoke-virtual {v0, v1}, Ljava/net/HttpURLConnection;->setReadTimeout(I)V

    const-string v1, "Accept"
    const-string v2, "application/json, text/calendar, */*"
    invoke-virtual {v0, v1, v2}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V
    const-string v1, "User-Agent"
    const-string v2, "Mozilla/5.0 NightCityRPG-Android/2.0"
    invoke-virtual {v0, v1, v2}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    if-eqz p3, :cond_no_auth
    invoke-virtual {p3}, Ljava/lang/String;->length()I
    move-result v1
    if-lez v1, :cond_no_auth
    const-string v1, "Authorization"
    invoke-virtual {v0, v1, p3}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V
    :cond_no_auth

    if-eqz p4, :cond_no_body
    invoke-virtual {p4}, Ljava/lang/String;->length()I
    move-result v1
    if-lez v1, :cond_no_body
    const-string v1, "Content-Type"
    const-string v2, "application/json; charset=UTF-8"
    invoke-virtual {v0, v1, v2}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V
    const/4 v1, 0x1
    invoke-virtual {v0, v1}, Ljava/net/HttpURLConnection;->setDoOutput(Z)V
    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->getOutputStream()Ljava/io/OutputStream;
    move-result-object v1
    const-string v2, "UTF-8"
    invoke-virtual {p4, v2}, Ljava/lang/String;->getBytes(Ljava/lang/String;)[B
    move-result-object v2
    invoke-virtual {v1, v2}, Ljava/io/OutputStream;->write([B)V
    invoke-virtual {v1}, Ljava/io/OutputStream;->close()V
    :cond_no_body

    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->getResponseCode()I
    move-result v1
    const/16 v2, 0x190
    if-ge v1, v2, :cond_err_stream
    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->getInputStream()Ljava/io/InputStream;
    move-result-object v1
    goto :cond_got_stream

    :cond_err_stream
    invoke-virtual {v0}, Ljava/net/HttpURLConnection;->getErrorStream()Ljava/io/InputStream;
    move-result-object v1

    :cond_got_stream
    if-eqz v1, :cond_empty
    new-instance v2, Ljava/io/InputStreamReader;
    const-string v3, "UTF-8"
    invoke-direct {v2, v1, v3}, Ljava/io/InputStreamReader;-><init>(Ljava/io/InputStream;Ljava/lang/String;)V
    new-instance v3, Ljava/io/BufferedReader;
    invoke-direct {v3, v2}, Ljava/io/BufferedReader;-><init>(Ljava/io/Reader;)V
    new-instance v4, Ljava/lang/StringBuilder;
    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    :loop_read
    invoke-virtual {v3}, Ljava/io/BufferedReader;->readLine()Ljava/lang/String;
    move-result-object v5
    if-eqz v5, :cond_read_done
    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v6, "\n"
    invoke-virtual {v4, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    goto :loop_read

    :cond_read_done
    invoke-virtual {v3}, Ljava/io/BufferedReader;->close()V
    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :cond_empty
    const-string v0, ""
    return-object v0
    :try_end_http
    .catch Ljava/lang/Exception; {:try_start_http .. :try_end_http} :catch_http

    :catch_http
    const-string v0, ""
    return-object v0
.end method

.method public consumeNativeActions()Ljava/lang/String;
    .registers 5
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "nc_rpg_prefs"
    const/4 v2, 0x0
    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v1

    const-string v2, "native_action_queue"
    const-string v3, ""
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0

    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v1
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v1}, Landroid/content/SharedPreferences$Editor;->commit()Z

    return-object v0
.end method

.method public syncWidgetData(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V
    .locals 4
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    const-string v1, "nc_rpg_prefs"
    const/4 v2, 0x0
    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v1

    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v1

    const-string v2, "widget_header_title"
    invoke-interface {v1, v2, p1}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "widget_header_sub"
    invoke-interface {v1, v2, p2}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "widget_quests_lines"
    invoke-interface {v1, v2, p3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    # O app já contabilizou o XP ganho pelo Widget -> zera o "(+XP)" pendente
    const-string v2, "widget_bonus_xp"
    const/4 v3, 0x0
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;

    invoke-interface {v1}, Landroid/content/SharedPreferences$Editor;->commit()Z

    invoke-static {v0}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateAllWidgets(Landroid/content/Context;)V
    return-void
.end method

.method public requestPinWidget()V
    .registers 6
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    iget-object v0, p0, Lcom/cyberdeck/nightcityrpg/AndroidBridge;->context:Landroid/content/Context;
    invoke-static {v0}, Landroid/appwidget/AppWidgetManager;->getInstance(Landroid/content/Context;)Landroid/appwidget/AppWidgetManager;
    move-result-object v1

    new-instance v2, Landroid/content/ComponentName;
    const-class v3, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;
    invoke-direct {v2, v0, v3}, Landroid/content/ComponentName;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    sget v3, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v4, 0x1a
    if-lt v3, v4, :cond_manual_toast

    invoke-virtual {v1}, Landroid/appwidget/AppWidgetManager;->isRequestPinAppWidgetSupported()Z
    move-result v3
    if-eqz v3, :cond_manual_toast

    const/4 v3, 0x0
    invoke-virtual {v1, v2, v3, v3}, Landroid/appwidget/AppWidgetManager;->requestPinAppWidget(Landroid/content/ComponentName;Landroid/os/Bundle;Landroid/app/PendingIntent;)Z
    move-result v3
    if-eqz v3, :cond_manual_toast

    invoke-static {v0}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateAllWidgets(Landroid/content/Context;)V
    return-void

    :cond_manual_toast
    const-string v1, "\ud83d\udcf1 Segure o dedo na Tela Inicial -> Widgets -> Night City RPG!"
    const/4 v2, 0x1
    invoke-static {v0, v1, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v1
    invoke-virtual {v1}, Landroid/widget/Toast;->show()V
    return-void
.end method
"""

NOTIFICATION_RECEIVER_SMALI = r""".class public Lcom/cyberdeck/nightcityrpg/NotificationActionReceiver;
.super Landroid/content/BroadcastReceiver;

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/content/BroadcastReceiver;-><init>()V
    return-void
.end method

.method public onReceive(Landroid/content/Context;Landroid/content/Intent;)V
    .registers 10

    if-eqz p2, :cond_done

    const-string v0, "nc_action"
    invoke-virtual {p2, v0}, Landroid/content/Intent;->getStringExtra(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :cond_done

    const-string v1, "nc_quest_id"
    invoke-virtual {p2, v1}, Landroid/content/Intent;->getStringExtra(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v1
    if-eqz v1, :cond_done

    const-string v2, "nc_notif_id"
    const/4 v3, 0x0
    invoke-virtual {p2, v2, v3}, Landroid/content/Intent;->getIntExtra(Ljava/lang/String;I)I
    move-result v2

    # Remove a notificação da barra do Android imediatamente
    const-string v4, "notification"
    invoke-virtual {p1, v4}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v4
    check-cast v4, Landroid/app/NotificationManager;
    invoke-virtual {v4, v2}, Landroid/app/NotificationManager;->cancel(I)V

    # Salva a ação (complete:questId ou mute:questId) em SharedPreferences para o app contabilizar o XP
    const-string v4, "nc_rpg_prefs"
    invoke-virtual {p1, v4, v3}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v4

    const-string v5, "native_action_queue"
    const-string v6, ""
    invoke-interface {v4, v5, v6}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v6

    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v2, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v6, ":"
    invoke-virtual {v2, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v6, "\n"
    invoke-virtual {v2, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v2

    invoke-interface {v4}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v4
    invoke-interface {v4, v5, v2}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v4}, Landroid/content/SharedPreferences$Editor;->commit()Z

    # Exibe Toast nativo do Android confirmando a ação feita pela barra de notificações
    const-string v4, "complete"
    invoke-virtual {v4, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v4
    if-eqz v4, :cond_mute_toast

    const-string v4, "\u26a1 +10 XP \u00b7 Daily Quest conclu\u00edda pela barra!"
    invoke-static {p1, v4, v3}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v4
    invoke-virtual {v4}, Landroid/widget/Toast;->show()V
    goto :cond_done

    :cond_mute_toast
    const-string v4, "\ud83d\udd15 Notifica\u00e7\u00e3o desta Daily Quest silenciada!"
    invoke-static {p1, v4, v3}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v4
    invoke-virtual {v4}, Landroid/widget/Toast;->show()V

    :cond_done
    return-void
.end method
"""

QUEST_WIDGET_PROVIDER_SMALI = r""".class public Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;
.super Landroid/appwidget/AppWidgetProvider;

# =====================================================================
# Widget "⚡ Night City Quests" (v2.0.87)
# IMPORTANTE: usa .locals (nunca .registers) para não sobrescrever p0/p1/p2.
# Formato de cada linha em widget_quests_lines:
#   questId \t badge \t título \t xp
# =====================================================================

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Landroid/appwidget/AppWidgetProvider;-><init>()V
    return-void
.end method

.method public onUpdate(Landroid/content/Context;Landroid/appwidget/AppWidgetManager;[I)V
    .locals 0
    invoke-static {p1, p2, p3}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateWidgets(Landroid/content/Context;Landroid/appwidget/AppWidgetManager;[I)V
    return-void
.end method

.method public static updateAllWidgets(Landroid/content/Context;)V
    .locals 3
    :try_start_all
    invoke-static {p0}, Landroid/appwidget/AppWidgetManager;->getInstance(Landroid/content/Context;)Landroid/appwidget/AppWidgetManager;
    move-result-object v0
    new-instance v1, Landroid/content/ComponentName;
    const-class v2, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;
    invoke-direct {v1, p0, v2}, Landroid/content/ComponentName;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    invoke-virtual {v0, v1}, Landroid/appwidget/AppWidgetManager;->getAppWidgetIds(Landroid/content/ComponentName;)[I
    move-result-object v2
    invoke-static {p0, v0, v2}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateWidgets(Landroid/content/Context;Landroid/appwidget/AppWidgetManager;[I)V
    :try_end_all
    .catch Ljava/lang/Exception; {:try_start_all .. :try_end_all} :catch_all
    return-void
    :catch_all
    return-void
.end method

# Retorna o campo [idx] de uma linha separada por TAB (ou "" se não existir)
.method private static field(Ljava/lang/String;I)Ljava/lang/String;
    .locals 2
    const-string v0, "\t"
    invoke-virtual {p0, v0}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v0
    array-length v1, v0
    if-ge p1, v1, :cond_has
    const-string v0, ""
    return-object v0
    :cond_has
    aget-object v0, v0, p1
    return-object v0
.end method

# PendingIntent de broadcast explícito para o próprio Widget
.method private static broadcastPI(Landroid/content/Context;Ljava/lang/String;II)Landroid/app/PendingIntent;
    .locals 2
    new-instance v0, Landroid/content/Intent;
    const-class v1, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;
    invoke-direct {v0, p0, v1}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    invoke-virtual {v0, p1}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;
    invoke-static {p0, p2, v0, p3}, Landroid/app/PendingIntent;->getBroadcast(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v0
    return-object v0
.end method

.method public onReceive(Landroid/content/Context;Landroid/content/Intent;)V
    .locals 13

    invoke-super {p0, p1, p2}, Landroid/appwidget/AppWidgetProvider;->onReceive(Landroid/content/Context;Landroid/content/Intent;)V
    if-eqz p2, :cond_done

    :try_start_recv
    invoke-virtual {p2}, Landroid/content/Intent;->getAction()Ljava/lang/String;
    move-result-object v0
    if-eqz v0, :cond_done

    const-string v1, "nc_rpg_prefs"
    const/4 v2, 0x0
    invoke-virtual {p1, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v1

    # ---------- [⏭ PRÓXIMA] ----------
    const-string v3, "com.cyberdeck.nightcityrpg.WIDGET_NEXT"
    invoke-virtual {v3, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-eqz v3, :cond_check_complete

    const-string v3, "widget_focus_idx"
    invoke-interface {v1, v3, v2}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v4
    add-int/lit8 v4, v4, 0x1
    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v5
    invoke-interface {v5, v3, v4}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v5}, Landroid/content/SharedPreferences$Editor;->commit()Z
    invoke-static {p1}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateAllWidgets(Landroid/content/Context;)V
    goto :cond_done

    # ---------- [✔ CONCLUIR] ----------
    :cond_check_complete
    const-string v3, "com.cyberdeck.nightcityrpg.WIDGET_COMPLETE"
    invoke-virtual {v3, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-eqz v3, :cond_check_refresh

    const-string v3, "widget_current_quest_line"
    const-string v4, ""
    invoke-interface {v1, v3, v4}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v5
    if-eqz v5, :cond_refresh_only
    invoke-virtual {v5}, Ljava/lang/String;->length()I
    move-result v6
    if-eqz v6, :cond_refresh_only

    # id (campo 0) e xp (campo 3)
    invoke-static {v5, v2}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->field(Ljava/lang/String;I)Ljava/lang/String;
    move-result-object v6
    const/4 v7, 0x3
    invoke-static {v5, v7}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->field(Ljava/lang/String;I)Ljava/lang/String;
    move-result-object v7

    # Enfileira "complete:<id>\n" para o app somar XP / atributo / histórico
    const-string v8, "native_action_queue"
    invoke-interface {v1, v8, v4}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v9
    new-instance v3, Ljava/lang/StringBuilder;
    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v3, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v0, "complete:"
    invoke-virtual {v3, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v0, "\n"
    invoke-virtual {v3, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v9

    # Remove a linha concluída da fila do Widget: ("\n"+lista+"\n").replace("\n"+linha+"\n", "\n").trim()
    const-string v0, "widget_quests_lines"
    invoke-interface {v1, v0, v4}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v6
    new-instance v3, Ljava/lang/StringBuilder;
    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V
    const-string v10, "\n"
    invoke-virtual {v3, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v6
    new-instance v3, Ljava/lang/StringBuilder;
    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v3, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v5
    invoke-virtual {v6, v5, v10}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;
    move-result-object v6
    invoke-virtual {v6}, Ljava/lang/String;->trim()Ljava/lang/String;
    move-result-object v6

    # XP da missão (int) — 0 se não for número
    const/4 v11, 0x0
    :try_start_parse
    invoke-static {v7}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I
    move-result v11
    :try_end_parse
    .catch Ljava/lang/Exception; {:try_start_parse .. :try_end_parse} :catch_parse
    goto :cond_after_parse
    :catch_parse
    const/4 v11, 0x0
    :cond_after_parse

    # XP ganho pelo Widget e ainda não processado pelo app (mostrado no cabeçalho)
    const-string v3, "widget_bonus_xp"
    invoke-interface {v1, v3, v2}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v12
    add-int/2addr v12, v11

    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v4
    invoke-interface {v4, v8, v9}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v4, v0, v6}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v4, v3, v12}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v4}, Landroid/content/SharedPreferences$Editor;->commit()Z

    new-instance v3, Ljava/lang/StringBuilder;
    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V
    const-string v4, "\u26a1 +"
    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3, v11}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v4, " XP \u00b7 Miss\u00e3o conclu\u00edda!"
    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v3
    invoke-static {p1, v3, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v3
    invoke-virtual {v3}, Landroid/widget/Toast;->show()V

    :cond_refresh_only
    invoke-static {p1}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateAllWidgets(Landroid/content/Context;)V
    goto :cond_done

    # ---------- [↻ ATUALIZAR] ----------
    :cond_check_refresh
    const-string v3, "com.cyberdeck.nightcityrpg.WIDGET_REFRESH"
    invoke-virtual {v3, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-eqz v3, :cond_done
    invoke-static {p1}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->updateAllWidgets(Landroid/content/Context;)V
    :try_end_recv
    .catch Ljava/lang/Exception; {:try_start_recv .. :try_end_recv} :catch_recv

    :cond_done
    return-void

    :catch_recv
    return-void
.end method

.method public static updateWidgets(Landroid/content/Context;Landroid/appwidget/AppWidgetManager;[I)V
    .locals 14

    if-eqz p2, :cond_ret
    array-length v0, p2
    if-eqz v0, :cond_ret

    :try_start_upd
    const-string v0, "nc_rpg_prefs"
    const/4 v1, 0x0
    invoke-virtual {p0, v0, v1}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v0

    # ----- Cabeçalho: Nível/XP (+ XP pendente ganho pelo Widget) -----
    const-string v2, "widget_header_title"
    const-string v3, "\u26a1 NIGHT CITY RPG"
    invoke-interface {v0, v2, v3}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v2

    const-string v3, "widget_bonus_xp"
    invoke-interface {v0, v3, v1}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v3
    if-lez v3, :cond_no_bonus
    new-instance v4, Ljava/lang/StringBuilder;
    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v4, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v5, "  (+"
    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v4, v3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v5, ")"
    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v2
    :cond_no_bonus

    const-string v3, "widget_header_sub"
    const-string v4, "Abra o app uma vez para sincronizar"
    invoke-interface {v0, v3, v4}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v3

    # ----- Fila de missões -----
    const-string v4, "widget_quests_lines"
    const-string v5, ""
    invoke-interface {v0, v4, v5}, Landroid/content/SharedPreferences;->getString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v4
    if-eqz v4, :cond_no_quests
    invoke-virtual {v4}, Ljava/lang/String;->trim()Ljava/lang/String;
    move-result-object v4

    const-string v5, "widget_focus_idx"
    invoke-interface {v0, v5, v1}, Landroid/content/SharedPreferences;->getInt(Ljava/lang/String;I)I
    move-result v5

    invoke-virtual {v4}, Ljava/lang/String;->length()I
    move-result v6
    if-eqz v6, :cond_no_quests

    const-string v6, "\n"
    invoke-virtual {v4, v6}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v6
    array-length v7, v6
    if-eqz v7, :cond_no_quests

    rem-int/2addr v5, v7
    if-gez v5, :cond_idx_ok
    const/4 v5, 0x0
    :cond_idx_ok

    aget-object v8, v6, v5

    # Guarda a missão em foco (para o botão CONCLUIR) e normaliza o índice
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v9
    const-string v10, "widget_current_quest_line"
    invoke-interface {v9, v10, v8}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    const-string v10, "widget_focus_idx"
    invoke-interface {v9, v10, v5}, Landroid/content/SharedPreferences$Editor;->putInt(Ljava/lang/String;I)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v9}, Landroid/content/SharedPreferences$Editor;->commit()Z

    const/4 v9, 0x1
    invoke-static {v8, v9}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->field(Ljava/lang/String;I)Ljava/lang/String;
    move-result-object v9
    const/4 v10, 0x2
    invoke-static {v8, v10}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->field(Ljava/lang/String;I)Ljava/lang/String;
    move-result-object v10

    # Destaque: "🎯 1/5 · 🔁 DAILY +10 XP · 🧠 INT\nTítulo"
    add-int/lit8 v11, v5, 0x1
    new-instance v12, Ljava/lang/StringBuilder;
    invoke-direct {v12}, Ljava/lang/StringBuilder;-><init>()V
    const-string v13, "\ud83c\udfaf "
    invoke-virtual {v12, v13}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v12, v11}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v13, "/"
    invoke-virtual {v12, v13}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v12, v7}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v13, "  \u00b7  "
    invoke-virtual {v12, v13}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v12, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v13, "\n"
    invoke-virtual {v12, v13}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v12, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v12}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v4

    # Próximas na fila (até 2)
    const/4 v11, 0x1
    if-gt v7, v11, :cond_has_next
    const-string v5, "\u2728 \u00daltima miss\u00e3o da fila!"
    goto :cond_render

    :cond_has_next
    const/4 v9, 0x2
    new-instance v12, Ljava/lang/StringBuilder;
    invoke-direct {v12}, Ljava/lang/StringBuilder;-><init>()V
    add-int/lit8 v11, v5, 0x1
    rem-int/2addr v11, v7
    aget-object v13, v6, v11
    invoke-static {v13, v9}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->field(Ljava/lang/String;I)Ljava/lang/String;
    move-result-object v13
    const-string v10, "\u25b8 "
    invoke-virtual {v12, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v12, v13}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const/4 v11, 0x2
    if-le v7, v11, :cond_next_done
    add-int/lit8 v11, v5, 0x2
    rem-int/2addr v11, v7
    aget-object v13, v6, v11
    invoke-static {v13, v9}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->field(Ljava/lang/String;I)Ljava/lang/String;
    move-result-object v13
    const-string v10, "\n\u25b8 "
    invoke-virtual {v12, v10}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v12, v13}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    :cond_next_done
    invoke-virtual {v12}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v5
    goto :cond_render

    :cond_no_quests
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v4
    const-string v5, "widget_current_quest_line"
    const-string v6, ""
    invoke-interface {v4, v5, v6}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;
    invoke-interface {v4}, Landroid/content/SharedPreferences$Editor;->commit()Z
    const-string v4, "\u2705 Fila limpa!\nNenhuma miss\u00e3o pendente agora."
    const-string v5, "Toque em \u26a1 ABRIR para criar novas Quests."

    # ----- Monta o RemoteViews -----
    :cond_render
    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;
    move-result-object v6
    const/high16 v7, 0x7f020000
    new-instance v8, Landroid/widget/RemoteViews;
    invoke-direct {v8, v6, v7}, Landroid/widget/RemoteViews;-><init>(Ljava/lang/String;I)V

    const v6, 0x01020016
    invoke-virtual {v8, v6, v2}, Landroid/widget/RemoteViews;->setTextViewText(ILjava/lang/CharSequence;)V
    const v6, 0x01020010
    invoke-virtual {v8, v6, v3}, Landroid/widget/RemoteViews;->setTextViewText(ILjava/lang/CharSequence;)V
    const v6, 0x01020014
    invoke-virtual {v8, v6, v4}, Landroid/widget/RemoteViews;->setTextViewText(ILjava/lang/CharSequence;)V
    const v6, 0x01020015
    invoke-virtual {v8, v6, v5}, Landroid/widget/RemoteViews;->setTextViewText(ILjava/lang/CharSequence;)V

    # Flags: FLAG_UPDATE_CURRENT | FLAG_IMMUTABLE (SDK >= 23)
    const/high16 v9, 0x08000000
    sget v10, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v11, 0x17
    if-lt v10, v11, :cond_flags_ok
    const/high16 v9, 0x0c000000
    :cond_flags_ok

    # [✔ CONCLUIR] -> android.R.id.button1
    const-string v10, "com.cyberdeck.nightcityrpg.WIDGET_COMPLETE"
    const/16 v11, 0x1b59
    invoke-static {p0, v10, v11, v9}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->broadcastPI(Landroid/content/Context;Ljava/lang/String;II)Landroid/app/PendingIntent;
    move-result-object v10
    const v11, 0x01020019
    invoke-virtual {v8, v11, v10}, Landroid/widget/RemoteViews;->setOnClickPendingIntent(ILandroid/app/PendingIntent;)V

    # [⏭ PRÓXIMA] -> android.R.id.button2
    const-string v10, "com.cyberdeck.nightcityrpg.WIDGET_NEXT"
    const/16 v11, 0x1b5a
    invoke-static {p0, v10, v11, v9}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->broadcastPI(Landroid/content/Context;Ljava/lang/String;II)Landroid/app/PendingIntent;
    move-result-object v10
    const v11, 0x0102001a
    invoke-virtual {v8, v11, v10}, Landroid/widget/RemoteViews;->setOnClickPendingIntent(ILandroid/app/PendingIntent;)V

    # [↻] Toque no ícone -> atualiza o Widget
    const-string v10, "com.cyberdeck.nightcityrpg.WIDGET_REFRESH"
    const/16 v11, 0x1b5c
    invoke-static {p0, v10, v11, v9}, Lcom/cyberdeck/nightcityrpg/QuestWidgetProvider;->broadcastPI(Landroid/content/Context;Ljava/lang/String;II)Landroid/app/PendingIntent;
    move-result-object v10
    const v11, 0x01020006
    invoke-virtual {v8, v11, v10}, Landroid/widget/RemoteViews;->setOnClickPendingIntent(ILandroid/app/PendingIntent;)V

    # [⚡ ABRIR] (button3) e toque na missão em destaque -> abre o app
    new-instance v10, Landroid/content/Intent;
    const-class v11, Lcom/cyberdeck/nightcityrpg/MainActivity;
    invoke-direct {v10, p0, v11}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const/high16 v11, 0x34000000
    invoke-virtual {v10, v11}, Landroid/content/Intent;->setFlags(I)Landroid/content/Intent;
    const/16 v11, 0x1b5b
    invoke-static {p0, v11, v10, v9}, Landroid/app/PendingIntent;->getActivity(Landroid/content/Context;ILandroid/content/Intent;I)Landroid/app/PendingIntent;
    move-result-object v10
    const v11, 0x0102001b
    invoke-virtual {v8, v11, v10}, Landroid/widget/RemoteViews;->setOnClickPendingIntent(ILandroid/app/PendingIntent;)V
    const v11, 0x01020014
    invoke-virtual {v8, v11, v10}, Landroid/widget/RemoteViews;->setOnClickPendingIntent(ILandroid/app/PendingIntent;)V

    invoke-virtual {p1, p2, v8}, Landroid/appwidget/AppWidgetManager;->updateAppWidget([ILandroid/widget/RemoteViews;)V
    :try_end_upd
    .catch Ljava/lang/Exception; {:try_start_upd .. :try_end_upd} :catch_upd

    :cond_ret
    return-void

    :catch_upd
    return-void
.end method
"""


def main():
    print("=" * 70)
    print(" 🔨 COMPILANDO APK STANDALONE: NIGHT CITY RPG MOBILE (v2.0.87)")
    print("=" * 70)

    # 0. Gera o ícone Cyberpunk 2077 personalizado em PNG (256x256)
    icon_png_bytes = generate_cyberpunk_icon_png(256)
    (WWW_DIR / "icon.png").write_bytes(icon_png_bytes)
    print(f" ✅ Ícone Cyberpunk 2077 personalizado gerado ({len(icon_png_bytes)} bytes)")

    # 1. Obtém o estado completo atual do cofre Obsidian + SUAP + Classroom
    sys.path.insert(0, str(BASE_DIR))
    import server as nc_server

    state = nc_server.scan_vault_and_compute_state()
    state_json = json.dumps(state, ensure_ascii=False)
    print(f" ✅ Banco de dados exportado: Level {state['player']['level']} ({state['player']['totalXP']} XP) | "
          f"{len(state['dailyQuests'])} Dailies | {len(state['quests'])} Quests | "
          f"{len(state['academic'].get('historicoItens', []))} itens SUAP")

    # 2. Prepara o index.html standalone com o banco de dados embutido (apenas dentro do APK)
    src_html = (WWW_DIR / "index.html").read_text(encoding="utf-8")
    target_tag = '<script id="standalone-initial-data">window.STANDALONE_INITIAL_STATE = null;</script>'
    injected_tag = f'<script id="standalone-initial-data">window.STANDALONE_INITIAL_STATE = {state_json};</script>'
    if target_tag in src_html:
        standalone_html = src_html.replace(target_tag, injected_tag, 1)
    else:
        standalone_html = src_html.replace("<script>", injected_tag + "\n  <script>", 1)

    # 3. Compila classes Smali -> classes.dex
    pkg_dir = SMALI_DIR / "com" / "cyberdeck" / "nightcityrpg"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "MainActivity.smali").write_text(MAIN_ACTIVITY_SMALI, encoding="utf-8")
    (pkg_dir / "AndroidBridge.smali").write_text(ANDROID_BRIDGE_SMALI, encoding="utf-8")
    (pkg_dir / "NotificationActionReceiver.smali").write_text(NOTIFICATION_RECEIVER_SMALI, encoding="utf-8")
    (pkg_dir / "QuestWidgetProvider.smali").write_text(QUEST_WIDGET_PROVIDER_SMALI, encoding="utf-8")

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    dex_path = DIST_DIR / "classes.dex"
    if dex_path.exists():
        dex_path.unlink()

    subprocess.run(
        [JAVA_EXE, "-jar", str(SMALI_JAR), "assemble", str(SMALI_DIR), "-o", str(dex_path)],
        check=True,
    )
    print(f" ✅ classes.dex compilado com sucesso ({dex_path.stat().st_size} bytes)")

    # 4. Gera AndroidManifest.xml binário (AXML), Widget XMLs e resources.arsc
    manifest_bytes = build_binary_android_manifest()
    widget_layout_bytes = build_binary_widget_layout_xml()
    widget_info_bytes = build_binary_widget_info_xml()
    arsc_bytes = build_resources_arsc()
    print(
        f" ✅ AndroidManifest.xml ({len(manifest_bytes)} B) + Widget XMLs ({len(widget_layout_bytes) + len(widget_info_bytes)} B) "
        f"+ resources.arsc ({len(arsc_bytes)} B) gerados"
    )

    # 5. Empacota o APK não assinado (resources.arsc e icon.png sem compressão p/ alinhamento 4-bytes ideal)
    unsigned_apk = DIST_DIR / "NightCityRPG-unsigned.apk"
    if unsigned_apk.exists():
        unsigned_apk.unlink()

    with zipfile.ZipFile(unsigned_apk, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("AndroidManifest.xml", manifest_bytes, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("resources.arsc", arsc_bytes, compress_type=zipfile.ZIP_STORED)
        zf.writestr("res/drawable/icon.png", icon_png_bytes, compress_type=zipfile.ZIP_STORED)
        zf.writestr("res/layout/quest_widget.xml", widget_layout_bytes, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("res/xml/quest_widget_info.xml", widget_info_bytes, compress_type=zipfile.ZIP_DEFLATED)
        zf.write(dex_path, "classes.dex", compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("assets/index.html", standalone_html.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)
        if (WWW_DIR / "icon.svg").exists():
            zf.write(WWW_DIR / "icon.svg", "assets/icon.svg", compress_type=zipfile.ZIP_DEFLATED)

    print(f" ✅ APK base montado ({unsigned_apk.stat().st_size // 1024} KB)")

    # 6. Assina (v1 + v2 + v3) e alinha (zipalign) com uber-apk-signer
    subprocess.run(
        [
            JAVA_EXE,
            "-jar",
            str(SIGNER_JAR),
            "--apks",
            str(unsigned_apk),
            "--out",
            str(DIST_DIR),
        ],
        check=True,
    )

    signed_candidate = DIST_DIR / "NightCityRPG-aligned-debugSigned.apk"
    final_apk = DIST_DIR / "NightCityRPG-Standalone.apk"
    if signed_candidate.exists():
        if final_apk.exists():
            final_apk.unlink()
        signed_candidate.rename(final_apk)

    if final_apk.exists():
        shutil.copy2(final_apk, WWW_DIR / "NightCityRPG-Standalone.apk")

    if unsigned_apk.exists():
        unsigned_apk.unlink()
    if dex_path.exists():
        dex_path.unlink()

    print("=" * 70)
    print(f" 🚀 APK STANDALONE PRONTO: {final_apk}")
    print(f" 📦 Tamanho Final: {final_apk.stat().st_size / 1024:.1f} KB")
    print("=" * 70)


if __name__ == "__main__":
    main()
