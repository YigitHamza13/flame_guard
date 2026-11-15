// Existing Playwright installation; no browser or package downloads.
const fs=require('fs');
const path=require('path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 const page=await context.newPage();
 const warm=process.argv.includes('--warm-shell');
 if(warm){
  await page.route('**/*.glb',route=>route.abort());
  await page.goto('http://127.0.0.1:8765');
  await page.getByText('Fire in space, in plain words',{exact:true}).waitFor({timeout:30000});
  await page.unroute('**/*.glb');
 }
 const cdp=await context.newCDPSession(page);
 await cdp.send('Network.enable'); await cdp.send('Network.setCacheDisabled',{cacheDisabled:!warm});
 await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:400,downloadThroughput:50000,uploadThroughput:50000,connectionType:'cellular3g'});
 const started=Date.now(),models=[],errors=[];
 page.on('request',r=>{if(r.url().endsWith('.glb')) models.push({url:r.url(),at_ms:Date.now()-started});});
 page.on('pageerror',e=>errors.push(e.message));
 console.log('Browser ready');
 const result={phase:process.argv[2]||'after',profile:{latency_ms:400,download_bytes_per_sec:50000,cache:warm?'warm application shell, cold GLB':'cold'},model_requests:models,errors};
 try{
  await page.goto('http://127.0.0.1:8765',{waitUntil:'domcontentloaded',timeout:120000});
  await page.getByText('Fire in space, in plain words',{exact:true}).waitFor({state:'visible',timeout:120000});
  result.meaningful_content_ms=Date.now()-started; console.log('Content visible',result.meaningful_content_ms);
  await page.waitForTimeout(3000);
  result.models_before_click=models.length;
  for(const frame of page.frames()){const button=frame.getByRole('button',{name:/Load 3D model/});if(await button.count()){result.click_ms=Date.now()-started;await button.click();break;}}
  const deadline=Date.now()+30000;
  result.model_loaded=false;
  while(Date.now()<deadline){
   for(const frame of page.frames()){
    if(await frame.locator('model-viewer').count()){
     if(await frame.locator('model-viewer').evaluate(m=>Boolean(m.loaded)).catch(()=>false)){result.model_loaded=true;result.model_loaded_ms=Date.now()-started;break;}
    }
   }
   if(result.model_loaded)break;
   await page.waitForTimeout(500);
  }
  result.model_observation_limit_ms=30000;
  result.fallback_shown=await Promise.all(page.frames().map(f=>f.locator('#fallback,#photo').count())).then(x=>x.some(Boolean));
 }catch(e){result.error=e.message;}
 result.elapsed_ms=Date.now()-started;
 fs.mkdirSync('docs',{recursive:true});fs.writeFileSync(path.join('docs',`performance-${result.phase}.json`),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
