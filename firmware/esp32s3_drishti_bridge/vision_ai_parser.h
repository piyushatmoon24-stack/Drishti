#ifndef VISION_AI_PARSER_H
#define VISION_AI_PARSER_H

#include <Arduino.h>
#include "config.h"

struct Detection {
  uint16_t classId;
  uint8_t confidence;
  int16_t x;
  int16_t y;
  int16_t w;
  int16_t h;
  uint8_t priority;
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
    while (valStart < (int)str.length() && 
          (str.charAt(valStart) == ' ' || str.charAt(valStart) == '\"' || str.charAt(valStart) == '\'')) {
      valStart++;
    }

    int valEnd = valStart;
    while (valEnd < (int)str.length() && 
           str.charAt(valEnd) != ',' && str.charAt(valEnd) != '}' && 
           str.charAt(valEnd) != ']' && str.charAt(valEnd) != '\"' && str.charAt(valEnd) != '\'') {
      valEnd++;
    }

    return str.substring(valStart, valEnd);
  }

public:
  VisionAIParser() : _serial(nullptr) {}

  static uint8_t getPriority(uint16_t id) {
    // Priority 1: Critical fall & moving vehicle collision hazards
    if (id == 1 || id == 18 || id == 19) {
      return 1;
    }
    // Priority 2: Navigational obstacles (people, doors, posts)
    if (id == 6 || id == 8 || id == 13) {
      return 2;
    }
    // Priority 3: Stationary indoor obstacles (furniture)
    return 3;
  }

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
      default: return "Obstacle";
    }
  }

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
      default:
        // Reserved for future 50-class catalog expansion
        return "Extended Catalog Item";
    }
  }

  static uint16_t parseTargetId(int rawTarget) {
    switch (rawTarget) {
      case 0: return 19; // car        -> /MP3/0019.mp3
      case 1: return 23; // chair      -> /MP3/0023.mp3
      case 2: return 8;  // door       -> /MP3/0008.mp3
      case 3: return 18; // motorcycle -> /MP3/0018.mp3
      case 4: return 13; // person     -> /MP3/0013.mp3
      case 5: return 6;  // pole       -> /MP3/0006.mp3
      case 6: return 1;  // stairs     -> /MP3/0001.mp3
      case 7: return 26; // table      -> /MP3/0026.mp3
      default:
        // Fallback pass-through if model outputs direct catalog ID
        if (rawTarget >= 1 && rawTarget <= CATALOG_RESERVE_CLASSES) {
          return (uint16_t)rawTarget;
        }
        return 0;
    }
  }

  static uint16_t parseTargetId(String targetStr) {
    targetStr.trim();
    targetStr.replace("\"", "");
    targetStr.replace("'", "");

    if (targetStr.length() == 4 && targetStr.toInt() > 0) {
      return (uint16_t)targetStr.toInt();
    }

    if (targetStr.equalsIgnoreCase("stairs")) return 1;
    if (targetStr.equalsIgnoreCase("pole")) return 6;
    if (targetStr.equalsIgnoreCase("door")) return 8;
    if (targetStr.equalsIgnoreCase("person")) return 13;
    if (targetStr.equalsIgnoreCase("motorcycle")) return 18;
    if (targetStr.equalsIgnoreCase("car")) return 19;
    if (targetStr.equalsIgnoreCase("chair")) return 23;
    if (targetStr.equalsIgnoreCase("table")) return 26;

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

    return 0;
  }

  static void arbitrateCandidate(const Detection& cand, Detection& bestCandidate, bool& foundAny) {
    long candArea = (long)cand.w * cand.h;
    long bestArea = (long)bestCandidate.w * bestCandidate.h;

    // Highest safety priority first; if equal priority, pick largest bounding area (closest)
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
  }

  bool update(Detection& outDetection) {
    while (_serial && _serial->available()) {
      char c = (char)_serial->read();
      if (c == '\n' || c == '\r') {
        if (_rxBuffer.length() > 5) {
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
          _rxBuffer = "";
        }
      }
    }
    return false;
  }

  bool parseLine(const String& line, Detection& outDet) {
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

    int boxesArrayStart = line.indexOf('[', boxesPos);
    if (boxesArrayStart == -1) return false;

    int resPos = line.indexOf("resolution", boxesPos);
    int outerEnd = (resPos != -1) ? line.lastIndexOf(']', resPos) : (int)line.length();

    int nextBracket = line.indexOf('[', boxesArrayStart + 1);
    int nextBrace   = line.indexOf('{', boxesArrayStart + 1);
    if (nextBracket > outerEnd) nextBracket = -1;
    if (nextBrace   > outerEnd) nextBrace   = -1;

    // Dict format: boxes = [{target, score, x, y, w, h}, ...]
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

        int score = (scoreStr.indexOf('.') != -1) ? (int)(scoreStr.toFloat() * 100.0f) : scoreStr.toInt();

        if (score >= MIN_CONFIDENCE_THRESHOLD && targetStr.length() > 0) {
          uint16_t cId = parseTargetId(targetStr);
          if (cId > 0 && cId <= CATALOG_RESERVE_CLASSES) {
            Detection cand;
            cand.classId = cId;
            cand.confidence = (uint8_t)score;
            cand.x = extractField(chunk, "x").toInt();
            cand.y = extractField(chunk, "y").toInt();
            String wStr = extractField(chunk, "w");
            if (wStr.length() == 0) wStr = extractField(chunk, "width");
            String hStr = extractField(chunk, "h");
            if (hStr.length() == 0) hStr = extractField(chunk, "height");
            cand.w = wStr.toInt();
            cand.h = hStr.toInt();
            cand.priority = getPriority(cand.classId);
            arbitrateCandidate(cand, bestCandidate, foundAny);
          }
        }
        objStart = line.indexOf('{', objEnd + 1);
      }
    }
    // Nested array format: boxes = [[x, y, w, h, score, target], ...]
    else {
      int innerStart = line.indexOf('[', boxesArrayStart + 1);
      while (innerStart != -1 && innerStart < outerEnd) {
        int innerEnd = line.indexOf(']', innerStart + 1);
        if (innerEnd == -1) break;

        String content = line.substring(innerStart + 1, innerEnd);
        content.trim();
        if (content.length() == 0) break;

        int vals[5] = {0};
        int targetRaw = -1;
        int tokenIdx = 0;
        int segStart = 0;

        for (int i = 0; i <= (int)content.length() && tokenIdx <= 5; i++) {
          if (i == (int)content.length() || content.charAt(i) == ',') {
            String tok = content.substring(segStart, i);
            tok.trim();
            tok.replace("\"", "");
            tok.replace("'", "");
            if (tokenIdx < 5) vals[tokenIdx] = tok.toInt();
            else              targetRaw = tok.toInt();
            tokenIdx++;
            segStart = i + 1;
          }
        }

        if (tokenIdx >= 6 && targetRaw >= 0 && vals[4] >= MIN_CONFIDENCE_THRESHOLD) {
          uint16_t cId = parseTargetId(targetRaw);
          if (cId > 0 && cId <= CATALOG_RESERVE_CLASSES) {
            Detection cand;
            cand.classId = cId;
            cand.confidence = (uint8_t)vals[4];
            cand.x = vals[0];
            cand.y = vals[1];
            cand.w = vals[2];
            cand.h = vals[3];
            cand.priority = getPriority(cand.classId);
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
