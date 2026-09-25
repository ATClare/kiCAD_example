#pragma once
#include <stdint.h>
#include <math.h>

namespace soil {
enum class Fault { None, Interlock, Sensor, Stale, Budget };
struct Config {
  uint32_t version = 1;
  float dryMv = 1600, wetMv = 850;
  float low = 30, high = 55;
  bool calibrated = false;
  bool valid() const {
    return version == 1 && isfinite(dryMv) && isfinite(wetMv) && isfinite(low) && isfinite(high)
      && wetMv >= 100 && dryMv <= 2150 && dryMv-wetMv >= 200
      && low >= 5 && high <= 95 && high-low >= 5;
  }
};
struct Controller {
  static constexpr uint32_t PULSE_MS=5000, SOAK_MS=60000, WINDOW_MS=3600000, BUDGET_MS=30000;
  Config cfg;
  bool armed=false, opening=false, demand=false, good=false, interlock=false, seen=false;
  Fault fault=Fault::None;
  float mv=0, moisture=0;
  uint8_t goodCount=0, badCount=0;
  uint32_t lastSample=0, openedAt=0, closedAt=0, windowAt=0, reserved=0;
  static uint32_t elapsed(uint32_t now,uint32_t then) { return now-then; }
  void close(uint32_t now) { if(opening) closedAt=now; opening=false; }
  void trip(Fault f,uint32_t now) { fault=f; armed=false; demand=false; close(now); }
  void sample(float value,uint32_t now) {
    seen=true; lastSample=now;
    if(!isfinite(value)||value<100||value>2150) {
      good=false; goodCount=0; if(badCount<3) ++badCount;
      if(badCount>=3) trip(Fault::Sensor,now);
      return;
    }
    badCount=0;
    mv=goodCount==0?value:0.25f*value+0.75f*mv;
    if(goodCount<5) ++goodCount;
    good=goodCount>=5;
    moisture=fmaxf(0,fminf(100,100*(cfg.dryMv-mv)/(cfg.dryMv-cfg.wetMv)));
  }
  bool ready(uint32_t now) const {
    return cfg.valid() && cfg.calibrated && good && seen && !interlock && elapsed(now,lastSample)<=2000;
  }
  bool arm(uint32_t now) {
    if(fault!=Fault::None || !ready(now)) return false;
    armed=true; return true;
  }
  void disarm(uint32_t now) { armed=false; demand=false; close(now); }
  bool reset(uint32_t now) {
    if(!good || interlock || !seen || elapsed(now,lastSample)>2000) return false;
    if(fault==Fault::Budget && elapsed(now,windowAt)<WINDOW_MS) return false;
    fault=Fault::None; disarm(now); return true;
  }
  bool start(uint32_t now) {
    if(opening || fault!=Fault::None || !ready(now) || elapsed(now,closedAt)<SOAK_MS) return false;
    // A conservative rolling lockout: restart the hour on every accepted pulse.
    // Reservations clear only after a full hour with no pulse starts.
    if(elapsed(now,windowAt)>=WINDOW_MS) reserved=0;
    if(reserved+PULSE_MS>BUDGET_MS) { trip(Fault::Budget,now); return false; }
    reserved+=PULSE_MS; windowAt=now; opening=true; openedAt=now; return true;
  }
  bool manual(uint32_t now) { return start(now); }
  void tick(uint32_t now,bool loopOpen) {
    interlock=loopOpen;
    if(interlock) { trip(Fault::Interlock,now); return; }
    if(seen && elapsed(now,lastSample)>2000) { trip(Fault::Stale,now); return; }
    if(opening && (!good || fault!=Fault::None || elapsed(now,openedAt)>=PULSE_MS)) close(now);
    if(!armed || fault!=Fault::None || !ready(now)) return;
    if(moisture>=cfg.high) { demand=false; close(now); }
    else if(moisture<cfg.low) demand=true;
    if(demand && !opening) start(now);
  }
};
inline const char* faultName(Fault f) {
  switch(f) {case Fault::Interlock:return "STOP loop open";case Fault::Sensor:return "Sensor out of range";
  case Fault::Stale:return "Sensor samples stale";case Fault::Budget:return "Watering budget exhausted";default:return "";}
}
}
