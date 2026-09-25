#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <esp_task_wdt.h>
#include "control.h"
#include "ui.h"
#if __has_include("secrets.h")
#include "secrets.h"
#else
#error "Copy include/secrets.example.h to include/secrets.h and set unique passwords."
#endif

constexpr int ADC_PIN=34, SERVO_PIN=18, GREEN=25, AMBER=26, RED=32, STOP_PIN=27;
// Commission with horn disconnected. HS-311 nominal +/-60 deg is 900..2100 us.
constexpr int CLOSED_US=1050, OPEN_US=1950, PWM_CHANNEL=0;
constexpr size_t HISTORY_N=1440, EVENT_N=32;
struct Point { uint64_t sec; float pct,mv; bool valid,open; };
struct Event { uint64_t sec; String message; };
soil::Controller ctl;
Point history[HISTORY_N]; Event events[EVENT_N];
size_t histHead=0,histCount=0,eventHead=0,eventCount=0;
uint64_t upMs=0; uint32_t previousMs=0;
SemaphoreHandle_t lock;
WebServer server(80);
String csrf, bootId;
bool storageOK=true, controlOK=false;
void event(const String& s) { events[eventHead]={upMs/1000,s}; eventHead=(eventHead+1)%EVENT_N; if(eventCount<EVENT_N) ++eventCount; }
void pwm(bool open) { ledcWrite(PWM_CHANNEL, uint32_t((open?OPEN_US:CLOSED_US)*65535UL/20000UL)); }
void controlTask(void*) {
  esp_task_wdt_add(nullptr);
  uint32_t sampleAt=millis()-250, logAt=millis()-60000;
  bool wasOpen=false, wasArmed=false; soil::Fault wasFault=soil::Fault::None; int zone=-1;
  for(;;) {
    uint32_t now=millis();
    bool takeSample=uint32_t(now-sampleAt)>=250;
    float value=0;
    if(takeSample) { for(int i=0;i<16;++i) value+=analogReadMilliVolts(ADC_PIN); value/=16; sampleAt=now; }
    xSemaphoreTake(lock,portMAX_DELAY);
    now=millis(); // Commands may have changed timestamps while ADC sampling ran.
    upMs+=uint32_t(now-previousMs); previousMs=now;
    if(takeSample) ctl.sample(value,now);
    ctl.tick(now,digitalRead(STOP_PIN)==HIGH);
    pwm(ctl.opening);
    digitalWrite(GREEN,ctl.armed?HIGH:((now/1000)%2));
    digitalWrite(AMBER,ctl.opening);
    digitalWrite(RED,ctl.fault!=soil::Fault::None || !ctl.cfg.calibrated || !storageOK);
    if(ctl.opening!=wasOpen) { event(ctl.opening?"Valve commanded OPEN":"Valve commanded CLOSED"); wasOpen=ctl.opening; }
    if(ctl.armed!=wasArmed) { event(ctl.armed?"Automatic watering armed":"Automatic watering disarmed"); wasArmed=ctl.armed; }
    if(ctl.fault!=wasFault) { event(ctl.fault==soil::Fault::None?"Fault reset":String("FAULT: ")+soil::faultName(ctl.fault)); wasFault=ctl.fault; }
    if(ctl.good && ctl.cfg.calibrated) {
      int next=ctl.moisture<ctl.cfg.low?0:(ctl.moisture>=ctl.cfg.high?2:1);
      if(next!=zone) { event(next==0?"LOW moisture threshold crossed":next==2?"HIGH moisture threshold reached":"Moisture in target band"); zone=next; }
    }
    if(uint32_t(now-logAt)>=60000) {
      history[histHead]={upMs/1000,ctl.moisture,ctl.mv,ctl.good&&ctl.cfg.calibrated,ctl.opening};
      histHead=(histHead+1)%HISTORY_N; if(histCount<HISTORY_N) ++histCount; logAt=now;
    }
    xSemaphoreGive(lock);
    esp_task_wdt_reset();
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}
bool auth(bool mutation=false) {
  if(!server.authenticate("admin",ADMIN_PASSWORD)) { server.requestAuthentication(); return false; }
  server.sendHeader("Cache-Control","no-store");
  server.sendHeader("X-Content-Type-Options","nosniff");
  if(mutation && server.header("X-Control-Token")!=csrf) { server.send(403,"text/plain","Invalid control token"); return false; }
  return true;
}
String number64(uint64_t n) { char b[24]; snprintf(b,sizeof(b),"%llu",(unsigned long long)n); return String(b); }
void status() {
  if(!auth()) return;
  xSemaphoreTake(lock,portMAX_DELAY);
  auto c=ctl; auto sec=upMs/1000;
  String ev="[";
  for(size_t i=0;i<eventCount;++i) {auto& e=events[(eventHead+EVENT_N-eventCount+i)%EVENT_N]; if(i) ev+=","; ev+="{\"s\":"+number64(e.sec)+",\"message\":\""+e.message+"\"}";}
  ev+="]";
  xSemaphoreGive(lock);
  String out="{\"boot\":\""+bootId+"\",\"token\":\""+csrf+"\",\"s\":"+number64(sec);
  out+=",\"moisture\":"+String(c.moisture,1)+",\"mv\":"+String(c.mv,1);
  out+=",\"valid\":"+String(c.good&&c.cfg.calibrated?"true":"false")+",\"armed\":"+String(c.armed?"true":"false");
  out+=",\"open\":"+String(c.opening?"true":"false")+",\"fault\":\""+soil::faultName(c.fault)+"\"";
  out+=",\"calibrated\":"+String(c.cfg.calibrated?"true":"false")+",\"storageOK\":"+String(storageOK?"true":"false");
  out+=",\"low\":"+String(c.cfg.low)+",\"high\":"+String(c.cfg.high)+",\"dryMv\":"+String(c.cfg.dryMv)+",\"wetMv\":"+String(c.cfg.wetMv);
  out+=",\"reservedSeconds\":"+String(c.reserved/1000)+",\"events\":"+ev+"}";
  server.send(200,"application/json",out);
}
void historyGet() {
  if(!auth()) return;
  // Copy under the lock; network transmission never holds the control lock.
  Point* copy=new(std::nothrow) Point[HISTORY_N];
  if(!copy) {server.send(503,"text/plain","Memory busy");return;}
  xSemaphoreTake(lock,portMAX_DELAY); size_t count=histCount;
  for(size_t i=0;i<count;++i) copy[i]=history[(histHead+HISTORY_N-count+i)%HISTORY_N];
  xSemaphoreGive(lock);
  server.setContentLength(CONTENT_LENGTH_UNKNOWN); server.send(200,"application/json",""); server.sendContent("[");
  String chunk; chunk.reserve(1600);
  for(size_t i=0;i<count;++i) {
    if(i) chunk+=",";
    chunk+="{\"s\":"+number64(copy[i].sec)+",\"pct\":"+(copy[i].valid?String(copy[i].pct,1):String("null"));
    chunk+=",\"mv\":"+String(copy[i].mv,1)+",\"open\":"+String(copy[i].open?"true":"false")+"}";
    if(chunk.length()>1200) {server.sendContent(chunk);chunk="";}
  }
  chunk+="]"; server.sendContent(chunk); server.sendContent(""); delete[] copy;
}
bool parseNumber(const char* key,float& v) {
  if(!server.hasArg(key)) return false;
  String s=server.arg(key); char* end=nullptr; v=strtof(s.c_str(),&end);
  return end!=s.c_str() && *end=='\0' && isfinite(v);
}
void configure() {
  if(!auth(true)) return;
  soil::Config next;
  if(!parseNumber("dryMv",next.dryMv)||!parseNumber("wetMv",next.wetMv)||!parseNumber("low",next.low)||!parseNumber("high",next.high)||!next.valid()) {
    server.send(400,"text/plain","Require 100 <= wet < dry <= 2150 mV; span >= 200; 5 <= low < high <= 95; gap >= 5"); return;
  }
  next.calibrated=true;
  xSemaphoreTake(lock,portMAX_DELAY);
  bool busy=ctl.opening||ctl.armed;
  xSemaphoreGive(lock);
  if(busy) {server.send(409,"text/plain","Disarm and close before changing calibration");return;}
  Preferences p;
  bool ok=p.begin("soil",false);
  if(ok) {ok=p.putBytes("config",&next,sizeof(next))==sizeof(next);p.end();}
  xSemaphoreTake(lock,portMAX_DELAY); storageOK=ok; xSemaphoreGive(lock);
  if(!ok) {server.send(500,"text/plain","Configuration persistence failed");return;}
  xSemaphoreTake(lock,portMAX_DELAY); ctl.cfg=next; ctl.good=false; ctl.goodCount=0; histCount=0;histHead=0;
  event("Calibration saved; history cleared; remains disarmed"); xSemaphoreGive(lock);
  server.send(200,"text/plain","Saved. Wait for fresh samples before arming.");
}
void command() {
  if(!auth(true)) return;
  String action=server.arg("action"); bool ok=false;
  xSemaphoreTake(lock,portMAX_DELAY); uint32_t now=millis();
  // Recheck the physical input synchronously before accepting a command.
  ctl.tick(now,digitalRead(STOP_PIN)==HIGH);
  if(action=="close") {ctl.disarm(now);ok=true;}
  else if(action=="arm") ok=storageOK&&ctl.arm(now);
  else if(action=="pulse") ok=storageOK&&!ctl.armed&&ctl.manual(now);
  else if(action=="reset") ok=ctl.reset(now);
  if(ok) event("UI command: "+action);
  xSemaphoreGive(lock);
  server.send(ok?200:409,"text/plain",ok?"Command accepted":"Blocked: check calibration, fault, STOP loop, soak timer, budget, and mode");
}
void setup() {
  Serial.begin(115200);
  pinMode(STOP_PIN,INPUT_PULLUP);
  for(int pin:{GREEN,AMBER,RED}) {pinMode(pin,OUTPUT);digitalWrite(pin,LOW);}
  pinMode(SERVO_PIN,OUTPUT);digitalWrite(SERVO_PIN,LOW);
  ledcSetup(PWM_CHANNEL,50,16);ledcAttachPin(SERVO_PIN,PWM_CHANNEL);pwm(false);
  analogReadResolution(12);analogSetPinAttenuation(ADC_PIN,ADC_11db);
  lock=xSemaphoreCreateMutex(); if(!lock) {digitalWrite(RED,HIGH);return;}
  Preferences p;
  if(p.begin("soil",true)) {
    soil::Config saved;
    if(p.getBytesLength("config")==sizeof(saved) && p.getBytes("config",&saved,sizeof(saved))==sizeof(saved) && saved.valid()) ctl.cfg=saved;
    p.end();
  }
  ctl.closedAt=millis(); previousMs=millis();
  event("Boot: CLOSED command; automatic watering disarmed");
  esp_task_wdt_init(3,true);
  controlOK=xTaskCreatePinnedToCore(controlTask,"control",6144,nullptr,3,nullptr,1)==pdPASS;
  if(!controlOK) {digitalWrite(RED,HIGH);return;}
  if(strlen(AP_PASSWORD)<12 || strlen(ADMIN_PASSWORD)<12 || strstr(AP_PASSWORD,"replace-") || strstr(ADMIN_PASSWORD,"replace-")) {
    Serial.println("Set unique passwords, >=12 characters. Network disabled."); return;
  }
  WiFi.mode(WIFI_AP);
  String ssid="SoilValve-"+String(uint32_t(ESP.getEfuseMac()),HEX);
  if(!WiFi.softAP(ssid.c_str(),AP_PASSWORD)) {Serial.println("AP failed; control remains disarmed");return;}
  bootId=String(esp_random(),HEX); csrf=String(esp_random(),HEX)+String(esp_random(),HEX)+String(esp_random(),HEX)+String(esp_random(),HEX);
  const char* headers[]={"X-Control-Token"};server.collectHeaders(headers,1);
  server.on("/",HTTP_GET,[]{if(auth())server.send_P(200,"text/html",UI);});
  server.on("/api/status",HTTP_GET,status); server.on("/api/history",HTTP_GET,historyGet);
  server.on("/api/config",HTTP_POST,configure);server.on("/api/command",HTTP_POST,command);
  server.onNotFound([]{server.send(404,"text/plain","Not found");});server.begin();
  Serial.printf("Connect to %s, open http://192.168.4.1 (admin).\n",ssid.c_str());
}
void loop() {if(controlOK)server.handleClient();delay(2);}
