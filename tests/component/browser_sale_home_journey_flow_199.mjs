// Real authenticated Streamlit app + existing canonical writer, isolated data only.
// External test runner, not a product dependency. See evidence/logi-199-sale-home-journey/README.md.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const OUT=path.resolve(process.env.LOGI199_BROWSER_OUTPUT || path.join(ROOT,'.tmp/logi199-flow/after'));
const credentials=JSON.parse(fs.readFileSync(process.env.LOGI199_TEST_CREDENTIALS_FILE,'utf8'));
const readback=process.env.LOGI199_TEST_READBACK_FILE;
const BASE=process.env.LOGI199_TEST_URL || 'http://127.0.0.1:9501';
assert.ok(readback,'test-side DB snapshot path is required');
fs.mkdirSync(OUT,{recursive:true});
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE});
const SID='FLOW199-FCL';
const ROUTE=`/lo-hang/${SID}?tab=van-tai&stage=si-vgm&work=info`;
const label='Ngày xếp hàng lên tàu (on-board)';
const results={browser:await browser.version(),authRequired:true,isolation:'MONGOMOCK_PROCESS_LOCAL',flow:[],pageErrors:[]};
const record=(name,value)=>{results[name]=value;fs.writeFileSync(path.join(OUT,'result.json'),JSON.stringify(results,null,2));};
const snapshot=()=>JSON.parse(fs.readFileSync(readback,'utf8'));
function waitForSnapshot(predicate){
  return new Promise((resolve,reject)=>{
    const watcher=fs.watch(path.dirname(readback),check);
    const timeout=setTimeout(()=>{watcher.close();reject(new Error('Canonical DB readback timed out'));},30000);
    function check(){
      try{const value=snapshot();if(predicate(value)){watcher.close();clearTimeout(timeout);resolve(value);}}catch{}
    }
    check();
  });
}
async function login(page,initial=false){
  const username=page.getByLabel('Tài khoản',{exact:true});
  if(initial){await username.waitFor({state:'visible',timeout:90000});assert.equal(await page.locator('.logi-shell').count(),0,'no app before login');}
  else await Promise.race([username.waitFor({state:'visible',timeout:90000}),page.locator('.logi-shell').waitFor({state:'visible',timeout:90000})]);
  if(await username.isVisible()){
    await username.fill('flow199.sale');
    await page.getByLabel('Mật khẩu',{exact:true}).fill(credentials.password);
    await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();
  }
  await page.locator('.logi-shell').waitFor({state:'visible',timeout:90000});
}
async function reloadHome(page){await page.reload({waitUntil:'domcontentloaded'});await login(page);await page.getByTestId('attention-now').waitFor();}
async function openFromHome(page){
  const target=page.getByTestId('attention-now').locator(`a[href="${ROUTE}"]`);
  assert.equal(await target.count(),1,'Home contains canonical exact-stage action');
  await target.click();
  await page.getByTestId('journey-stage-workspace').waitFor();
  assert.match(await page.getByTestId('journey-modal').innerText(),new RegExp(`CÔNG ĐOẠN · ${SID}`));
  assert.match(await page.getByTestId('journey-stage-workspace').innerText(),/SI \/ VGM/);
  assert.equal(await page.getByLabel('Trạng thái SI',{exact:true}).inputValue(),'UNKNOWN','unknown is not completed');
  assert.equal(await page.getByTestId('journey-stage-workspace').getByRole('combobox').count(),2,'only SI/VGM statuses, no customer reselection');
  assert.match(await page.locator('.logi-shell main').innerText(),/An Phát JSC/);
}
async function closeStage(page){await page.getByRole('button',{name:'Đóng công đoạn',exact:true}).click();await page.getByTestId('journey-modal').waitFor({state:'hidden'});}
async function openNode(page,id,work,touch){
  await page.getByTestId('journey-zoom-fit').click();
  const node=page.getByTestId(`journey-node-${id}`);
  if(touch) await node.tap(); else await node.click();
  await page.getByTestId('journey-bubble').waitFor();
  assert.equal(await page.getByTestId('journey-bubble').getAttribute('data-node'),id);
  if(touch) await page.getByTestId('journey-zoom-readable').click();
  const bubble=page.getByTestId(`journey-bubble-task-${work}`);
  if(touch) await bubble.tap(); else await bubble.click();
  await page.getByTestId('journey-stage-workspace').waitFor();
}
async function noOverflow(page){
  const value=await page.locator('.logi-shell').evaluate(el=>Math.max(0,el.scrollWidth-el.clientWidth));
  assert.equal(value,0,'shell must not overflow horizontally');return value;
}
try{
  for(const [name,viewport,touch,newDate] of [
    ['desktop',{width:1440,height:900},false,'2026-10-05'],
    ['mobile',{width:390,height:844},true,'2026-10-06'],
  ]){
    const context=await browser.newContext({viewport,isMobile:touch,hasTouch:touch,deviceScaleFactor:1});
    const page=await context.newPage();
    page.on('pageerror',error=>results.pageErrors.push({viewport:name,message:String(error)}));
    await page.goto(BASE,{waitUntil:'domcontentloaded'});await login(page,true);
    const item={viewport,homeOverflow:await noOverflow(page),route:ROUTE};
    item.homeLayout=await page.getByTestId('attention-now').evaluate(el=>({height:el.getBoundingClientRect().height,gridAlign:getComputedStyle(el.parentElement).alignItems,siblingHeight:el.nextElementSibling?.getBoundingClientRect().height}));
    if(!touch){assert.equal(item.homeLayout.gridAlign,'flex-start');assert.ok(item.homeLayout.height<item.homeLayout.siblingHeight);}
    await page.screenshot({path:path.join(OUT,`${name}-home.png`)});
    if(!touch){
      const task=page.getByTestId('attention-now').locator('a[href="/lo-hang/LO-0308"]').first();
      assert.equal(await task.count(),1,'unbound task opens own shipment without arbitrary tab');
      await task.click();await page.getByTestId('shipment-journey').waitFor();
      assert.match(await page.locator('.logi-shell main').innerText(),/LO-0308/);
      assert.equal(await page.getByTestId('journey-modal').count(),0,'unbound task must not guess a stage');
      await page.screenshot({path:path.join(OUT,'desktop-unbound-task.png')});
      await reloadHome(page);
    }
    await openFromHome(page);
    await page.screenshot({path:path.join(OUT,`${name}-home-fcl-target.png`)});
    await closeStage(page);
    item.nodes=await page.locator('[data-testid^="journey-node-"]').count();assert.equal(item.nodes,9);
    item.mapTexture=await page.getByTestId('journey-map-texture').evaluate(el=>({hasImage:getComputedStyle(el).backgroundImage.startsWith('url('),size:getComputedStyle(el).backgroundSize}));assert.deepEqual(item.mapTexture,{hasImage:true,size:'760px'});
    item.parallelBranch=await page.getByTestId('journey-parallel-branch').count();assert.equal(item.parallelBranch,1);
    for(const branch of ['si-vgm','gate-in']) assert.equal(await page.locator(`svg path[data-from="${branch}"][data-to="etd"]`).count(),1,'parallel branches merge at ETD');
    await page.screenshot({path:path.join(OUT,`${name}-fcl-initial.png`)});
    await openNode(page,'si-vgm','docs',touch);
    await page.getByTestId('attachment-category').waitFor({state:'visible'});
    item.siDocumentCategories=await page.getByTestId('attachment-category').locator('option').evaluateAll(options=>options.map(o=>o.value));
    assert.deepEqual([...item.siDocumentCategories].sort(),['si','vgm']);
    assert.equal(await page.getByTestId('missing-info').count(),0);
    assert.equal(await page.getByTestId('journey-stage-workspace').locator('.sticky-action').count(),0);
    await page.screenshot({path:path.join(OUT,`${name}-si-docs.png`)});
    await closeStage(page);
    await openNode(page,'on-board','stage',touch);
    await page.getByLabel(label,{exact:true}).waitFor({state:'visible'});
    const workspace=page.getByTestId('journey-stage-workspace');
    assert.equal(await workspace.locator('input').count(),1);
    assert.equal(await page.getByTestId('missing-info').count(),0);
    assert.equal(await workspace.getByRole('button',{name:'Tài chính',exact:true}).count(),0);
    const before=await waitForSnapshot(value=>value.authRequired && value.shipments[SID]?.audit?.length);
    const beforeRow=before.shipments[SID];
    assert.equal(beforeRow.customerId,'CUST-ANPHAT');
    const oldDate=await page.getByLabel(label,{exact:true}).inputValue();
    assert.equal(oldDate,beforeRow.sea_export.on_board_at);assert.notEqual(oldDate,newDate,'must be a real edit');
    fs.writeFileSync(path.join(OUT,`${name}-backend-before.json`),JSON.stringify(beforeRow,null,2));
    await page.getByLabel(label,{exact:true}).fill(newDate);
    await page.screenshot({path:path.join(OUT,`${name}-on-board-edited.png`)});
    const saved=waitForSnapshot(value=>value.shipments[SID]?.version===beforeRow.version+1 && value.shipments[SID]?.sea_export.on_board_at===newDate);
    await page.getByTestId('sea-export-facts-save').click();
    const after=(await saved).shipments[SID];
    assert.equal(after.updated_by,'flow199.sale');assert.equal(after.updated_by_role,'sale');
    assert.equal(after.customerId,beforeRow.customerId);assert.equal(after.audit_count,beforeRow.audit_count+1);
    const lastAudit=after.audit.at(-1);
    assert.equal(lastAudit.actor,'flow199.sale');assert.equal(lastAudit.actor_role,'sale');
    assert.equal(lastAudit.before_on_board_at,oldDate);assert.equal(lastAudit.after_on_board_at,newDate);
    assert.deepEqual(after.sea_export,{...beforeRow.sea_export,on_board_at:newDate},'no unrelated sea fact altered');
    fs.writeFileSync(path.join(OUT,`${name}-backend-after-save.json`),JSON.stringify(after,null,2));
    await reloadHome(page);
    await openFromHome(page);await closeStage(page);await openNode(page,'on-board','stage',touch);
    assert.equal(await page.getByLabel(label,{exact:true}).inputValue(),newDate,'UI readback after full reload');
    const reloaded=snapshot().shipments[SID];assert.deepEqual(reloaded,after,'reload must not write or reset state');
    fs.writeFileSync(path.join(OUT,`${name}-backend-after-reload.json`),JSON.stringify(reloaded,null,2));
    item.save={oldDate,newDate,beforeVersion:beforeRow.version,afterVersion:after.version,actor:lastAudit.actor,auditDelta:after.audit_count-beforeRow.audit_count,customerUnchanged:true,reloadUiReadback:true,reloadDbReadback:true};
    item.popupOverflow=await noOverflow(page);
    await page.screenshot({path:path.join(OUT,`${name}-on-board-reloaded.png`)});
    results.flow.push(item);record('verdict','PASS_SO_FAR');
    await context.close();
  }
  // Keep the existing full-scope FCL map and missing-info truth, but only in
  // the whole-lot workspace. The stage must not inherit those global controls.
  const context=await browser.newContext({viewport:{width:1440,height:900},hasTouch:true});
  const page=await context.newPage();
  page.on('pageerror',error=>results.pageErrors.push({viewport:'full-scope-guard',message:String(error)}));
  await page.goto(BASE);await login(page,true);
  await page.locator('a[href="/lo-hang"]:visible').first().click();
  await page.getByTestId('shipment-period-tat-ca').click();
  await page.locator('a[href="/lo-hang/T6-FCL"]:visible').first().click();
  await page.getByTestId('shipment-journey').waitFor();
  assert.equal(await page.locator('[data-testid^="journey-node-"]').count(),11);
  await page.screenshot({path:path.join(OUT,'desktop-t6-full-scope-map.png')});
  const t6Before=snapshot().shipments['T6-FCL'];
  await page.getByTestId('journey-global-open').click();
  await page.getByTestId('missing-info').waitFor();
  assert.match(await page.getByTestId('missing-info').innerText(),/Thiếu 3 thông tin/);
  await page.getByRole('button',{name:'Đóng Global Workspace',exact:true}).click();
  await page.setViewportSize({width:390,height:844});
  await openNode(page,'on-board','stage',true);await page.getByLabel(label,{exact:true}).waitFor();
  assert.equal(await page.getByLabel(label,{exact:true}).inputValue(),'','unknown date is blank, not zero/completed');
  assert.equal(await page.getByTestId('missing-info').count(),0);
  assert.equal(await page.getByTestId('journey-stage-workspace').locator('.sticky-action').count(),0);
  assert.deepEqual(snapshot().shipments['T6-FCL'],t6Before,'read-only navigation must not write');
  await noOverflow(page);await page.screenshot({path:path.join(OUT,'mobile-t6-on-board-popup.png')});
  record('fullScopeGuard',{nodes:11,globalMissingInfo:3,stageMissingInfo:0,stageGlobalStickyActions:0,unknownDate:'',writes:0});
  await context.close();
  assert.deepEqual(results.pageErrors,[],'no browser page errors');
  record('verdict','PASS');
  console.log(JSON.stringify(results,null,2));
}catch(error){record('verdict','FAIL');console.error(error);process.exitCode=1;}
finally{await browser.close();}
