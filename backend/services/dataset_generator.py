"""Synthetic trademark dataset generator.

Generates 1000+ demonstration trademark records across multiple
Nice classes and jurisdictions. All records are clearly identified
as synthetic demonstration data and must NOT be represented as
verified official registry results.
"""

import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timezone

from backend.agents.normalizer import normalizer
from backend.database.engine import SessionLocal, init_db
from backend.database.models import Trademark, TrademarkGoodsService, NiceClass

# ─── Seed data ────────────────────────────────────────────────────────────────

BRAND_ROOTS = [
    # Benchmark roots
    "Quick", "Color",
    # Beauty/Cosmetics (Class 3)
    "Nykaa", "Lakme", "GlowUp", "BeautyPlus", "SkinGlow", "FreshFace",
    "PureBeauty", "GlamourBox", "RadiantSkin", "VelvetTouch", "BloomCosmetics",
    "NaturaCare", "LuxeSkin", "CrystalGlow", "PetalSoft", "AuraBeauty",
    "ZenSkin", "DivaGlow", "EcoBeauty", "SilkShine", "RoseGold",
    # Technology (Class 9)
    "TechVista", "DigiPulse", "NovaTech", "CyberEdge", "QuantumBit",
    "PixelWave", "DataStream", "CloudNine", "SmartLink", "ByteForce",
    "LogicPro", "NeuralNet", "SynthWave", "CodeCraft", "AppForge",
    "ChipZone", "VoltEdge", "MeshNet", "GridPower", "PulseAI",
    # Food/Beverages (Classes 29-32)
    "FreshBite", "NutriPure", "GoldenHarvest", "SpiceLand", "TastyTreats",
    "OrganicRoots", "NaturalFarm", "GreenLeaf", "PureJuice", "FruitVille",
    "MilkMagic", "GrainWorks", "SweetNectar", "CrunchTime", "VitalBites",
    "ZestyFoods", "EarthBowl", "FarmFresh", "HealthyBrew", "AquaPure",
    # Clothing (Class 25)
    "FashionVista", "StyleCraft", "UrbanThreads", "ChicWear", "TrendSetters",
    "EleganceWear", "ModernFit", "ClassicStyle", "VibeWear", "CoolTrend",
    "DenimWorld", "SilkRoute", "CottonBliss", "WoolMark", "ThreadWork",
    "FabricArts", "StitchPerfect", "VogueStyle", "StreetWear", "NobleDress",
    # Pharma (Class 5)
    "MediCure", "HealthFirst", "VitaPlus", "PharmaCare", "BioHeal",
    "WellnessRx", "CureLab", "GenesisMed", "NovaPharma", "PureHealth",
    "LifeGuard", "HealFast", "MediTrust", "BioVita", "CarePlus",
    "NutriMed", "PillBox", "HealthShield", "MedEase", "VitalCure",
    # Services (Classes 35, 42)
    "BizPro", "MarketEdge", "ConsultPro", "TechServe", "DataWorks",
    "CloudServe", "WebCraft", "DesignHub", "BrandBuilder", "DigitalEdge",
    "StartupHub", "VenturePoint", "GrowthLab", "InnovateTech", "ScaleUp",
    "CodeBase", "DevForge", "CyberGuard", "NetSecure", "DataVault",
]

JURISDICTIONS = ["IN", "US", "GB", "EU", "JP", "AU", "CA", "SG"]

GOODS_BY_CLASS: dict[int, list[str]] = {
    3: [
        "Cosmetics and skincare products",
        "Beauty and cosmetic products",
        "Hair care preparations",
        "Perfumery and fragrances",
        "Soaps and cleaning preparations",
        "Skin moisturizers and lotions",
        "Makeup and cosmetic preparations",
        "Essential oils for personal use",
        "Nail care products",
        "Lip care preparations",
    ],
    5: [
        "Pharmaceutical preparations",
        "Dietary supplements",
        "Medical nutrition products",
        "Vitamin supplements",
        "Herbal remedies",
        "First aid supplies",
        "Antiseptic preparations",
        "Pain relief medications",
        "Cough and cold remedies",
        "Dermatological preparations",
    ],
    9: [
        "Computer software and applications",
        "Electronic devices and accessories",
        "Mobile phone accessories",
        "Data processing equipment",
        "Smart home devices",
        "Wearable technology",
        "Audio and video equipment",
        "Computer peripherals",
        "Scientific instruments",
        "Telecommunications equipment",
    ],
    25: [
        "Clothing and apparel",
        "Footwear",
        "Headwear and hats",
        "Sports clothing",
        "Casual wear",
        "Formal clothing",
        "Children's clothing",
        "Outerwear and jackets",
        "Undergarments",
        "Fashion accessories",
    ],
    29: [
        "Processed meats and poultry",
        "Dairy products",
        "Preserved fruits and vegetables",
        "Edible oils and fats",
        "Frozen foods",
        "Canned foods",
        "Dried fruits and nuts",
        "Pickles and chutneys",
        "Tofu and soy products",
        "Jams and preserves",
    ],
    30: [
        "Rice and grains",
        "Flour and cereals",
        "Bread and bakery products",
        "Spices and condiments",
        "Tea and coffee",
        "Chocolate and confectionery",
        "Pasta and noodles",
        "Sauces and seasonings",
        "Snack foods",
        "Honey and sugar products",
    ],
    32: [
        "Non-alcoholic beverages",
        "Fruit juices and drinks",
        "Mineral and aerated waters",
        "Energy drinks",
        "Sports drinks",
        "Flavored water",
        "Smoothies and shakes",
        "Soft drinks",
        "Herbal drinks",
        "Lemonade and iced tea",
    ],
    35: [
        "Advertising and marketing services",
        "Business management consulting",
        "Retail services",
        "Online marketplace services",
        "Market research",
        "Public relations services",
        "Import-export agency services",
        "Office functions",
        "Franchise management",
        "Sales promotion services",
    ],
    42: [
        "Software development services",
        "IT consulting",
        "Cloud computing services",
        "Web design and hosting",
        "Data analytics services",
        "Cybersecurity services",
        "Mobile app development",
        "Platform as a service",
        "Scientific research",
        "Quality assurance testing",
    ],
}

NICE_CLASS_DATA = {
    1: ("Chemicals", "Chemical products for use in industry, science and photography"),
    2: ("Paints", "Paints, varnishes, lacquers"),
    3: ("Cosmetics", "Non-medicated cosmetics and toiletry preparations"),
    4: ("Lubricants", "Industrial oils and greases, lubricants"),
    5: ("Pharmaceuticals", "Pharmaceutical, medical and veterinary preparations"),
    6: ("Metals", "Common metals and their alloys"),
    7: ("Machines", "Machines, machine tools, power-operated tools"),
    8: ("Hand tools", "Hand tools and implements, hand-operated"),
    9: ("Electronics", "Scientific, research, navigation, surveying and electrical apparatus"),
    10: ("Medical devices", "Surgical, medical, dental and veterinary apparatus"),
    11: ("HVAC", "Apparatus for lighting, heating, cooking, refrigerating"),
    12: ("Vehicles", "Vehicles and apparatus for locomotion"),
    13: ("Firearms", "Firearms, ammunition and projectiles"),
    14: ("Jewellery", "Precious metals, jewellery, horological instruments"),
    15: ("Musical instruments", "Musical instruments and accessories"),
    16: ("Paper", "Paper and cardboard, printed matter"),
    17: ("Rubber", "Unprocessed and semi-processed rubber, gutta-percha"),
    18: ("Leather", "Leather and imitations of leather"),
    19: ("Building materials", "Materials, not of metal, for building"),
    20: ("Furniture", "Furniture, mirrors, picture frames"),
    21: ("Housewares", "Household or kitchen utensils and containers"),
    22: ("Cordage", "Ropes, string, nets, tents, awnings"),
    23: ("Yarns", "Yarns and threads for textile use"),
    24: ("Textiles", "Textiles and substitutes for textiles"),
    25: ("Clothing", "Clothing, footwear, headwear"),
    26: ("Haberdashery", "Lace, braid and embroidery"),
    27: ("Floor coverings", "Carpets, rugs, mats"),
    28: ("Toys", "Games, toys and playthings"),
    29: ("Processed foods", "Meat, fish, poultry and game"),
    30: ("Staple foods", "Coffee, tea, cocoa and substitutes"),
    31: ("Agriculture", "Raw and unprocessed agricultural products"),
    32: ("Beverages", "Beers, non-alcoholic beverages"),
    33: ("Spirits", "Alcoholic beverages, except beers"),
    34: ("Tobacco", "Tobacco and tobacco substitutes"),
    35: ("Business services", "Advertising, business management"),
    36: ("Financial services", "Financial, monetary and banking services"),
    37: ("Construction", "Construction services, installation and repair"),
    38: ("Telecommunications", "Telecommunications services"),
    39: ("Transport", "Transport, packaging and storage"),
    40: ("Manufacturing", "Treatment of materials, recycling"),
    41: ("Education", "Education, entertainment, sporting and cultural"),
    42: ("Technology services", "Scientific and technological services"),
    43: ("Food services", "Services for providing food and drink"),
    44: ("Medical services", "Medical, beauty and agricultural services"),
    45: ("Legal services", "Legal and security services"),
}


def _create_variant(name: str) -> str:
    """Create a slight spelling variant of a brand name."""
    if len(name) < 3:
        return name
    transforms = [
        lambda n: n[:-1] + ("a" if n[-1] != "a" else "e"),
        lambda n: n[:1].lower() + n[1:],
        lambda n: n + "s",
        lambda n: n + "Pro",
        lambda n: n.replace("a", "aa", 1) if "a" in n else n + "a",
        lambda n: n.replace("e", "i", 1) if "e" in n else n,
        lambda n: n.replace("i", "y", 1) if "i" in n else n,
        lambda n: n + "Plus",
        lambda n: "e" + n,
        lambda n: n.replace("c", "k", 1) if "c" in n.lower() else n,
    ]
    transform = random.choice(transforms)
    return transform(name)


def generate_dataset(count: int = 1000) -> list[dict]:
    """Generate synthetic trademark records."""
    random.seed(42)  # Reproducible
    records = []
    used_ids = set()

    for i in range(count):
        # Pick a base brand
        base = random.choice(BRAND_ROOTS)

        # Sometimes create a variant
        if random.random() < 0.3:
            name = _create_variant(base)
        else:
            name = base

        # Sometimes add prefix/suffix
        if random.random() < 0.2:
            name = random.choice(["The ", "My", "i", "e", "Go"]) + name

        # Assign class and goods
        class_num = random.choice(list(GOODS_BY_CLASS.keys()))
        goods_desc = random.choice(GOODS_BY_CLASS[class_num])

        # Sometimes add a secondary class
        extra_classes = []
        if random.random() < 0.3:
            from backend.agents.class_overlap import NICE_CLASSES as NC
            related = NC.get(class_num, {}).get("related", [])
            if related:
                extra = random.choice(related)
                if extra in GOODS_BY_CLASS:
                    extra_classes.append(extra)

        jurisdiction = random.choice(JURISDICTIONS)

        # Generate unique ID
        tid = f"DEMO{i+1:04d}"
        while tid in used_ids:
            tid = f"DEMO{random.randint(10000, 99999)}"
        used_ids.add(tid)

        norm = normalizer.normalize(name)

        record = {
            "trademark_id": tid,
            "mark_name": name,
            "normalized_name": norm.normalized,
            "nice_classes": [class_num] + extra_classes,
            "goods_description": goods_desc,
            "jurisdiction": jurisdiction,
            "registration_status": "sample_record",
            "source": "synthetic_demo",
            "source_type": "synthetic",
        }
        records.append(record)

    return records


def seed_database():
    """Generate synthetic data and insert into database."""
    init_db()

    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Trademark).count()
        if existing > 0:
            print(f"Database already has {existing} records. Skipping seed.")
            return existing

        # Seed Nice classes
        for class_num, (title, desc) in NICE_CLASS_DATA.items():
            from backend.agents.class_overlap import NICE_CLASSES as NC
            related = NC.get(class_num, {}).get("related", [])
            nc = NiceClass(
                class_number=class_num,
                title=title,
                description=desc,
                related_classes=related,
            )
            db.add(nc)

        # Generate and insert trademarks
        records = generate_dataset(1000)
        for rec in records:
            tm = Trademark(
                trademark_id=rec["trademark_id"],
                mark_name=rec["mark_name"],
                normalized_name=rec["normalized_name"],
                jurisdiction=rec["jurisdiction"],
                registration_status=rec["registration_status"],
                source=rec["source"],
                source_type=rec["source_type"],
            )
            db.add(tm)
            db.flush()

            for cls in rec["nice_classes"]:
                gs = TrademarkGoodsService(
                    trademark_id=tm.id,
                    nice_class=cls,
                    description=rec["goods_description"],
                )
                db.add(gs)

        db.commit()
        print(f"Seeded {len(records)} trademark records and {len(NICE_CLASS_DATA)} Nice classes.")

        # Also save as JSON
        datasets_dir = Path(__file__).resolve().parent.parent / "datasets"
        datasets_dir.mkdir(exist_ok=True)
        with open(datasets_dir / "synthetic_trademarks.json", "w") as f:
            json.dump(records, f, indent=2)
        print(f"Saved dataset to {datasets_dir / 'synthetic_trademarks.json'}")

        return len(records)

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
