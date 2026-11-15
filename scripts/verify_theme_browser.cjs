const fs=require('fs');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const envs=[['ISS','ISS','fg-env-iss'],['Moon Base','Lunar habitat','fg-env-moon'],['Mars Mission','Mars mission','fg-env-mars'],['Earth Lab','Earth laboratory','fg-env-earth']];
const routes=['overview','environment','cargo','materials','experiments','gaps','assistant','methodology'];
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
 fs.mkdirSync('docs/theme_screens',{recursive:true});
 const results=[];
 for(const width of [1440,390]){
  const ctx=await b.newContext({viewport:{width,height:width===390?844:1000},reducedMotion:'reduce'});
  const p=await ctx.newPage();
  for(const [env,label,cls] of envs){
   await p.goto('http://127.0.0.1:8765');
   await p.locator('.st-key-mission_toolbar').getByText(label,{exact:true}).click();
   await p.locator('.stApp.'+cls).waitFor();
   for(const route of routes){
    // Use Streamlit navigation to preserve environment selection across pages.
    await p.locator('[data-testid=stSidebar] [data-testid=stPageLink-NavLink]').nth(routes.indexOf(route)).evaluate(e=>e.click());
    await p.locator('.stApp.'+cls).waitFor();
    if(route!=='overview')await p.waitForURL('**/'+route);
    await p.waitForTimeout(800);
    await p.evaluate(()=>{window.scrollTo(0,0);document.querySelectorAll('section,main,[data-testid*=Main]').forEach(e=>e.scrollTop=0);});
    const errors=await p.locator('[data-testid="stException"]').allTextContents();
    const overflow=await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2);
    const file=`docs/theme_screens/${cls}-${route}-${width}.png`;
    await p.screenshot({path:file,fullPage:true});
    results.push({env,route,width,errors,overflow,file});
    if(errors.length)throw new Error(JSON.stringify(results.at(-1)));
   }
  }
  await ctx.close();
 }
 fs.writeFileSync('docs/theme_screens/results.json',JSON.stringify(results,null,2));
 console.log(JSON.stringify({screenshots:results.length,errors:results.filter(x=>x.errors.length).length,overflows:results.filter(x=>x.overflow)}));
 await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
