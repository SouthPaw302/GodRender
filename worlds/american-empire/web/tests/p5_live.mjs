// Actual browser P5 contract: exact parity vs the Python P3 oracle, live branching,
// 2037 evolution, comparisons, local save/reload, replay and full run export.
// Execute for both HTTPS-like served static build and standalone file:// build.
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const address=process.env.AE_BASE_URL||'http://127.0.0.1:8765';
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1440,height:900},acceptDownloads:true});
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(address,{waitUntil:'load'});
 await page.waitForFunction(()=>document.querySelector('#liveStatus')?.textContent?.includes('P3 parity PASS'),{timeout:25000});
 assert.equal(await page.locator('#liveScenario option').count(),3);
 assert.equal(await page.locator('#liveAction option').count(),10);
 await page.locator('[data-tab="simulation"]').click();
 assert.equal(await page.locator('#liveMetrics .sim-variable').count(),7);
 await page.locator('#liveYear').evaluate(el=>{el.value='2029';el.dispatchEvent(new Event('input',{bubbles:true}));});
 assert.equal(await page.locator('#liveYearDisplay').textContent(),'2029');
 const title=await page.locator('#liveHeroTitle').textContent();
 const baseline=(await page.locator('#livePressure').textContent()).trim();
 await page.locator('#liveAction').selectOption('atlas_expansion');
 await page.locator('#liveSubject').selectOption('system:S1');
 await page.locator('#liveIntensity').evaluate(el=>{el.value='2';el.dispatchEvent(new Event('input',{bubbles:true}));});
 await page.locator('#liveForkName').fill('atlas-test-p5');
 await page.locator('#liveApply').click();
 await page.getByText(/Created atlas-test-p5/).waitFor();
 assert.equal(await page.locator('#liveScenario').inputValue(),'atlas-test-p5');
 assert.equal(await page.locator('#liveHeroTitle').textContent(),title); // canon unchanged
 assert.notEqual((await page.locator('#livePressure').textContent()).trim(),baseline);
 await page.locator('#liveCompare').selectOption('baseline');
 await page.locator('#liveCompareButton').click();
 assert.match(await page.locator('#liveComparison').textContent(),/First divergence:\s*2029/);
 await page.locator('#liveReplay').click();
 await page.getByText(/REPLAY VERIFIED/).waitFor();
 const receiptPromise=page.waitForEvent('download');
 await page.locator('#liveExport').click();
 const download=await receiptPromise;
 assert.match(download.suggestedFilename(),/atlas-test-p5-p5-run\.json/);
 const receipt=JSON.parse(await (await import('node:fs/promises')).readFile(await download.path(),'utf8'));
 assert.equal(receipt.authority_layer,'scenario_only');
 assert.equal(receipt.snapshots.length,12);
 assert.equal(receipt.event_receipts.length,1);
 assert.equal(receipt.event_receipts[0].type,'atlas_expansion');
 assert.equal(receipt.event_receipts[0].subject,'system:S1');
 assert.equal(receipt.event_receipts[0].intensity,2);
 assert.equal(receipt.scenario.branch.fork_year,2028);
 assert.equal(receipt.snapshots[2].state.V1,37); // source seed 35, +1 per intact year through 2028
 await page.locator('#liveAdvance').click();
 assert.equal(await page.locator('#liveYearDisplay').textContent(),'2030');
 await page.locator('#liveYear').evaluate(el=>{el.value='2037';el.dispatchEvent(new Event('input',{bubbles:true}));});
 assert.equal(await page.locator('#liveYearDisplay').textContent(),'2037');
 await page.locator('#liveSave').click();
 await page.getByText(/Saved atlas-test-p5 locally/).waitFor();
 await page.reload({waitUntil:'load'});
 await page.waitForFunction(()=>document.querySelector('#liveStatus')?.textContent?.includes('P3 parity PASS'),{timeout:25000});
 await page.locator('[data-tab="simulation"]').click();
 assert.equal(await page.locator('#liveScenario option').count(),4);
 await page.locator('#liveScenario').selectOption('atlas-test-p5');
 await page.locator('#liveYear').evaluate(el=>{el.value='2029';el.dispatchEvent(new Event('input',{bubbles:true}));});
 assert.match(await page.locator('#liveEvents').textContent(),/Atlas settlement integration/);
 assert.match(await page.locator('#liveSavedList').textContent(),/atlas-test-p5/);
 // Failed import may not promote tampered run output or rewrite source hashes.
 const corrupted=structuredClone(receipt);corrupted.scenario.id='new-tampered-run';
 corrupted.snapshots[0].state.V1=99;
 await page.locator('#liveImportFile').setInputFiles({name:'tampered.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(corrupted))});
 await page.getByText(/Import rejected/).waitFor();
 assert.equal(await page.locator('#liveScenario option').count(),4);
 if(errors.length)throw new Error('Page script exceptions: '+errors.join('; '));
 console.log('P5 LIVE BROWSER PASS: exact P3 parity, fork at 2029, compare, replay, export, year 2037, local persistence, rejection of tampered imports.');
} finally {await browser.close();}
