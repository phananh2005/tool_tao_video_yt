with open("core/contracts.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("class AssetSceneJSON:\n    scene_number: int\n    image_prompt: str\n    image_path: str",
                          "class AssetSceneJSON:\n    scene_number: int\n    image_prompt: str\n    image_path: str\n    audio_path: Optional[str] = None\n    duration_seconds: Optional[float] = None")

with open("core/contracts.py", "w", encoding="utf-8") as f:
    f.write(content)
