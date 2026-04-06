import json
import os
from pathlib import Path

def create_actor_files(actor_name, media_ids):
    actor_dir = Path("actress") / actor_name
    actor_dir.mkdir(parents=True, exist_ok=True)
    
    media_list = [{"id": m} for m in media_ids]
    with open(actor_dir / "media_list.json", "w", encoding="utf-8") as f:
        json.dump(media_list, f, indent=2, ensure_ascii=False)
    
    print(f"Created files for {actor_name} in {actor_dir}")

actors = {
    "明日葉みつは": ["OAE-237", "OFJE-460", "REBD-812", "SONE-019", "SONE-061", "SONE-120", "SONE-143", "SONE-186", "SONE-252", "SONE-294", "SONE-343", "SONE-439", "SONE-481", "SONE-527", "SONE-576", "SONE-622", "SONE-668", "SSIS-818", "SSIS-833", "SSIS-868", "SSIS-906", "pfes-107", "sivr-313", "sone-107", "sone-388", "ssis-943", "SONE-923", "SNOS-006", "SNOS-074", "sivr-473", "PFES-133"],
    "明里つむぎ": ["ACHJ-008", "ADN-188", "ADN-210", "ADN-243", "ADN-251", "ADN-256", "ADN-262", "ADN-267", "ADN-277", "ADN-298", "ADN-302", "ADN-314", "ADN-328", "ADN-341", "ADN-347", "ADN-366", "ADN-381", "ADN-400", "AP-019", "ATID-318", "ATID-368", "ATID-379", "ATID-394", "ATID-399", "ATID-431", "ATID-456", "ATID-489", "ATID-495", "ATID-522", "ATKD-278", "ATKD-286", "ATKD-362", "BAGBD-068", "HHD-800", "IDBD-765", "IDBD-911", "IDBD-992", "IPBZ-005", "IPX-004", "IPX-021", "IPX-037", "IPX-053", "IPX-071", "IPX-101", "IPX-113", "IPX-128", "IPX-142", "IPX-175", "IPX-191", "IPX-204", "IPX-316", "IPX-328", "IPX-344", "IPX-360", "IPX-374", "IPX-389", "IPX-404"],
    "涼森れむ": ["ABF-007", "ABF-017", "ABF-029", "ABF-034", "ABF-043", "ABF-055", "ABF-063", "ABF-073", "ABF-087", "ABF-094", "ABF-105", "ABF-114", "ABF-125", "ABF-137", "ABF-149", "ABF-159", "ABF-168", "ABF-188", "ABF-199", "ABF-217", "ABP-889", "ABP-919", "ABP-933", "ABP-975", "ABW-032", "ABW-065", "ABW-076", "ABW-087", "ABW-108", "ABW-121", "ABW-135", "ABW-153", "ABW-179", "ABW-187", "ABW-198", "ABW-208", "ABW-220", "ABW-244", "ABW-254", "ABW-265", "ABW-276", "ABW-286", "ABW-296", "ABW-305", "ABW-314", "ABW-324", "ABW-339", "ABW-348", "ABW-358", "ABW-366", "BGN-054", "HEO-009", "HEO-016", "HRV-035"]
}

for actor, media_ids in actors.items():
    create_actor_files(actor, media_ids)
