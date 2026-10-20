// Export a deterministic P7 world-state receipt as GodRender runner input.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
const base=process.env.AE_BASE_URL||'http://127.0.0.1:8765';
const output=process.env.AE_SEED_OUTPUT||'dist/data/ae_p7_seed_receipt.json';
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
try{
 const page=await browser.newPage();
 await page.goto(base,{waitUntil:'load'});
 await page.waitForFunction(()=>document.querySelector('#peopleStatus')?.textContent?.includes('P7 VERIFIED'),null,{timeout:30000});
 const receipt=await page.evaluate(()=>window.AE_People.getRun());
 if(receipt?.schema!=='american-empire.p7-run.v1'||receipt.snapshots.length!==12||!receipt.snapshots[1].people.claire)
   throw Error('Source-bound film participant receipt unavailable');
 await fs.mkdir((await import('node:path')).dirname(output),{recursive:true});
 await fs.writeFile(output,JSON.stringify(receipt,null,2)+'\n','utf8');
 console.log('AE seed generated from real browser P7 engine: '+receipt.run_sha256+' · agents '+Object.keys(receipt.snapshots[1].people).length);
}finally{await browser.close();}
