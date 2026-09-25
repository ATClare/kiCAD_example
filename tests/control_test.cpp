#include "../firmware/include/control.h"
#include <assert.h>
#include <stdio.h>
#include <limits>
using namespace soil;
void samples(Controller& c,uint32_t t,float v=1500) {for(int i=0;i<5;i++)c.sample(v,t);}
Controller ready(uint32_t t=60000) {Controller c;c.cfg.calibrated=true;samples(c,t);c.tick(t,false);return c;}
int main(){
  {Controller c;samples(c,60000);assert(!c.arm(60000));assert(!c.manual(60000));}
  {auto c=ready();assert(c.arm(60000));c.tick(60000,false);assert(c.opening);samples(c,65000);c.tick(65000,false);assert(!c.opening);samples(c,124999);c.tick(124999,false);assert(!c.opening);samples(c,125000);c.tick(125000,false);assert(c.opening);}
  {auto c=ready();assert(c.manual(60000));c.tick(60020,true);assert(!c.opening&&!c.armed&&c.fault==Fault::Interlock);assert(!c.reset(60020));c.tick(60040,false);assert(c.reset(60040));assert(!c.armed);}
  {auto c=ready();assert(c.manual(60000));c.sample(0,60250);c.tick(60250,false);assert(!c.opening);c.sample(0,60500);c.sample(0,60750);assert(c.fault==Fault::Sensor);assert(!c.arm(60750));}
  {auto c=ready();c.manual(60000);c.tick(62001,false);assert(c.fault==Fault::Stale&&!c.opening);}
  {auto c=ready();c.arm(60000);c.tick(60000,false);samples(c,60250,850);for(int i=0;i<12;++i)c.sample(850,60250);c.tick(60250,false);assert(!c.opening&&!c.demand);}
  {auto c=ready();for(int i=0;i<6;++i){uint32_t t=60000+i*65000;samples(c,t);assert(c.manual(t));samples(c,t+5000);c.tick(t+5000,false);}samples(c,450000);assert(!c.manual(450000));assert(c.fault==Fault::Budget);assert(!c.reset(450000));samples(c,3985000);assert(c.reset(3985000));assert(c.manual(3985000));}
  {auto c=ready();c.closedAt=0xffff0000U;samples(c,0xffffff00U);assert(c.manual(0xffffff00U));samples(c,0x00001300U);c.tick(0x00001300U,false);assert(!c.opening);}
  {Config c;c.wetMv=c.dryMv;assert(!c.valid());c=Config();c.low=c.high;assert(!c.valid());c=Config();c.dryMv=std::numeric_limits<float>::quiet_NaN();assert(!c.valid());}
  {auto c=ready();c.manual(60000);c.disarm(60001);assert(!c.opening&&!c.armed);assert(!c.manual(60002));}
  puts("PASS: calibration, hysteresis, pulse limit, soak, STOP, sensor faults, staleness, budget, rollover, config, disarm");
}
