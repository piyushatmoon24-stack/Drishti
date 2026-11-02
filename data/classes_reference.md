# Drishti Assistive Vision Classes Reference (Indian Bilingual Edition)

## 🎯 Active Deployed 8-Class Model (Edge Impulse FOMO on Himax WiseEye2 / Ethos-U55 NPU)
The on-device FOMO MobileNetV2 0.35 model running on the Grove Vision AI Module V2 Ethos-U55 NPU is trained on **8 high-accuracy, 100% balanced classes** (1,200 curated images per class, 9,600 total images). Dog has been pruned to eliminate any person-dog confusion.

| Model Index | Model Label | Class ID | DFPlayer Track | Object / Hazard Description | Priority Level | Indian Bilingual Voice Prompt |
| :---: | :---: | :---: | :---: | :--- | :---: | :--- |
| `0` | `car` | `0019` | `0019.mp3` | Moving or parked cars, taxis, automobiles | **Critical (1)** | *"Car ahead. आगे गाड़ी है।"* |
| `1` | `chair` | `0023` | `0023.mp3` | Indoor chairs, benches, office seating | **Low (3)** | *"Chair nearby. आगे कुर्सी है।"* |
| `2` | `door` | `0008` | `0008.mp3` | Closed doors, entryways, room access | **Normal (2)** | *"Closed door. दरवाजा बंद है।"* |
| `3` | `motorcycle` | `0018` | `0018.mp3` | Motorcycles, motorbikes, scooters | **Critical (1)** | *"Motorcycle nearby. बाइक पास में है।"* |
| `4` | `person` | `0013` | `0013.mp3` | Pedestrians, walking humans | **Normal (2)** | *"Person ahead. आगे व्यक्ति है।"* |
| `5` | `pole` | `0006` | `0006.mp3` | Lampposts, street utility poles, pillars | **Normal (2)** | *"Obstacle, pole ahead. आगे खंभा है।"* |
| `6` | `stairs` | `0001` | `0001.mp3` | Descending & ascending stairs (fall hazard) | **Critical (1)** | *"Caution, stairs down. सावधान, नीचे सीढ़ियां।"* |
| `7` | `table` | `0026` | `0026.mp3` | Tables, work desks, dining tables | **Low (3)** | *"Table ahead. आगे मेज है।"* |

---

## 📚 Complete 50-Class Drishti Catalog & MicroSD Audio Library

Each class is assigned a 4-digit unique numerical ID (`0001` - `0050`) matching the exact MP3 track `/MP3/xxxx.mp3` on the MicroSD card.
The default voice is **Indian Bilingual** (English keywords followed by clear Hindi speech), using natural Indian intonation that is immediately recognizable and understandable to users in India.

| ID | Class Label | Object / Situation | Hazard Level | Indian Bilingual Voice Prompt (English + Hindi) | Debounce |
| :---: | :---: | :--- | :---: | :--- | :---: |
| `0001` | `0001` | Stairs Down | Critical (1) | *"Caution, stairs down. सावधान, नीचे सीढ़ियां।"* | 1.5s |
| `0002` | `0002` | Stairs Up | Critical (1) | *"Stairs up. ऊपर सीढ़ियां।"* | 2.0s |
| `0003` | `0003` | Curb / Drop-off | Critical (1) | *"Caution, drop-off ahead. सावधान, आगे ढलान।"* | 1.5s |
| `0004` | `0004` | Pothole / Trench / Hole | Critical (1) | *"Warning, hole ahead. सावधान, आगे गड्ढा है।"* | 1.5s |
| `0005` | `0005` | Low Overhead Obstacle | Critical (1) | *"Caution, head hazard. सावधान, सिर बचाएं।"* | 1.5s |
| `0006` | `0006` | Pole / Street Post | High (2) | *"Obstacle, pole ahead. आगे खंभा है।"* | 2.5s |
| `0007` | `0007` | Wall / Barricade | High (2) | *"Wall ahead. आगे दीवार है।"* | 2.5s |
| `0008` | `0008` | Closed Door | Normal (2) | *"Closed door. दरवाजा बंद है।"* | 3.0s |
| `0009` | `0009` | Open Door | Normal (2) | *"Open door. दरवाजा खुला है।"* | 3.0s |
| `0010` | `0010` | Zebra Crosswalk | High (2) | *"Crosswalk ahead. जेब्रा क्रॉसिंग।"* | 3.0s |
| `0011` | `0011` | Traffic Light (Red) | Critical (1) | *"Red signal, stop. लाल बत्ती, रुकिए।"* | 2.0s |
| `0012` | `0012` | Traffic Light (Green) | Critical (1) | *"Green signal, proceed. हरी बत्ती, चलिए।"* | 2.0s |
| `0013` | `0013` | Person / Pedestrian | Normal (2) | *"Person ahead. आगे व्यक्ति है।"* | 3.0s |
| `0014` | `0014` | Dog / Guide Dog | Normal (2) | *"Dog nearby. पास में कुत्ता है।"* | 2.5s |
| `0015` | `0015` | Cat / Small Pet | Low (3) | *"Small animal. बिल्ली या छोटा जानवर।"* | 3.0s |
| `0016` | `0016` | Cow / Large Animal | Critical (1) | *"Caution, large animal. सावधान, गाय या जानवर है।"* | 2.0s |
| `0017` | `0017` | Bicycle | High (2) | *"Bicycle approaching. साइकिल आ रही है।"* | 2.5s |
| `0018` | `0018` | Motorcycle / Scooter | Critical (1) | *"Motorcycle nearby. बाइक पास में है।"* | 2.5s |
| `0019` | `0019` | Car / Taxi | Critical (1) | *"Car ahead. आगे गाड़ी है।"* | 2.5s |
| `0020` | `0020` | Bus | High (2) | *"Bus ahead. आगे बस है।"* | 2.5s |
| `0021` | `0021` | Truck | High (2) | *"Truck ahead. आगे ट्रक है।"* | 2.5s |
| `0022` | `0022` | Auto Rickshaw | High (2) | *"Auto rickshaw nearby. ऑटो रिक्शा पास में है।"* | 2.5s |
| `0023` | `0023` | Chair | Low (3) | *"Chair nearby. आगे कुर्सी है।"* | 3.5s |
| `0024` | `0024` | Sofa / Couch | Low (3) | *"Sofa ahead. आगे सोफा है।"* | 3.5s |
| `0025` | `0025` | Bed | Low (3) | *"Bed ahead. आगे बिस्तर है।"* | 3.5s |
| `0026` | `0026` | Table / Desk | Low (3) | *"Table ahead. आगे मेज है।"* | 3.5s |
| `0027` | `0027` | Toilet / Commode | Normal (3) | *"Toilet ahead. शौचालय आगे है।"* | 3.0s |
| `0028` | `0028` | Washbasin / Sink | Normal (3) | *"Washbasin ahead. वॉशबेसिन आगे है।"* | 3.0s |
| `0029` | `0029` | Elevator / Lift | Normal (2) | *"Elevator door. लिफ्ट का दरवाजा।"* | 3.0s |
| `0030` | `0030` | Dustbin / Trash Can | Low (3) | *"Dustbin nearby. कचरे का डिब्बा।"* | 4.0s |
| `0031` | `0031` | White Cane | Normal (3) | *"White cane. सफेद छड़ी।"* | 3.0s |
| `0032` | `0032` | Eyeglasses / Spectacles | Low (3) | *"Eyeglasses. चश्मा।"* | 3.0s |
| `0033` | `0033` | Mobile Phone | Low (3) | *"Mobile phone. मोबाइल फोन।"* | 3.0s |
| `0034` | `0034` | Medicine Bottle / Pills | High (2) | *"Medicine container. दवाई की शीशी।"* | 2.5s |
| `0035` | `0035` | Water Bottle | Low (3) | *"Water bottle. पानी की बोतल।"* | 3.0s |
| `0036` | `0036` | Cup / Mug / Glass | Low (3) | *"Cup or glass. कप या ग्लास।"* | 3.0s |
| `0037` | `0037` | Plate / Food Bowl | Low (3) | *"Food plate. खाने की थाली।"* | 3.0s |
| `0038` | `0038` | Spoon / Fork / Cutlery | Low (3) | *"Spoon or cutlery. चम्मच।"* | 3.0s |
| `0039` | `0039` | Currency Note | High (2) | *"Currency note. रुपये का नोट।"* | 2.5s |
| `0040` | `0040` | Coin | Low (3) | *"Coin detected. सिक्का।"* | 3.0s |
| `0041` | `0041` | Keys / Keyring | Low (3) | *"Keys detected. चाबी।"* | 3.0s |
| `0042` | `0042` | Wallet / Purse | Low (3) | *"Wallet detected. बटुआ या पर्स।"* | 3.0s |
| `0043` | `0043` | Footwear / Shoes | Low (3) | *"Footwear on floor. जूते या चप्पल।"* | 3.5s |
| `0044` | `0044` | Clothes / Jacket | Info (4) | *"Clothing item. कपड़े।"* | 4.0s |
| `0045` | `0045` | Electrical Wall Socket | High (2) | *"Caution, electric socket. सावधान, बिजली का बोर्ड।"* | 2.5s |
| `0046` | `0046` | Stove / Cooking Burner | Critical (1) | *"Warning, hot stove. सावधान, चूल्हा या गैस बर्नर।"* | 2.0s |
| `0047` | `0047` | Refrigerator | Low (3) | *"Refrigerator ahead. फ्रिज आगे है।"* | 4.0s |
| `0048` | `0048` | Toothbrush | Low (3) | *"Toothbrush. टूथब्रश।"* | 3.0s |
| `0049` | `0049` | Soap / Sanitizer Bottle | Low (3) | *"Soap or sanitizer. साबुन या सैनिटाइज़र।"* | 3.0s |
| `0050` | `0050` | Ceiling / Pedestal Fan | Low (3) | *"Fan ahead. पंखा।"* | 4.0s |

---

## 🎙️ Changing Voice Modes

You can regenerate the audio tracks at any time using:

1. **Bilingual Mode (Default - English + Hindi)**:
   ```bash
   python scripts/generate_audio_assets.py --mode bilingual
   ```
2. **Indian English Accent Mode**:
   ```bash
   python scripts/generate_audio_assets.py --mode indian_english --voice en-IN-NeerjaExpressiveNeural
   ```
3. **Pure Hindi Mode**:
   ```bash
   python scripts/generate_audio_assets.py --mode hindi --voice hi-IN-SwaraNeural
   ```
