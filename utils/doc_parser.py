from __future__ import annotations



import re

from pathlib import Path

from typing import Any



import pandas as pd



try:

    import pdfplumber

except ImportError:

    pdfplumber = None



try:

    from PIL import Image

except ImportError:

    Image = None





EXPECTED_COLUMNS = [

    "shipment_id",

    "ship_date",

    "carrier",

    "facility",

    "weight_lbs",

    "miles",

    "base_freight_usd",

    "accessorial_charge_usd",

]





def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()



    df.columns = [

        str(col).strip().lower().replace(" ", "_").replace("-", "_")

        for col in df.columns

    ]



    return df





def ensure_expected_columns(df: pd.DataFrame) -> pd.DataFrame:

    df = normalize_columns(df)



    rename_map = {



        # shipment id

        "load_id": "shipment_id",

        "order_id": "shipment_id",

        "id": "shipment_id",

        "shipment_number": "shipment_id",



        # date

        "date": "ship_date",

        "pickup_date": "ship_date",

        "shipment_date": "ship_date",

        "ship_dt": "ship_date",



        # carrier

        "carrier_name": "carrier",

        "trucking_company": "carrier",

        "provider": "carrier",



        # facility

        "warehouse": "facility",

        "location": "facility",

        "dc": "facility",

        "distribution_center": "facility",



        # weight

        "weight": "weight_lbs",

        "lbs": "weight_lbs",

        "weight_lb": "weight_lbs",

        "shipment_weight": "weight_lbs",



        # miles

        "distance": "miles",

        "distance_miles": "miles",

        "route_miles": "miles",

        "trip_miles": "miles",



        # freight

        "freight_cost": "base_freight_usd",

        "base_rate": "base_freight_usd",

        "freight": "base_freight_usd",

        "base_cost": "base_freight_usd",



        # accessorial

        "extra_charges": "accessorial_charge_usd",

        "accessorial_cost": "accessorial_charge_usd",

        "extra_cost": "accessorial_charge_usd",

        "accessorials": "accessorial_charge_usd",

        "extra_fees": "accessorial_charge_usd",

    }



    mapped_columns = {}



    for old, new in rename_map.items():

        if old in df.columns and new not in df.columns:

            mapped_columns[old] = new



    df = df.rename(columns=rename_map)



    for col in EXPECTED_COLUMNS:

        if col not in df.columns:

            df[col] = None



    df = df[EXPECTED_COLUMNS]



    # save mapping metadata

    df.attrs["column_mapping"] = mapped_columns



    return df





def parse_excel(file_obj: Any) -> pd.DataFrame:

    df = pd.read_excel(file_obj)

    return ensure_expected_columns(df)





def parse_csv(file_obj: Any) -> pd.DataFrame:

    df = pd.read_csv(file_obj)

    return ensure_expected_columns(df)





def parse_pdf(file_obj: Any) -> pd.DataFrame:



    if pdfplumber is None:

        raise ImportError("pdfplumber is not installed.")



    with pdfplumber.open(file_obj) as pdf:



        text_chunks = []



        for page in pdf.pages:

            page_text = page.extract_text()



            if page_text:

                text_chunks.append(page_text)



    text = "\n".join(text_chunks)



    shipment_match = re.search(r"(shipment_id|load_id|order_id)[:\-]?\s*(.+)", text, re.IGNORECASE)

    date_match = re.search(r"(ship_date|date|pickup_date)[:\-]?\s*(.+)", text, re.IGNORECASE)

    carrier_match = re.search(r"carrier[:\-]?\s*(.+)", text, re.IGNORECASE)

    facility_match = re.search(r"(facility|warehouse|location)[:\-]?\s*(.+)", text, re.IGNORECASE)

    weight_match = re.search(r"(weight|lbs)[:\-]?\s*(.+)", text, re.IGNORECASE)

    miles_match = re.search(r"(miles|distance)[:\-]?\s*(.+)", text, re.IGNORECASE)

    freight_match = re.search(r"(freight|base_rate)[:\-]?\s*(.+)", text, re.IGNORECASE)

    accessorial_match = re.search(r"(accessorial|extra_charges)[:\-]?\s*(.+)", text, re.IGNORECASE)



    row = {

        "shipment_id": shipment_match.group(2).strip() if shipment_match else None,

        "ship_date": date_match.group(2).strip() if date_match else None,

        "carrier": carrier_match.group(1).strip() if carrier_match else None,

        "facility": facility_match.group(2).strip() if facility_match else None,

        "weight_lbs": weight_match.group(2).strip() if weight_match else None,

        "miles": miles_match.group(2).strip() if miles_match else None,

        "base_freight_usd": freight_match.group(2).strip() if freight_match else None,

        "accessorial_charge_usd": accessorial_match.group(2).strip() if accessorial_match else None,

    }



    df = pd.DataFrame([row])



    return ensure_expected_columns(df)





def parse_image(file_obj: Any) -> pd.DataFrame:



    if Image is None:

        raise ImportError("Pillow is not installed.")



    _ = Image.open(file_obj)



    row = {

        "shipment_id": None,

        "ship_date": None,

        "carrier": None,

        "facility": None,

        "weight_lbs": None,

        "miles": None,

        "base_freight_usd": None,

        "accessorial_charge_usd": None,

    }



    df = pd.DataFrame([row])



    return ensure_expected_columns(df)





def parse_uploaded_document(file_obj: Any, filename: str) -> pd.DataFrame:



    suffix = Path(filename).suffix.lower()



    if suffix in [".xlsx", ".xls"]:

        return parse_excel(file_obj)



    if suffix == ".csv":

        return parse_csv(file_obj)



    if suffix == ".pdf":

        return parse_pdf(file_obj)



    if suffix in [".png", ".jpg", ".jpeg"]:

        return parse_image(file_obj)



    raise ValueError(f"Unsupported file type: {suffix}")