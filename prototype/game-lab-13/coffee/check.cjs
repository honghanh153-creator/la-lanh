const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const path=require('node:path');
const source=fs.readFileSync(process.argv[2]||path.join(__dirname,'index.html'),'utf8');
let document;
class Element {
  constructor(tag='div',attrs={}){this.tagName=tag;this.attrs=attrs;this.children=[];this.events={};this.style={};this.dataset=new Proxy({}, {get:(_,key)=>this.attrs['data-'+key.replace(/[A-Z]/g,l=>'-'+l.toLowerCase())],set:(_,key,value)=>{this.attrs['data-'+key.replace(/[A-Z]/g,l=>'-'+l.toLowerCase())]=String(value);return true;}});this.clientWidth=800;this.clientHeight=600;this.value=attrs.value||'';this.classList={add:(c)=>{const a=new Set((this.className||'').split(/\s+/));a.add(c);this.className=[...a].join(' ');},toggle:(c,force)=>{const a=new Set((this.className||'').split(/\s+/));const next=force===undefined?!a.has(c):force;if(next)a.add(c);else a.delete(c);this.className=[...a].join(' ');return next;},contains:c=>(this.className||'').split(/\s+/).includes(c)};}
  get className(){return this.attrs.class||''}set className(v){this.attrs.class=v}
  get hidden(){return 'hidden'in this.attrs}set hidden(v){if(v)this.attrs.hidden='';else delete this.attrs.hidden}
  get disabled(){return 'disabled'in this.attrs}set disabled(v){if(v)this.attrs.disabled='';else delete this.attrs.disabled}
  get isConnected(){let n=this;while(n.parent)n=n.parent;return n===root}
  get textContent(){return this.children.map(c=>typeof c==='string'?c:c.textContent).join('')}set textContent(v){this.replaceChildren(String(v))}
  set innerHTML(v){const fragment=parse(v);this.replaceChildren(...fragment.children)}
  setAttribute(k,v){this.attrs[k]=String(v)}getAttribute(k){return this.attrs[k]??null}
  append(...nodes){nodes.forEach(n=>{if(typeof n!=='string')n.parent=this;this.children.push(n)})}
  replaceChildren(...nodes){this.children.forEach(n=>{if(typeof n!=='string')n.parent=null});this.children=[];this.append(...nodes)}
  addEventListener(k,fn){this.events[k]=fn}
  emit(k,e={}){assert(this.events[k],this.tagName+' missing '+k);this.events[k]({target:this,preventDefault(){},...e})}
  click(){if(!this.disabled){this.focus();this.emit('click')}}focus(){document.activeElement=this}
  matches(s){if(s.includes(','))return s.split(',').some(x=>this.matches(x));if(s.endsWith(':not(:disabled)'))return !this.disabled&&this.matches(s.slice(0,-':not(:disabled)'.length));if(s.startsWith('.'))return this.classList.contains(s.slice(1));if(s.startsWith('#'))return this.attrs.id===s.slice(1);if(s.startsWith('[')){const m=s.match(/^\[([^=\]]+)(?:="([^"]*)")?\]$/);assert(m,'Unsupported '+s);return m[2]===undefined?m[1]in this.attrs:this.attrs[m[1]]===m[2];}return this.tagName===s}
  querySelectorAll(s){const result=[];for(const c of this.children)if(typeof c!=='string'){if(c.matches(s))result.push(c);result.push(...c.querySelectorAll(s))}return result}
  querySelector(s){return this.querySelectorAll(s)[0]||null}
}
function parse(html){const base=new Element('document'),stack=[base];for(const token of html.match(/<!--[\s\S]*?-->|<![^>]*>|<[^>]*>|[^<]+/g)||[]){if(token.startsWith('<!'))continue;if(token.startsWith('</')){const tag=token.match(/^<\/([\w-]+)/)?.[1];for(let i=stack.length-1;i>0;i--)if(stack[i].tagName===tag){stack.length=i;break;}continue;}if(token.startsWith('<')){const tag=token.match(/^<([\w-]+)/)?.[1];if(!tag)continue;const attrs={};const raw=token.slice(tag.length+1).replace(/\/?\s*>$/,'');for(const m of raw.matchAll(/([^\s=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g))attrs[m[1]]=m[2]??m[3]??m[4]??'';const node=new Element(tag,attrs);stack[stack.length-1].append(node);if(!['img','meta','input','br','link','hr','source'].includes(tag)&&!token.endsWith('/>'))stack.push(node);}else stack[stack.length-1].append(token);}return base;}
const script=[...source.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
const root=parse(source.replace(/<script>[\s\S]*?<\/script>/g,'').replace(/<style>[\s\S]*?<\/style>/g,''));
document={body:root.querySelector('body'),activeElement:null,events:{},getElementById:id=>root.querySelector('#'+id),querySelectorAll:s=>root.querySelectorAll(s),createElement:tag=>new Element(tag),addEventListener(k,fn){this.events[k]=fn;}};
const context=vm.createContext({document,console,window:{GameLab:require('../model.js')},setTimeout:()=>1,clearTimeout(){}});script.forEach(s=>new vm.Script(s).runInContext(context));
const $=id=>document.getElementById(id);
const tabs=root.querySelectorAll('[data-theme]');assert.equal(tabs.length,2);
let loops=0;
for(let t=0;t<2;t++){
 tabs[t].click();assert.equal(tabs[t].getAttribute('aria-selected'),'true');assert.equal(root.querySelectorAll('.hit').length,11);assert.equal(root.querySelectorAll('.actor').length,3);assert.equal(root.querySelectorAll('.person-label').length,3);
 const room=$('room').src;assert(room.includes(t?'pixel-room':'cartoon-room')||room.startsWith('data:'));
 for(const hit of root.querySelectorAll('.hit')){
  hit.click();assert(!$('context').hidden);assert.equal(hit.getAttribute('aria-pressed'),'true');$('look').click();assert(!$('shade').hidden);assert($('modalContent').querySelector('.closeup'));const lookText=$('modalContent').textContent;
  $('close').click();assert($('shade').hidden);assert.equal($('objectSelect').value,hit.dataset.object);
  $('search').click();assert(!$('shade').hidden);assert($('modalContent').querySelector('.scan-line'));if(['bag','pocket'].includes(hit.dataset.object)){assert($('modalContent').querySelector('.notice'));assert($('modalContent').textContent.includes('Chưa có quyền'));}
  assert.notEqual($('modalContent').textContent,lookText);$('modalContent').querySelector('.book-save').click();assert($('modalContent').textContent.includes('Đã ghi chú'));$('close').click();loops++;
 }
 for(const label of root.querySelectorAll('.person-label')){label.click();assert(!$('shade').hidden);assert($('modalContent').textContent.includes('Tính cách và chiêm tinh không được dùng để kết tội'));$('close').click();}
 $('motion').click();assert(document.body.classList.contains('paused'));$('motion').click();assert(!document.body.classList.contains('paused'));
 $('markers').click();assert($('stage').classList.contains('hits-off'));$('markers').click();assert(!$('stage').classList.contains('hits-off'));
}
assert.equal($('visitCount').textContent,'Đã nhìn kỹ 11 / 11 đồ vật');
const books=root.querySelectorAll('[data-book]');books[1].click();assert($('book').textContent.includes('Lời khai · Chưa kiểm chứng'));books[2].click();assert($('book').textContent.includes('Không dùng sự thật kín'));books[0].click();
$('help').click();document.events.keydown({key:'Escape'});assert($('shade').hidden);
root.querySelectorAll('.hit')[0].click();$('look').click();const focusables=$('modal').querySelectorAll('button:not(:disabled),[tabindex="0"]');assert(focusables.length>=3);focusables.at(-1).focus();let trapped=false;document.events.keydown({key:'Tab',preventDefault(){trapped=true}});assert(trapped);assert.equal(document.activeElement,focusables[0]);$('close').click();
assert(source.includes('@keyframes breathe')&&source.includes('@keyframes blink'));assert(source.includes('prefers-reduced-motion'));assert(!/fetch\(|XMLHttpRequest|WebSocket/.test(source));assert.equal(root.querySelectorAll('.time').filter(n=>n.disabled).length,2);
console.log(JSON.stringify({syntax:'pass',actual_app_script_executed:true,art_directions:2,independent_cast_layers:3,look_search_roundtrips:loops,private_contents_not_shown:true,notebook_and_claims:true,theme_keeps_inspected_state:true,pause_and_markers:true,keyboard_escape_focus_trap:true,external_api_calls:false,animation_css_present:true,browser_render_and_animation_visual_qa:false},null,2));
