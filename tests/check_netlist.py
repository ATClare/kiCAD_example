"""Compare KiCad's actual exported nets against the generator's intended pin map."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
expected=json.loads((root/'electronics/connectivity.json').read_text())
xml=ET.parse(root/'electronics/soil_valve.net.xml')
actual={}
for n in xml.findall('.//nets/net'):
    name=n.attrib['name'].lstrip('/')
    pins=sorted([p.attrib['ref'],p.attrib['pin']] for p in n.findall('node') if not p.attrib['ref'].startswith('#'))
    actual[name]=pins
for name,pins in expected.items():assert sorted(pins)==actual.get(name),(name,pins,actual.get(name))
assert actual['ADC_MV']==sorted([['R1','2'],['R2','1'],['C3','1'],['U1','J2.5']])
assert ['U2','5'] in actual['+5V'] and ['U2','1'] in actual['GND']
assert ['U1','J3.9'] in actual['PWM_3V3']
print(f'PASS: all {len(expected)} named nets match exported KiCad connectivity; ADC and buffer pin checks passed')
