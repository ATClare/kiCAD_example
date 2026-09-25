"""Offline browser integration checks using mocked device responses, not hardware."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs';OUT.mkdir(exist_ok=True)
html=(ROOT/'firmware/web/index.html').read_text(encoding='utf-8')
state={'boot':'testboot','token':'test-token','s':300,'moisture':28.5,'mv':1386.0,'valid':True,'armed':False,'open':False,'fault':'','storageOK':True,'calibrated':True,'low':30,'high':55,'dryMv':1600,'wetMv':850,'reservedSeconds':0,'events':[{'s':120,'message':'LOW moisture threshold crossed'}]}
commands=[]; errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1200},device_scale_factor=1)
    page.on('pageerror',lambda err:errors.append(str(err)))
    page.goto((ROOT/'firmware/web/index.html').as_uri()+'?demo=1')
    page.screenshot(path=str(OUT/'dashboard-demo.png'),full_page=True)
    assert page.locator('#demo').is_visible()
    assert page.locator('[data-action="arm"]').is_disabled()
    def route(r):
        path=r.request.url.split('soil.test')[-1]
        if path=='/':r.fulfill(content_type='text/html',body=html)
        elif path=='/api/status':r.fulfill(content_type='application/json',body=json.dumps(state))
        elif path=='/api/history':r.fulfill(content_type='application/json',body=json.dumps([{'s':60,'pct':40,'mv':1300,'open':False},{'s':120,'pct':None,'mv':0,'open':False},{'s':180,'pct':28.5,'mv':1386,'open':False}]))
        elif path=='/api/command':
            assert r.request.headers['x-control-token']=='test-token'
            commands.append(r.request.post_data)
            if 'arm'==r.request.post_data.split('=')[-1]:state['armed']=True
            if 'close' in r.request.post_data:state['armed']=False
            r.fulfill(body='Command accepted')
        elif path=='/api/config':
            commands.append(r.request.post_data);r.fulfill(body='Saved')
        else:r.fulfill(status=404)
    page.route('http://soil.test/**',route)
    page.goto('http://soil.test/')
    page.wait_for_function("document.querySelector('#moisture').textContent==='28.5 %'")
    assert 'LOW moisture' in page.locator('#banner').inner_text()
    page.click('[data-action="arm"]')
    page.wait_for_function("document.querySelector('#mode').textContent==='Armed'")
    page.click('[data-action="close"]')
    page.wait_for_function("document.querySelector('#mode').textContent==='Disarmed'")
    assert len(commands)==2
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(OUT/'dashboard-mobile-test.png'),full_page=True)
    with page.expect_download() as download:page.click('#csv')
    download.value.save_as(str(OUT/'test-history.csv'))
    csv=(OUT/'test-history.csv').read_text()
    assert '120,,0,false' in csv
    page.unroute('http://soil.test/**')
    page.route('http://soil.test/**',lambda r:r.abort())
    page.evaluate('refresh()')
    page.wait_for_function("document.querySelector('#connection').textContent==='Offline / stale'")
    assert page.locator('[data-action="arm"]').is_disabled()
    # Native SVG visual inspection assets.
    page.set_viewport_size({'width':1680,'height':1188})
    page.set_content('<body style="margin:0;background:white">'+(ROOT/'electronics/rendered/soil_valve.svg').read_text(encoding='utf-8').split('<svg',1)[0].replace('<?xml version="1.0" standalone="no"?>','')+'</body>')
    svg=(ROOT/'electronics/rendered/soil_valve.svg').read_text(encoding='utf-8')
    page.set_content('<body style="margin:0;background:white"><svg'+svg.split('<svg',1)[1]+'</body>')
    page.locator('svg').evaluate("e=>{e.style.width='1680px';e.style.height='1188px'}")
    page.screenshot(path=str(OUT/'schematic-preview.png'))
    svg=(ROOT/'mechanical/exports/enclosure_exploded.svg').read_text(encoding='utf-8')
    page.set_content('<body style="background:white"><svg'+svg.split('<svg',1)[1]+'</body>')
    page.screenshot(path=str(OUT/'enclosure-preview.png'))
    browser.close()
assert not errors,errors
print('PASS: demo, live rendering, threshold alert, arm/close requests, CSRF header, mobile layout, CSV gaps, offline disable, JavaScript errors')
