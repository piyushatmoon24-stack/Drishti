#ifndef VISION_AI_PARSER_H
#define VISION_AI_PARSER_H

#include <Arduino.h>
#include "config.h"

// Detected object structure
struct Detection {
  uint16_t classId;     // 1 to 50 (matching "0001" to "0050")
  uint8_t confidence;   // 0 to 100%
  int16_t x;
  int16_t y;
  int16_t w;
  int16_t h;
  uint8_t priority;     // 1 (Critical Hazard), 2 (Moving Obstacle), 3 (Furniture), 4 (Low)
};

class VisionAIParser {
private:
  HardwareSerial* _serial;
  String _rxBuffer;

  String extractField(const String& str, const String& key) {
    int keyPos = str.indexOf("\"" + key + "\"");
    if (keyPos == -1) keyPos = str.indexOf(key);
    if (keyPos == -1) return "";
    int colonPos = str.indexOf(':', keyPos);
    if (colonPos == -1) return "";
    int valStart = colonPos + 1;
    while (valStart < (int)str.length() && (str.charAt(valStart) == ' ' || str.charAt(valStart) == '\"' || str.charAt(valStart) == '\'')) {
      valStart++;
    }
    int valEnd = valStart;
    while (valEnd < (int)str.length() && str.charAt(valEnd) != ',' && str.charAt(valEnd) != '}' && str.charAt(valEnd) != ']' && str.charAt(valEnd) != '\"' && str.charAt(valEnd) != '\'') {
      valEnd++;
    }
    return str.substring(valStart, valEnd);
  }

public:
  VisionAIParser() : _serial(nullptr) {}

  // Determine hazard priority for a given 4-digit class ID (1-50)
  // Supports both the 9 active deployed classes and the full 50-class Drishti catalog
  static uint8_t getPriority(uint16_t id) {
    // Priority 1: Critical safety hazards (immediate fall/burn/traffic collision risk)
    // - 1: Stairs (Fall Hazard)  - 2: Stairs Up (34/50)
    // - 3: Curb/Drop-off (50)    - 4: Pothole/Hole (34/50)
    // - 5: Low Overhead (50)     - 11: Red Light (34/50)
    // - 16: Cow/Large Animal     - 18: Motorcycle / Scooter (Critical Moving Traffic Hazard)
    // - 19: Car / Taxi / Auto    - 46: Stove/Burner (34/50)
    if (id == 1 || id == 2 || id == 3 || id == 4 || id == 5 || 
        id == 11 || id == 16 || id == 18 || id == 19 || id == 46) {
      return 1;
    }
    // Priority 2: Moving entities & navigation obstacles (pedestrians, animals, doors, poles, crosswalks, sockets)
    // - 6: Pole (34/active)      - 7: Wall (34/50)           - 8: Closed Door (34/active)
    // - 10: Crosswalk (34/50)    - 12: Green Light (34/50)   - 13: Person (34/active)
    // - 14: Dog (34/active)      - 17: Bicycle (34/50)       - 20: Bus (34/50)
    // - 21: Truck (50)           - 22: Auto Rickshaw (34/50) - 29: Elevator (34/50)
    // - 34: Medicine Bottle (50) - 45: Electrical Socket (34/50)
    if (id == 6 || id == 7 || id == 8 || id == 10 || id == 12 || 
        id == 13 || id == 14 || id == 17 || (id >= 20 && id <= 22) || 
        id == 29 || id == 34 || id == 45) {
      return 2;
    }
    // Priority 4: Low priority informational/clothing items
    // - 44: Clothes/Jacket (50)
    if (id == 44) return 4;

    // Priority 3: Stationary furniture & utility items (chair 23, table 26, bed 25, toilet 27, dustbin 30, phone 33, bottle 35, etc.)
    return 3;
  }

  // Get name from the raw 0-based SSCMA class index (as it comes from camera model)
  static const char* getTargetName(int rawIndex) {
    switch (rawIndex) {
      case 0: return "Car";
      case 1: return "Chair";
      case 2: return "Door";
      case 3: return "Motorcycle";
      case 4: return "Person";
      case 5: return "Pole";
      case 6: return "Stairs";
      case 7: return "Table";
      default: return "Unknown";
    }
  }

  // Get name from the mapped Drishti classId (1-50, used for MP3 track selection)
  static const char* getClassNameById(uint16_t classId) {
    switch (classId) {
      case 1:  return "Stairs";
      case 6:  return "Pole";
      case 8:  return "Door";
      case 13: return "Person";
      case 18: return "Motorcycle";
      case 19: return "Car";
      case 23: return "Chair";
      case 26: return "Table";
      // Extended catalog entries
      case 2:  return "Stairs Up";
      case 7:  return "Wall";
      case 11: return "Traffic Light";
      case 14: return "Dog";
      case 15: return "Cat";
      case 16: return "Cow";
      case 17: return "Bicycle";
      case 20: return "Bus";
      case 21: return "Truck";
      case 22: return "Auto Rickshaw";
      case 25: return "Bed";
      case 27: return "Toilet";
      case 29: return "Elevator";
      case 30: return "Dustbin";
      case 33: return "Phone";
      case 34: return "Medicine Bottle";
      case 35: return "Bottle";
      case 39: return "Book";
      case 40: return "Laptop";
      case 42: return "Backpack";
      case 44: return "Clothes";
      case 45: return "Electrical Socket";
      case 46: return "Stove";
      case 47: return "Refrigerator";
      default: return "Obstacle";
    }
  }

  // Parse raw target integer (strict mapping for Drishti 8-Class Model)
  static uint16_t parseTargetId(int rawTarget) {
    switch (rawTarget) {
      case 0: return 19; // car -> 0019.mp3
      case 1: return 23; // chair -> 0023.mp3
      case 2: return 8;  // door -> 0008.mp3
      case 3: return 18; // motorcycle -> 0018.mp3
      case 4: return 13; // person -> 0013.mp3
      case 5: return 6;  // pole -> 0006.mp3
      case 6: return 1;  // stairs -> 0001.mp3
      case 7: return 26; // table -> 0026.mp3
      case 56: return 23; // chair (COCO fallback)
      case 60: return 26; // dining table (COCO fallback)
      default:
        if (rawTarget >= 1 && rawTarget <= TOTAL_CLASSES) {
          return (uint16_t)rawTarget;
        }
        return 0;
    }
  }

  // Parse target string (e.g. "0013", "person", "chair", or raw index "0") into classId (1-50)
  static uint16_t parseTargetId(String targetStr) {
    targetStr.trim();
    targetStr.replace("\"", "");
    targetStr.replace("'", "");

    // Case 1: Direct 4-digit string ID like "0001" -> 1
    if (targetStr.length() == 4 && targetStr.toInt() > 0) {
      return (uint16_t)targetStr.toInt();
    }
    // Case 2: Active 8-Class Names & Catalog Fallbacks
    if (targetStr.equalsIgnoreCase("stairs") || targetStr.equalsIgnoreCase("stair") || targetStr.equalsIgnoreCase("staircase")) return 1;
    if (targetStr.equalsIgnoreCase("pole") || targetStr.equalsIgnoreCase("street post") || targetStr.equalsIgnoreCase("post") || targetStr.equalsIgnoreCase("pillar")) return 6;
    if (targetStr.equalsIgnoreCase("door") || targetStr.equalsIgnoreCase("closed door") || targetStr.equalsIgnoreCase("open door")) return 8;
    if (targetStr.equalsIgnoreCase("person") || targetStr.equalsIgnoreCase("pedestrian") || targetStr.equalsIgnoreCase("human")) return 13;
    if (targetStr.equalsIgnoreCase("motorcycle") || targetStr.equalsIgnoreCase("scooter") || targetStr.equalsIgnoreCase("motorbike") || targetStr.equalsIgnoreCase("bike")) return 18;
    if (targetStr.equalsIgnoreCase("car") || targetStr.equalsIgnoreCase("taxi") || targetStr.equalsIgnoreCase("automobile") || targetStr.equalsIgnoreCase("vehicle")) return 19;
    if (targetStr.equalsIgnoreCase("chair") || targetStr.equalsIgnoreCase("couch") || targetStr.equalsIgnoreCase("sofa") || targetStr.equalsIgnoreCase("bench")) return 23;
    if (targetStr.equalsIgnoreCase("table") || targetStr.equalsIgnoreCase("dining table") || targetStr.equalsIgnoreCase("desk")) return 26;

    // Additional Catalog Fallbacks
    if (targetStr.equalsIgnoreCase("traffic light")) return 11;
    if (targetStr.equalsIgnoreCase("cat")) return 15;
    if (targetStr.equalsIgnoreCase("cow")) return 16;
    if (targetStr.equalsIgnoreCase("bicycle")) return 17;
    if (targetStr.equalsIgnoreCase("bus") || targetStr.equalsIgnoreCase("truck")) return 20;
    if (targetStr.equalsIgnoreCase("bed")) return 25;
    if (targetStr.equalsIgnoreCase("toilet")) return 27;
    if (targetStr.equalsIgnoreCase("dustbin") || targetStr.equalsIgnoreCase("trash") || targetStr.equalsIgnoreCase("bin")) return 30;
    if (targetStr.equalsIgnoreCase("cell phone") || targetStr.equalsIgnoreCase("phone")) return 33;
    if (targetStr.equalsIgnoreCase("bottle") || targetStr.equalsIgnoreCase("cup")) return 35;
    if (targetStr.equalsIgnoreCase("backpack") || targetStr.equalsIgnoreCase("handbag") || targetStr.equalsIgnoreCase("suitcase")) return 42;
    if (targetStr.equalsIgnoreCase("laptop")) return 40;
    if (targetStr.equalsIgnoreCase("book")) return 39;
    if (targetStr.equalsIgnoreCase("microwave") || targetStr.equalsIgnoreCase("oven")) return 46;
    if (targetStr.equalsIgnoreCase("refrigerator")) return 47;
    if (targetStr.equalsIgnoreCase("stop sign")) return 7;

    // Case 3: 0-based integer index fallback (if SenseCraft outputs 0-33 instead of "0001")
    bool isNumber = (targetStr.length() > 0);
    for (unsigned int c = 0; c < targetStr.length(); c++) {
      if (!isDigit(targetStr.charAt(c))) {
        isNumber = false;
        break;
      }
    }
    if (isNumber) {
      return parseTargetId(targetStr.toInt());
    }

    return 0; // Unrecognized
  }

  // Arbitration rule: Highest Hazard Priority first, then Largest Bounding Box (closest)
  static void arbitrateCandidate(const Detection& cand, Detection& bestCandidate, bool& foundAny) {
    long candArea = (long)cand.w * cand.h;
    long bestArea = (long)bestCandidate.w * bestCandidate.h;

    if (!foundAny || cand.priority < bestCandidate.priority || 
       (cand.priority == bestCandidate.priority && candArea > bestArea)) {
      bestCandidate = cand;
      foundAny = true;
    }
  }

  void begin(HardwareSerial* serialPort, int rxPin, int txPin) {
    _serial = serialPort;
    _serial->begin(VISION_BAUDRATE, SERIAL_8N1, rxPin, txPin);
    _rxBuffer.reserve(512);
    DEBUG_PRINTLN("[VisionAI] Serial connection initialized.");
  }

  // Polls UART and parses incoming detections.
  // Returns true if a valid detection was parsed into 'outDetection'.
  bool update(Detection& outDetection) {
    while (_serial->available()) {
      char c = (char)_serial->read();
      if (c == '\n' || c == '\r') {
        if (_rxBuffer.length() > 5) {
          DEBUG_PRINTF("[Grove UART] %s\n", _rxBuffer.c_str());
          bool found = parseLine(_rxBuffer, outDetection);
          _rxBuffer = "";
          if (found) {
            return true;
          }
        } else {
          _rxBuffer = "";
        }
      } else {
        if (_rxBuffer.length() < 510) {
          _rxBuffer += c;
        } else {
          _rxBuffer = ""; // Overflow guard
        }
      }
    }
    return false;
  }

  // Parses Grove Vision AI V2 packets and chooses the HIGHEST PRIORITY & NEAREST object
  bool parseLine(const String& line, Detection& outDet) {
    // -------------------------------------------------------------
    // Format 1: Edge Impulse Console Format
    // e.g.: "    person (0.85) [ x: 24, y: 32, width: 40, height: 50 ]"
    // -------------------------------------------------------------
    int bracketPos = line.indexOf("[ x:");
    if (bracketPos == -1) bracketPos = line.indexOf("[x:");
    if (bracketPos != -1) {
      int parenStart = line.indexOf('(');
      if (parenStart != -1 && parenStart < bracketPos) {
        String labelStr = line.substring(0, parenStart);
        labelStr.trim();
        int parenEnd = line.indexOf(')', parenStart);
        String scoreStr = (parenEnd != -1) ? line.substring(parenStart + 1, parenEnd) : "0";
        scoreStr.trim();
        int score = (int)(scoreStr.toFloat() * 100.0f);
        if (score > 100) score = scoreStr.toInt();

        if (score >= MIN_CONFIDENCE_THRESHOLD && labelStr.length() > 0) {
          uint16_t cId = parseTargetId(labelStr);
          if (cId >= 1 && cId <= TOTAL_CLASSES) {
            outDet.classId = cId;
            outDet.confidence = (uint8_t)score;
            outDet.x = extractField(line, "x").toInt();
            outDet.y = extractField(line, "y").toInt();
            outDet.w = extractField(line, "width").toInt();
            outDet.h = extractField(line, "height").toInt();
            outDet.priority = getPriority(outDet.classId);
            return true;
          }
        }
      }
    }

    // -------------------------------------------------------------
    // Format 2: Direct Single-Object JSON Format
    // e.g.: {"label": "person", "value": 0.85, "x": 24, "y": 32, "width": 40, "height": 50}
    // -------------------------------------------------------------
    if (line.indexOf("\"label\"") != -1 && line.indexOf("boxes") == -1) {
      String labelStr = extractField(line, "label");
      String scoreStr = extractField(line, "value");
      if (scoreStr.length() == 0) scoreStr = extractField(line, "score");
      if (scoreStr.length() == 0) scoreStr = extractField(line, "confidence");

      int score = 0;
      if (scoreStr.indexOf('.') != -1) {
        score = (int)(scoreStr.toFloat() * 100.0f);
      } else {
        score = scoreStr.toInt();
      }

      if (score >= MIN_CONFIDENCE_THRESHOLD && labelStr.length() > 0) {
        uint16_t cId = parseTargetId(labelStr);
        if (cId >= 1 && cId <= TOTAL_CLASSES) {
          outDet.classId = cId;
          outDet.confidence = (uint8_t)score;
          outDet.x = extractField(line, "x").toInt();
          outDet.y = extractField(line, "y").toInt();
          String wStr = extractField(line, "width");
          if (wStr.length() == 0) wStr = extractField(line, "w");
          outDet.w = wStr.toInt();
          String hStr = extractField(line, "height");
          if (hStr.length() == 0) hStr = extractField(line, "h");
          outDet.h = hStr.toInt();
          outDet.priority = getPriority(outDet.classId);
          return true;
        }
      }
    }

    // -------------------------------------------------------------
    // Format 3: Seeed SSCMA Nested Array Format
    // Packet: {"type":1,"name":"INVOKE","code":0,"data":{"count":N,"perf":[p,p,p],
    //          "boxes":[[x,y,w,h,score,target],...],"resolution":[W,H]}}
    // score=0-100 int, target=0-based class index (int). Primary SSCMA format.
    // -------------------------------------------------------------
    int boxesPos = line.indexOf("\"boxes\"");
    if (boxesPos == -1) boxesPos = line.indexOf("boxes");
    if (boxesPos == -1) return false;

    Detection bestCandidate;
    bestCandidate.classId = 0;
    bestCandidate.priority = 255;
    bestCandidate.w = 0;
    bestCandidate.h = 0;
    bestCandidate.confidence = 0;
    bool foundAny = false;

    // Find opening '[' of the boxes value
    int boxesArrayStart = line.indexOf('[', boxesPos);
    if (boxesArrayStart == -1) return false;

    // Outer array end: stop before "resolution" key
    int resPos = line.indexOf("resolution", boxesPos);
    int outerEnd = (resPos != -1) ? line.lastIndexOf(']', resPos) : (int)line.length();

    // Detect format: '[' inside = nested arrays, '{' inside = dict objects
    int nextBracket = line.indexOf('[', boxesArrayStart + 1);
    int nextBrace   = line.indexOf('{', boxesArrayStart + 1);
    if (nextBracket > outerEnd) nextBracket = -1;
    if (nextBrace   > outerEnd) nextBrace   = -1;

    // ---- Format A: boxes=[{target,score,x,y,w,h},...] ----
    if (nextBrace != -1 && (nextBracket == -1 || nextBrace < nextBracket)) {
      int objStart = nextBrace;
      while (objStart != -1 && objStart < outerEnd) {
        int objEnd = line.indexOf('}', objStart);
        if (objEnd == -1 || objEnd > outerEnd) break;
        String chunk = line.substring(objStart, objEnd + 1);
        String targetStr = extractField(chunk, "target");
        if (targetStr.length() == 0) targetStr = extractField(chunk, "label");
        String scoreStr = extractField(chunk, "score");
        if (scoreStr.length() == 0) scoreStr = extractField(chunk, "confidence");
        if (scoreStr.length() == 0) scoreStr = extractField(chunk, "value");
        int score = (scoreStr.indexOf('.') != -1) ? (int)(scoreStr.toFloat()*100.0f) : scoreStr.toInt();
        if (score >= MIN_CONFIDENCE_THRESHOLD && targetStr.length() > 0) {
          uint16_t cId = parseTargetId(targetStr);
          if (cId >= 1 && cId <= TOTAL_CLASSES) {
            Detection cand;
            cand.classId = cId;
            cand.confidence = (uint8_t)score;
            cand.x = extractField(chunk, "x").toInt();
            cand.y = extractField(chunk, "y").toInt();
            String wStr = extractField(chunk, "w"); if (wStr.length()==0) wStr = extractField(chunk, "width");
            String hStr = extractField(chunk, "h"); if (hStr.length()==0) hStr = extractField(chunk, "height");
            cand.w = wStr.toInt(); cand.h = hStr.toInt();
            cand.priority = getPriority(cand.classId);
            arbitrateCandidate(cand, bestCandidate, foundAny);
          }
        }
        objStart = line.indexOf('{', objEnd + 1);
      }
    }
    // ---- Format B: boxes=[[x,y,w,h,score,target],...] (PRIMARY SSCMA format) ----
    else {
      int innerStart = line.indexOf('[', boxesArrayStart + 1);
      while (innerStart != -1 && innerStart < outerEnd) {
        int innerEnd = line.indexOf(']', innerStart + 1);
        if (innerEnd == -1) break;
        String content = line.substring(innerStart + 1, innerEnd);
        content.trim();
        if (content.length() == 0) break; // empty boxes = no objects detected

        // Parse: x, y, w, h, score, target_index (6 comma-separated ints)
        int vals[5] = {0};
        int targetRaw = -1;
        int tokenIdx = 0;
        int segStart = 0;
        for (int i = 0; i <= (int)content.length() && tokenIdx <= 5; i++) {
          if (i == (int)content.length() || content.charAt(i) == ',') {
            String tok = content.substring(segStart, i);
            tok.trim(); tok.replace("\"",""); tok.replace("'","");
            if (tokenIdx < 5) vals[tokenIdx] = tok.toInt();
            else              targetRaw = tok.toInt();
            tokenIdx++;
            segStart = i + 1;
          }
        }
        // vals[0..4]=x,y,w,h,score  targetRaw=0-based class index
        if (tokenIdx >= 6 && targetRaw >= 0 && vals[4] >= MIN_CONFIDENCE_THRESHOLD) {
          uint16_t cId = parseTargetId(targetRaw);
          if (cId >= 1 && cId <= TOTAL_CLASSES) {
            Detection cand;
            cand.classId   = cId;
            cand.confidence = (uint8_t)vals[4];
            cand.x = vals[0]; cand.y = vals[1];
            cand.w = vals[2]; cand.h = vals[3];
            cand.priority  = getPriority(cand.classId);
            DEBUG_PRINTF("[Parser] Box cls=%d->id=%d conf=%d%% (%d,%d,%d,%d)\n",
                         targetRaw, cId, vals[4], vals[0], vals[1], vals[2], vals[3]);
            arbitrateCandidate(cand, bestCandidate, foundAny);
          }
        }
        innerStart = line.indexOf('[', innerEnd + 1);
      }
    }

    if (foundAny) {
      outDet = bestCandidate;
      return true;
    }
    return false;
  }
};

#endif // VISION_AI_PARSER_H
