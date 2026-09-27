#!/usr/bin/env python3
"""Idempotent seed script for CivicPulse database (§2.3).

Loads >= 30 realistic municipal complaints in Urdu-influenced English across all categories.
Uses deterministic UUIDs derived from a constant namespace to guarantee strict idempotency:
Running it multiple times will never duplicate rows.
"""

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_settings
from app.models.complaint import Complaint
from app.schemas.common import Category, Priority, Status

SEED_NAMESPACE = uuid.UUID("a3b8c2d1-e4f5-4a6b-8c7d-9e0f1a2b3c4d")

# 32 realistic municipal complaints in Urdu-influenced English
SEED_DATA = [
    {
        "slug": "seed-01",
        "text": "Burst water main flooding Street 12 since fajr, water entering ground floors of multiple houses.",
        "location": "Street 12, Sector F-8/2, Islamabad",
        "reporter_contact": "+923001234567",
        "category": Category.WATER,
        "priority": Priority.HIGH,
        "status": Status.IN_PROGRESS,
        "ai_summary": "Major pipeline burst flooding residential ground floors since dawn.",
        "triaged_by": "llm:groq",
        "latency": 320,
    },
    {
        "slug": "seed-02",
        "text": "Transformer sparking loudly near Jamia Masjid chowk, bijli tripping every 10 minutes, huge fire hazard.",
        "location": "Chowk Jamia Masjid, Gulshan-e-Iqbal Block 13-D, Karachi",
        "reporter_contact": "resident_gulshan@gmail.com",
        "category": Category.ELECTRICITY,
        "priority": Priority.HIGH,
        "status": Status.OPEN,
        "ai_summary": "Dangerous transformer sparks and continuous power tripping near mosque.",
        "triaged_by": "llm:groq",
        "latency": 280,
    },
    {
        "slug": "seed-03",
        "text": "Huge heap of kachra overflowing from bin near government school gate. Severe smell and dogs gathering.",
        "location": "Circular Road near Govt High School, Lahore",
        "reporter_contact": None,
        "category": Category.SANITATION,
        "priority": Priority.NORMAL,
        "status": Status.OPEN,
        "ai_summary": "Overflowing garbage dump near school gate creating health hazard.",
        "triaged_by": "rules",
        "latency": 15,
    },
    {
        "slug": "seed-04",
        "text": "Deep crater pothole in middle of main double road, two motorcyclists fell down yesterday night.",
        "location": "Main Boulevard, Allama Iqbal Town, Lahore",
        "reporter_contact": "+923219876543",
        "category": Category.ROADS,
        "priority": Priority.HIGH,
        "status": Status.IN_PROGRESS,
        "ai_summary": "Dangerous road crater causing traffic accidents.",
        "triaged_by": "llm:gemini",
        "latency": 450,
    },
    {
        "slug": "seed-05",
        "text": "Streetlight pole bulb fused since two weeks. Entire gali is pitch dark (andhera) after maghrib.",
        "location": "Gali Number 5, Mohallah Usmania, Rawalpindi",
        "reporter_contact": None,
        "category": Category.STREETLIGHTS,
        "priority": Priority.LOW,
        "status": Status.OPEN,
        "ai_summary": "Dead streetlight bulb causing pitch darkness in residential alley.",
        "triaged_by": "rules",
        "latency": 12,
    },
    {
        "slug": "seed-06",
        "text": "No water supply in our lane for the past 4 days. Motor is pulling only air, residents buying private tankers.",
        "location": "Lane 4, Phase 4, Bahria Town, Rawalpindi",
        "reporter_contact": "tariq.mehmood@hotmail.com",
        "category": Category.WATER,
        "priority": Priority.HIGH,
        "status": Status.OPEN,
        "ai_summary": "Zero municipal water supply for four consecutive days.",
        "triaged_by": "llm:groq",
        "latency": 310,
    },
    {
        "slug": "seed-07",
        "text": "Live 11kV electrical wire hanging down low to shoulder height from pole after heavy wind storm.",
        "location": "Near Pehalwan Pakwan, G-9 Markaz, Islamabad",
        "reporter_contact": "+923335551212",
        "category": Category.ELECTRICITY,
        "priority": Priority.HIGH,
        "status": Status.IN_PROGRESS,
        "ai_summary": "Extremely dangerous low hanging live 11kV wire on main pathway.",
        "triaged_by": "llm:groq",
        "latency": 290,
    },
    {
        "slug": "seed-08",
        "text": "Main gutter choked and black sewage water bubbling up onto road, pedestrian walking impossible.",
        "location": "Commercial Market, Satellite Town, Gujranwala",
        "reporter_contact": "+923005544332",
        "category": Category.SANITATION,
        "priority": Priority.NORMAL,
        "status": Status.OPEN,
        "ai_summary": "Choked sewage overflowing across commercial marketplace road.",
        "triaged_by": "rules",
        "latency": 18,
    },
    {
        "slug": "seed-09",
        "text": "Road dug up for gas pipeline work two months ago, contractors left trenches open without asphalt filling.",
        "location": "Sector I-10/1, Street 45, Islamabad",
        "reporter_contact": None,
        "category": Category.ROADS,
        "priority": Priority.NORMAL,
        "status": Status.OPEN,
        "ai_summary": "Unfinished road excavation trenches left unpaved for two months.",
        "triaged_by": "simulated",
        "latency": 5,
    },
    {
        "slug": "seed-10",
        "text": "Three street lamps flickering continuously like disco lights, disturbing nearby bedrooms.",
        "location": "Khayaban-e-Seher, Phase 6, DHA Karachi",
        "reporter_contact": "dha_resident_6@yahoo.com",
        "category": Category.STREETLIGHTS,
        "priority": Priority.LOW,
        "status": Status.RESOLVED,
        "ai_summary": "Flickering street light fixtures along residential street.",
        "triaged_by": "rules",
        "latency": 14,
    },
    {
        "slug": "seed-11",
        "text": "Drinking water coming contaminated with dirty foul smell and brown color from tap since morning.",
        "location": "Mohallah Raja Sultan, Rawalpindi",
        "reporter_contact": "+923451122334",
        "category": Category.WATER,
        "priority": Priority.HIGH,
        "status": Status.OPEN,
        "ai_summary": "Contaminated tap water with foul smell posing severe health risk.",
        "triaged_by": "llm:groq",
        "latency": 340,
    },
    {
        "slug": "seed-12",
        "text": "Electricity voltage dropping to 120V in afternoon, AC and refrigerator motors burning out.",
        "location": "Wapda Town, Block B, Multan",
        "reporter_contact": "+923129988776",
        "category": Category.ELECTRICITY,
        "priority": Priority.NORMAL,
        "status": Status.OPEN,
        "ai_summary": "Extreme low voltage damaging household appliances.",
        "triaged_by": "rules",
        "latency": 15,
    },
    {
        "slug": "seed-13",
        "text": "Sanitation sweepers (safai staff) have not visited street for three weeks, leaves and polythene bags choking drains.",
        "location": "Street 8, Model Town C Block, Lahore",
        "reporter_contact": None,
        "category": Category.SANITATION,
        "priority": Priority.LOW,
        "status": Status.OPEN,
        "ai_summary": "Absence of sanitary sweeping staff causing accumulation of street debris.",
        "triaged_by": "rules",
        "latency": 16,
    },
    {
        "slug": "seed-14",
        "text": "Speed breakers constructed illegally high without any white paint markings, scraping car chassis.",
        "location": "University Town Road, Peshawar",
        "reporter_contact": "imran_pesh@gmail.com",
        "category": Category.ROADS,
        "priority": Priority.LOW,
        "status": Status.RESOLVED,
        "ai_summary": "Unmarked illegal high speed bumps damaging vehicles.",
        "triaged_by": "simulated",
        "latency": 6,
    },
    {
        "slug": "seed-15",
        "text": "Heavy iron streetlight pole fell down onto roadside footpath during thunder storm, luckily no injury.",
        "location": "Kashmir Highway Service Road, Islamabad",
        "reporter_contact": "+923018882211",
        "category": Category.STREETLIGHTS,
        "priority": Priority.HIGH,
        "status": Status.RESOLVED,
        "ai_summary": "Fallen streetlight pole blocking footpath.",
        "triaged_by": "llm:groq",
        "latency": 305,
    },
    {
        "slug": "seed-16",
        "text": "Clean water underground pipeline leaking clean water at 100 gallons per minute into roadside drain.",
        "location": "Main Khyaban-e-Ittehad, Phase 2, DHA Karachi",
        "reporter_contact": "+923214445566",
        "category": Category.WATER,
        "priority": Priority.NORMAL,
        "status": Status.OPEN,
        "ai_summary": "Massive clean water pipeline leakage wasting municipal supply.",
        "triaged_by": "rules",
        "latency": 20,
    },
    {
        "slug": "seed-17",
        "text": "Phase imbalance in our lane causing neutral wire to carry 80V current, giving mild shock on water taps.",
        "location": "Sector G-11/3, Street 18, Islamabad",
        "reporter_contact": "kamran_g11@yahoo.com",
        "category": Category.ELECTRICITY,
        "priority": Priority.HIGH,
        "status": Status.OPEN,
        "ai_summary": "Dangerous electrical leakage into plumbing due to neutral wire charge.",
        "triaged_by": "llm:groq",
        "latency": 330,
    },
    {
        "slug": "seed-18",
        "text": "Dead stray animal lying beside empty plot since yesterday noon, unbearable foul smell in entire mohallah.",
        "location": "Plot 42, Johar Town Block R-1, Lahore",
        "reporter_contact": "+923337776655",
        "category": Category.SANITATION,
        "priority": Priority.HIGH,
        "status": Status.RESOLVED,
        "ai_summary": "Emergency carcass removal required due to severe odor hazard.",
        "triaged_by": "llm:groq",
        "latency": 295,
    },
    {
        "slug": "seed-19",
        "text": "Manhole cover completely missing in middle of unlit street, deadly death trap for children and cars.",
        "location": "Gali 3, Muslim Town, Rawalpindi",
        "reporter_contact": "+923009991122",
        "category": Category.SANITATION,
        "priority": Priority.HIGH,
        "status": Status.IN_PROGRESS,
        "ai_summary": "Open manhole death trap in unlit street requiring immediate cover.",
        "triaged_by": "llm:groq",
        "latency": 310,
    },
    {
        "slug": "seed-20",
        "text": "Traffic signal lights at busy roundabout stuck on yellow blinking mode, creating massive traffic jam.",
        "location": "Chungi No. 9 Chowk, Bosan Road, Multan",
        "reporter_contact": None,
        "category": Category.ROADS,
        "priority": Priority.NORMAL,
        "status": Status.OPEN,
        "ai_summary": "Malfunctioning traffic signal causing gridlock at central intersection.",
        "triaged_by": "rules",
        "latency": 15,
    },
    {
        "slug": "seed-21",
        "text": "Request to install two new streetlight poles on back road of community park for safety of evening walkers.",
        "location": "Ladies Park, Block 6, PECHS, Karachi",
        "reporter_contact": "pechs_committee@gmail.com",
        "category": Category.STREETLIGHTS,
        "priority": Priority.LOW,
        "status": Status.OPEN,
        "ai_summary": "Public request for new streetlight installations around park perimeter.",
        "triaged_by": "simulated",
        "latency": 6,
    },
    {
        "slug": "seed-22",
        "text": "Water tanker mafia punctured the main distribution valve to fill their commercial tankers illegally.",
        "location": "Manghopir Road near Orangi Sector 11, Karachi",
        "reporter_contact": "+923458877665",
        "category": Category.WATER,
        "priority": Priority.HIGH,
        "status": Status.OPEN,
        "ai_summary": "Illegal tampering and vandalism of main water distribution valve.",
        "triaged_by": "llm:groq",
        "latency": 350,
    },
    {
        "slug": "seed-23",
        "text": "Electric meter box on outer wall caught fire due to loose wiring sparks, fire extinguished but supply cut off.",
        "location": "House 112, Street 7, Cavalry Ground, Lahore",
        "reporter_contact": "+923218765432",
        "category": Category.ELECTRICITY,
        "priority": Priority.HIGH,
        "status": Status.RESOLVED,
        "ai_summary": "Burned meter box after electrical fire needing replacement.",
        "triaged_by": "llm:gemini",
        "latency": 410,
    },
    {
        "slug": "seed-24",
        "text": "Construction debris and malba dumped directly onto pedestrian footpath, pedestrians forced to walk on main road.",
        "location": "Main Murree Road, near Chandni Chowk, Rawalpindi",
        "reporter_contact": None,
        "category": Category.ROADS,
        "priority": Priority.NORMAL,
        "status": Status.OPEN,
        "ai_summary": "Illegal dumping of construction rubble obstructing pedestrian walkway.",
        "triaged_by": "rules",
        "latency": 14,
    },
    {
        "slug": "seed-25",
        "text": "Hospital waste bags found dumped near public nullah bridge, highly infectious medical waste hazard.",
        "location": "Nullah Bridge, Nishtar Road, Multan",
        "reporter_contact": "+923023344556",
        "category": Category.SANITATION,
        "priority": Priority.HIGH,
        "status": Status.IN_PROGRESS,
        "ai_summary": "Hazardous hospital medical waste dumped illegally near public stream.",
        "triaged_by": "llm:groq",
        "latency": 325,
    },
    {
        "slug": "seed-26",
        "text": "Municipal tube well pump operator does not turn on motor during scheduled morning hours.",
        "location": "Tube Well #4, Sector G-7/2, Islamabad",
        "reporter_contact": "resident_g7@gmail.com",
        "category": Category.WATER,
        "priority": Priority.NORMAL,
        "status": Status.OPEN,
        "ai_summary": "Operational negligence in morning municipal tube well pump schedule.",
        "triaged_by": "rules",
        "latency": 15,
    },
    {
        "slug": "seed-27",
        "text": "Streetlight timer switch broken, all 40 lights along canal road staying on throughout bright sunny day.",
        "location": "Canal Bank Road, near Dharampura, Lahore",
        "reporter_contact": None,
        "category": Category.STREETLIGHTS,
        "priority": Priority.LOW,
        "status": Status.OPEN,
        "ai_summary": "Broken daylight timer switch causing continuous daytime streetlight burning.",
        "triaged_by": "rules",
        "latency": 12,
    },
    {
        "slug": "seed-28",
        "text": "Storm water drainage nullah blocked with plastic rubbish, rainwater backing up during pre-monsoon showers.",
        "location": "Gujjar Nullah section near Liaquatabad, Karachi",
        "reporter_contact": "+923004455667",
        "category": Category.SANITATION,
        "priority": Priority.HIGH,
        "status": Status.OPEN,
        "ai_summary": "Severe plastic blockage in natural storm drainage channel.",
        "triaged_by": "llm:groq",
        "latency": 340,
    },
    {
        "slug": "seed-29",
        "text": "Road name board fallen down at intersection, delivery riders and ambulances getting lost.",
        "location": "Junction 9 & 10, Sector I-8/4, Islamabad",
        "reporter_contact": None,
        "category": Category.OTHER,
        "priority": Priority.LOW,
        "status": Status.REJECTED,
        "ai_summary": "Damaged intersection street name signpost needing reinstallation.",
        "triaged_by": "rules",
        "latency": 10,
    },
    {
        "slug": "seed-30",
        "text": "Illegal political banners and advertising hoardings tied with high tension electricity cables.",
        "location": "Ferozepur Road near Ichhra, Lahore",
        "reporter_contact": "+923136655443",
        "category": Category.ELECTRICITY,
        "priority": Priority.NORMAL,
        "status": Status.OPEN,
        "ai_summary": "Unauthorized banners attached to power cables creating electrical hazard.",
        "triaged_by": "simulated",
        "latency": 7,
    },
    {
        "slug": "seed-31",
        "text": "Water booster suction pump installed by private commercial plaza sucking water directly from main line.",
        "location": "Plaza 5, Commercial Zone, Bahria Phase 7, Rawalpindi",
        "reporter_contact": "plazawatch@gmail.com",
        "category": Category.WATER,
        "priority": Priority.NORMAL,
        "status": Status.OPEN,
        "ai_summary": "Illegal heavy suction pump depriving adjacent houses of water.",
        "triaged_by": "llm:groq",
        "latency": 320,
    },
    {
        "slug": "seed-32",
        "text": "Sinkhole formed on asphalt road after water line burst underneath, car tyre trapped inside.",
        "location": "Tipu Sultan Road, KDA Scheme 1, Karachi",
        "reporter_contact": "+923225566778",
        "category": Category.ROADS,
        "priority": Priority.HIGH,
        "status": Status.IN_PROGRESS,
        "ai_summary": "Sudden road sinkhole trapping vehicle after subterranean pipe leak.",
        "triaged_by": "llm:groq",
        "latency": 360,
    },
]


def seed_database() -> None:
    settings = get_settings()
    engine = create_engine(settings.SYNC_DATABASE_URL)

    with Session(engine) as session:
        created_count = 0
        skipped_count = 0
        base_time = datetime.now(timezone.utc) - timedelta(days=7)

        for i, item in enumerate(SEED_DATA):
            # Derive deterministic UUID from constant namespace and seed slug
            complaint_id = uuid.uuid5(SEED_NAMESPACE, item["slug"])

            # Check if row already exists
            existing = session.execute(
                select(Complaint).where(Complaint.id == complaint_id)
            ).scalar_one_or_none()

            if existing:
                skipped_count += 1
                continue

            # Stagger creation timestamps across past week
            row_created_at = base_time + timedelta(hours=i * 5, minutes=i * 12)

            complaint = Complaint(
                id=complaint_id,
                text=item["text"],
                location=item["location"],
                reporter_contact=item["reporter_contact"],
                category=item["category"],
                priority=item["priority"],
                status=item["status"],
                ai_summary=item["ai_summary"],
                triaged_by=item["triaged_by"],
                triage_latency_ms=item["latency"],
                created_at=row_created_at,
                updated_at=row_created_at,
            )
            session.add(complaint)
            created_count += 1

        session.commit()
        print(f"Seed complete: {created_count} inserted, {skipped_count} existing/skipped (Total: {len(SEED_DATA)}).")


if __name__ == "__main__":
    seed_database()
