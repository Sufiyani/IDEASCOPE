"""
IdeaScope – Reference data: categories and SDGs.
Owner: Member 2 (Sufiyaan Imran)

Single source of truth. Spellings match the SSUET proposal form exactly.
"""

from __future__ import annotations

# id -> name  (12 categories)
CATEGORY_NAMES: dict[int, str] = {
    1: "Artificial Intelligence and Big Data",
    2: "Augmented and Virtual Reality",
    3: "E-Health",
    4: "E-Commerce",
    5: "Internet of Things (IoT)",
    6: "Block Chain",
    7: "Cloud Computing and Cyber Security",
    8: "Game Development",
    9: "Graphics Animation",
    10: "Nano Technology",
    11: "Shared Economy",
    12: "Other",
}

# number -> name  (17 SDGs)
SDG_NAMES: dict[int, str] = {
    1: "No Poverty",
    2: "Zero Hunger",
    3: "Good Health and Well-Being",
    4: "Quality Education",
    5: "Gender Equality",
    6: "Clean Water and Sanitation",
    7: "Affordable and Clean Energy",
    8: "Decent Work and Economic Growth",
    9: "Industry, Innovation and Infrastructure",
    10: "Reduce Inequalities",
    11: "Sustainable Cities and Communities",
    12: "Responsible Consumption and Production",
    13: "Climate Action",
    14: "Life Below Water",
    15: "Life On Land",
    16: "Peace, Justice and Strong Institutions",
    17: "Partnerships for the Goals",
}
