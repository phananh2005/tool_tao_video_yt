import json
import sqlite3
from core.contracts import AssetJSON, AssetSceneJSON

asset_obj = AssetJSON(
    script_id=2,
    assets=[
        AssetSceneJSON(scene_number=1, image_prompt="p", image_path="p.jpg"),
        AssetSceneJSON(scene_number=2, image_prompt="p", image_path="p.jpg"),
    ]
)

scenes_dict = [sc.__dict__.copy() for sc in asset_obj.assets]
asset_dict = {
    'script_id': asset_obj.script_id,
    'assets': scenes_dict
}
print("Before:", asset_dict)

existing_data = {
    "assets": [
        {"scene_number": 1, "duration_seconds": 10.0, "audio_path": "a1.mp3"}
    ]
}

for existing_sc in existing_data.get('assets', []):
    for new_sc in asset_dict['assets']:
        if new_sc.get('scene_number') == existing_sc.get('scene_number'):
            if 'duration_seconds' in existing_sc:
                new_sc['duration_seconds'] = existing_sc['duration_seconds']
            if 'audio_path' in existing_sc:
                new_sc['audio_path'] = existing_sc['audio_path']

print("After:", asset_dict)
