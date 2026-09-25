"""Generate a self-contained KiCad schematic; no third-party symbol library needed."""
from pathlib import Path
import uuid, json, csv
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'electronics'; OUT.mkdir(exist_ok=True)
uid=lambda:str(uuid.uuid4())
def q(s): return json.dumps(str(s),ensure_ascii=False)
def effect(size=1.27,other=''): return f'(effects (font (size {size} {size})) {other})'
libs={}; components=[]; items=[]; rootid=uid(); nets={}
def library(name,pins,shape='box',width=12.7,height=None):
    h=height or max(5.08,len(pins)*1.27)
    if shape=='resistor': drawing='(rectangle (start -2.54 -1.016) (end 2.54 1.016) (stroke (width 0.254) (type default)) (fill (type none)))'
    elif shape=='capacitor': drawing=''.join(f'(polyline (pts (xy {x} -2.54) (xy {x} 2.54)) (stroke (width 0.254) (type default)) (fill (type none)))' for x in [-.635,.635])
    elif shape=='led': drawing='(polyline (pts (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27) (xy -1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 0 1.8) (xy 1.8 3.6) (xy 0.8 3.6) (xy 1.8 3.6) (xy 1.8 2.6)) (stroke (width 0.15) (type default)) (fill (type none)))'
    elif shape=='switch': drawing='(polyline (pts (xy -2.54 0) (xy 1.8 2)) (stroke (width 0.254) (type default)) (fill (type none))) (circle (center 2.54 0) (radius 0.4) (stroke (width 0.15) (type default)) (fill (type none)))'
    else: drawing=f'(rectangle (start {-width/2} {-h/2}) (end {width/2} {h/2}) (stroke (width 0.254) (type default)) (fill (type background)))'
    ps=[]
    for num,label,x,y,angle,kind,length in pins:
        ps.append(f'(pin {kind} line (at {x} {y} {angle}) (length {length}) (name {q(label)} {effect(1.0)}) (number {q(num)} {effect(1.0)}))')
    libs[name]=f'(symbol "Soil:{name}" (pin_names (offset 0.635)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 0 0) {effect()}) (property "Value" {q(name)} (at 0 0 0) {effect()}) (symbol "{name}_0_1" {drawing}) (symbol "{name}_1_1" {"".join(ps)}))'
    return pins
two=[('1','',-5.08,0,0,'passive',2.54),('2','',5.08,0,180,'passive',2.54)]
library('R',two,'resistor');library('Fuse',two,'resistor');library('Link',two,'switch')
cap=[('1','',-5.08,0,0,'passive',4.445),('2','',5.08,0,180,'passive',4.445)]
library('C',cap,'capacitor')
led=[('2','A',-5.08,0,0,'passive',3.81),('1','K',5.08,0,180,'passive',3.81)]
library('LED',led,'led')
for n in [2,3]:
    library('Conn'+str(n),[(str(i+1),str(i+1),-7.62,(n-1)*2.54/2-i*2.54,0,'passive',2.54) for i in range(n)],width=10.16,height=n*2.54+2.54)
buf=[('1','~{OE}',-15.24,5.08,0,'input',5.08),('2','A',-15.24,0,0,'input',5.08),('3','GND',-15.24,-5.08,0,'power_in',5.08),('4','Y',15.24,0,180,'output',5.08),('5','VCC',15.24,5.08,180,'power_in',5.08)]
library('AHCT125',buf,width=20.32,height=15.24)
left=['3V3','EN','VP','VN','IO34','IO35','IO32','IO33','IO25','IO26','IO27','IO14','IO12','GND','IO13','D2','D3','CMD','5V']
right=['GND','IO23','IO22','TX','RX','IO21','GND','IO19','IO18','IO5','IO17','IO16','IO4','IO0','IO2','IO15','D1','D0','CLK']
mcu=[]
for side,names,x,a in [('J2',left,-25.4,0),('J3',right,25.4,180)]:
    for i,name in enumerate(names):
        typ='power_in' if name in ['GND','5V'] else 'power_out' if name=='3V3' else 'input' if name in ['IO34','IO35','VP','VN','EN'] else 'bidirectional'
        mcu.append((f'{side}.{i+1}',name,x,45.72-i*5.08,a,typ,5.08))
library('DevKitC_V4',mcu,width=40.64,height=99.06)
def text(s,x,y,size=1.5): items.append(f'(text {q(s)} (at {x} {y} 0) {effect(size,"(justify left)")} (uuid {uid()}))')
def component(ref,kind,value,x,y,connections,desc,footprint=''):
    pins={'R':two,'Fuse':two,'Link':two,'C':cap,'LED':led,'AHCT125':buf,'DevKitC_V4':mcu}.get(kind)
    if pins is None:
        n=int(kind[-1]);pins=[(str(i+1),str(i+1),-7.62,(n-1)*2.54/2-i*2.54,0,'passive',2.54) for i in range(n)]
    sid=uid()
    offset=55 if kind=='DevKitC_V4' else 11 if kind=='AHCT125' else 8 if kind.startswith('Conn') else 6
    items.append(f'(symbol (lib_id "Soil:{kind}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {sid}) (property "Reference" {q(ref)} (at {x} {y-offset} 0) {effect()}) (property "Value" {q(value)} (at {x} {y-offset+2.54} 0) {effect(1.1)}) (property "Footprint" {q(footprint)} (at {x} {y} 0) {effect(1.27,"(hide yes)")}) '+''.join(f'(pin {q(p[0])} (uuid {uid()}))' for p in pins)+f'(instances (project "soil_valve" (path "/{rootid}" (reference {q(ref)}) (unit 1)))))')
    components.append({'reference':ref,'value':value,'description':desc,'footprint':footprint})
    for num,label,dx,dy,angle,typ,length in pins:
        px,py=round(x+dx,4),round(y-dy,4)
        net=connections.get(num)
        if net is None:
            items.append(f'(no_connect (at {px} {py}) (uuid {uid()}))');continue
        ex=round(px+(-7.62 if dx<0 else 7.62),4)
        items.append(f'(wire (pts (xy {px} {py}) (xy {ex} {py})) (stroke (width 0) (type default)) (uuid {uid()}))')
        items.append(f'(label {q(net)} (at {ex} {py} 0) {effect(1.1,"(justify left bottom)")} (uuid {uid()}))')
        nets.setdefault(net,[]).append([ref,num])
def pair(ref,kind,value,x,y,a,b,desc):component(ref,kind,value,x,y,{'1':a,'2':b},desc)
text('SOIL / VALVE — Rev A | MODULE-LEVEL BUILD SCHEMATIC',15,16,2.5)
text('01 / POWER — regulated 5.0 V, 3 A SELV supply; star ground at J1',15,23)
component('J1','Conn2','5 V INPUT',38.1,38.1,{'1':'VIN_5V','2':'GND'},'Keyed 2-pin supply connector, >=3 A; pin 1 positive')
pair('F1','Fuse','2 A fast fuse',81.28,38.1,'VIN_5V','FUSED_5V','Replaceable 2 A fuse, rated >=32 VDC')
pair('SW1','Link','POWER switch',132.08,38.1,'FUSED_5V','+5V','SPST maintained switch >=3 A DC')
pair('JP1','Link','RUN link',81.28,58.42,'+5V','MCU_5V','Remove this jumper AND switch external power OFF before USB connection')
pair('C1','C','1000 uF / 10 V (+ at 1)',132.08,58.42,'+5V','GND','Low ESR electrolytic, positive terminal pin 1, near servo connector')
pair('C2','C','10 uF / 10 V',38.1,78.74,'MCU_5V','GND','MCU input bulk capacitor')
text('USB programming: SW1 OFF + JP1 REMOVED. Disconnect USB before restoring RUN.',15,91,1.25)
text('Input has no reverse-polarity protection; verify J1 polarity before connection.',15,96,1.25)
text('02 / MOISTURE — SEN0193 powered from 3V3',15,111)
component('J2','Conn3','PROBE',38.1,127,{'1':'+3V3','2':'GND','3':'PROBE_OUT'},'Board harness: 1=3V3 2=GND 3=analog; verify sensor cable mapping')
pair('R1','R','10k 1%',88.9,127,'PROBE_OUT','ADC_MV','ADC divider top resistor')
pair('R2','R','20k 1%',139.7,127,'ADC_MV','GND','ADC divider bottom resistor, disconnect pulls ADC low')
pair('C3','C','100 nF',88.9,149.86,'ADC_MV','GND','ADC low pass capacitor at GPIO34')
pair('C4','C','100 nF',38.1,149.86,'+3V3','GND','Probe supply decoupling at connector')
text('Vadc = 0.667 x Vprobe. Calibrate at ADC node with this divider installed.',15,165,1.25)
text('03 / SERVO — HS-311; external low-pressure valve linkage',15,181)
component('U2','AHCT125','SN74AHCT1G125DBVR',68.58,205.74,{'1':'GND','2':'PWM_3V3','3':'GND','4':'PWM_5V','5':'+5V'},'TI SOT-23-5 buffer, TTL input; assemble on SOT23-5 breakout','Package_TO_SOT_SMD:SOT-23-5')
pair('R3','R','100k',38.1,233.68,'PWM_3V3','GND','PWM pulldown keeps buffer input low during reset')
pair('R4','R','220R',121.92,203.2,'PWM_5V','SERVO_SIG','Series output damping resistor')
component('J3','Conn3','SERVO',139.7,226.06,{'1':'GND','2':'+5V','3':'SERVO_SIG'},'Servo: 1 black ground, 2 red supply, 3 yellow signal; verify actual unit')
pair('C5','C','100 nF',81.28,254,'+5V','GND','U2 bypass within 5 mm of pins 5/3')
text('Servo current returns directly to J1 GND. Do not route through DevKit headers.',15,269,1.25)
text('04 / ESP32 DevKitC V4 — ESP32-WROOM-32E',200,23)
con={'J2.1':'+3V3','J2.5':'ADC_MV','J2.7':'LED_RED','J2.9':'LED_GREEN','J2.10':'LED_AMBER','J2.11':'STOP_GPIO','J2.14':'GND','J2.19':'MCU_5V','J3.1':'GND','J3.7':'GND','J3.9':'PWM_3V3'}
component('U1','DevKitC_V4','ESP32-DevKitC V4',281.94,88.9,con,'Complete purchased Espressif development board; pin numbers refer to its J2/J3 headers')
text('All unconnected module header pins intentionally unused.',219,144,1.25)
text('05 / PANEL LEDs — 5 mm diffused, active HIGH',200,160)
for i,(net,col) in enumerate([('LED_GREEN','GREEN'),('LED_AMBER','AMBER'),('LED_RED','RED')]):
    y=175.26+i*17.78
    pair('R'+str(5+i),'R','680R',233.68,y,net,'A_'+col,'LED series resistor, approx 1–2 mA')
    component('D'+str(i+1),'LED',col,299.72,y,{'2':'A_'+col,'1':'GND'},'Off-board 5 mm panel LED, anode=2 cathode=1')
text('06 / PHYSICAL STOP — firmware interlock, not a safety-rated E-stop',200,230)
component('J4','Conn2','NC STOP LOOP',226.06,246.38,{'1':'STOP_SW','2':'GND'},'Connect an external normally closed maintained STOP switch between pins 1 and 2')
pair('R8','R','1k',276.86,246.38,'STOP_SW','STOP_GPIO','Input current limiting; loop open reads high')
pair('R9','R','10k',337.82,246.38,'+3V3','STOP_GPIO','External STOP pullup')
pair('C6','C','100 nF',276.86,266.7,'STOP_GPIO','GND','STOP input noise filtering')
text('STOP latches a firmware fault.\nNo guaranteed closure on power loss.',200,280,1.25)
# Explicit power sources for ERC: input connector, protected rails and common ground.
flag=[('1','pwr',0,0,90,'power_out',0)]
library('PWR_FLAG',flag,width=1.27,height=1.27)
for i,(net,x) in enumerate([('VIN_5V',360.68),('GND',375.92),('+5V',391.16),('MCU_5V',360.68)]):
    y=43.18 if i<3 else 63.5;ref=f'#FLG0{i+1}'
    items.append(f'(symbol (lib_id "Soil:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {uid()}) (property "Reference" {q(ref)} (at {x} {y} 0) {effect(1.27,"(hide yes)")}) (property "Value" "PWR_FLAG" (at {x} {y-3} 0) {effect(1)}) (pin "1" (uuid {uid()})) (instances (project "soil_valve" (path "/{rootid}" (reference {q(ref)}) (unit 1)))))')
    items.append(f'(label {q(net)} (at {x} {y} 0) {effect(1,"(justify left bottom)")} (uuid {uid()}))')
text('POWER SOURCE\nDECLARATIONS',351,27,1.25)
body=f'(kicad_sch (version 20250114) (generator "soil_design_generator") (uuid {rootid}) (paper "A3") (title_block (title "ESP32 Soil Moisture / Servo Valve") (date "2026-09-25") (rev "A") (company "Engineering prototype — hardware validation required")) (lib_symbols {"".join(libs.values())}) {"".join(items)} (embedded_fonts no))'
(OUT/'soil_valve.kicad_sch').write_text(body,encoding='utf-8')
(OUT/'Soil.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "soil_design_generator") '+''.join(s.replace('"Soil:'+name+'"','"'+name+'"',1) for name,s in libs.items())+')',encoding='utf-8')
(OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Soil")(type "KiCad")(uri "${KIPRJMOD}/Soil.kicad_sym")(options "")(descr "Project symbols")))')
(OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Package_TO_SOT_SMD")(type "KiCad")(uri "${KICAD10_FOOTPRINT_DIR}/Package_TO_SOT_SMD.pretty")(options "")(descr "KiCad standard footprints")))')
(OUT/'connectivity.json').write_text(json.dumps(nets,indent=2)+'\n')
with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['reference','value','description','footprint']);w.writeheader();w.writerows(components)
print(f'Generated {len(components)} components, {len(nets)} nets')
