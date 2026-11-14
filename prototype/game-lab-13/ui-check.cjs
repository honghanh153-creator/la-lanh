const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const path=require('node:path');
const source=fs.readFileSync(process.argv[2]||path.join(__dirname,'index.html'),'utf8');
let document;
class Element {
  constructor(tag='div',attrs={}){this.tagName=tag;this.attrs=attrs;this.children=[];this.events={};this.style={setProperty(k,v){this[k]=v}};this.dataset=new Proxy({}, {get:(_,key)=>this.attrs['data-'+key.replace(/[A-Z]/g,l=>'-'+l.toLowerCase())],set:(_,key,value)=>{this.attrs['data-'+key.replace(/[A-Z]/g,l=>'-'+l.toLowerCase())]=String(value);return true;}});this.clientWidth=800;this.clientHeight=600;this.value=attrs.value||'';this.classList={add:(c)=>{const a=new Set((this.className||'').split(/\s+/));a.add(c);this.className=[...a].join(' ');},toggle:(c,force)=>{const a=new Set((this.className||'').split(/\s+/));const next=force===undefined?!a.has(c):force;if(next)a.add(c);else a.delete(c);this.className=[...a].join(' ');return next;},contains:c=>(this.className||'').split(/\s+/).includes(c)};}
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
  matches(s){if(s.includes(','))return s.split(',').some(x=>this.matches(x));if(s.endsWith(':not(:disabled)'))return !this.disabled&&this.matches(s.slice(0,-':not(:disabled)'.length));if(s.startsWith('.'))return this.classList.contains(s.slice(1));if(s.startsWith('#'))return this.attrs.id===s.slice(1);if(s.startsWith('[')){const m=s.match(/^\[([^=\]]+)(?:="([^"]*)")?\]$/);assert(m,'Unsupported '+s);return m[2]===undefined?m[1]in this.attrs:this.attrs[m[1]]===m[2];}const tagAttr=s.match(/^([a-z]+)(\[.*\])$/);if(tagAttr)return this.tagName===tagAttr[1]&&this.matches(tagAttr[2]);return this.tagName===s}
  querySelectorAll(s){const result=[];for(const c of this.children)if(typeof c!=='string'){if(c.matches(s))result.push(c);result.push(...c.querySelectorAll(s))}return result}
  querySelector(s){return this.querySelectorAll(s)[0]||null}
}
function parse(html){const base=new Element('document'),stack=[base];for(const token of html.match(/<!--[\s\S]*?-->|<![^>]*>|<[^>]*>|[^<]+/g)||[]){if(token.startsWith('<!'))continue;if(token.startsWith('</')){const tag=token.match(/^<\/([\w-]+)/)?.[1];for(let i=stack.length-1;i>0;i--)if(stack[i].tagName===tag){stack.length=i;break;}continue;}if(token.startsWith('<')){const tag=token.match(/^<([\w-]+)/)?.[1];if(!tag)continue;const attrs={};const raw=token.slice(tag.length+1).replace(/\/?\s*>$/,'');for(const m of raw.matchAll(/([^\s=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g))attrs[m[1]]=m[2]??m[3]??m[4]??'';const node=new Element(tag,attrs);stack[stack.length-1].append(node);if(!['img','meta','input','br','link','hr','source'].includes(tag)&&!token.endsWith('/>'))stack.push(node);}else stack[stack.length-1].append(token);}return base;}

const root=parse(source);document={body:root.querySelector('body'),activeElement:null,events:{},getElementById:id=>root.querySelector('#'+id),querySelectorAll:s=>root.querySelectorAll(s),createElement:tag=>new Element(tag),addEventListener(k,fn){this.events[k]=fn;}};
const context=vm.createContext({document,console,setTimeout:()=>1,clearTimeout(){}});context.window=context;
for(const file of ['model.js','app.js'])new vm.Script(fs.readFileSync(path.join(__dirname,file),'utf8')).runInContext(context);
const M=require('./model.js'),$=id=>document.getElementById(id);const answers={photo:['linh','binh','duy'],route:['linh','ha','duy']};
let challengeCount=0,profileCount=0;
function choose(id){$('suspect').value=id;$('suspect').emit('change');}
choose('not-a-profile');assert.equal($('suspect').value,'');assert($('trialResult').textContent.includes('Chọn hồ sơ'));
for(const mode of ['photo','route']){
 root.querySelector('[data-mode="'+mode+'"]').click();
 assert.equal($('levels').querySelectorAll('button')[1].disabled,true);
 assert.equal($('characters').querySelectorAll('button').length,6);
 for(let index=0;index<3;index++){
  const c=M[mode][index];assert($('caseTitle').textContent.includes(c.title));
  for(const art of ['pixel','cartoon']){root.querySelector('[data-art="'+art+'"]').click();assert($('room').src.includes(art));assert.equal($('profileList').querySelectorAll('button').length,6);}
  const first=$('characters').querySelectorAll('button')[0];first.click();assert(!$('shade').hidden);assert($('dialogBody').textContent.includes(M.profiles[0].trait));const tones=$('dialogBody').querySelector('.dialog-actions').querySelectorAll('button');tones[2].click();assert($('dialogBody').querySelector('.quote').textContent===M.profiles[0].joke);$('close').click();profileCount++;
  choose(answers[mode][index]);$('submit').click();assert($('feedback').textContent.includes('Chưa đủ'));assert($('next').hidden);
  for(const key of c.required){
   root.querySelector('[data-clue="'+key+'"]').click();assert(!$('shade').hidden);const quiz=$('dialogBody').querySelector('form');const input=$('dialogBody').querySelector('[data-quiz="'+key+'"]');const q=M.clueQuiz(c,mode,key);input.value=String(q.answer+1);quiz.emit('submit');assert(!$('shade').hidden);assert($('dialogBody').textContent.includes('Chưa khớp'));input.value=String(q.answer);quiz.emit('submit');assert($('shade').hidden);assert(root.querySelector('[data-pin="'+key+'"]').getAttribute('aria-pressed')==='true');challengeCount++;
  }
  const firstKey=c.required[0];root.querySelector('[data-pin="'+firstKey+'"]').click();$('submit').click();assert($('feedback').textContent.includes('Chưa đủ'));root.querySelector('[data-pin="'+firstKey+'"]').click();
  choose(M.profiles.find(p=>p.id!==answers[mode][index]).id);$('submit').click();assert($('feedback').textContent.includes('chưa giải thích'));assert($('next').hidden);
  choose(answers[mode][index]);$('submit').click();assert(!$('shade').hidden);assert($('dialogBody').querySelector('.reveal-banner'));assert($('submit').disabled);
  if(index<2){$('dialogBody').querySelector('button').click();assert($('shade').hidden);assert($('caseTitle').textContent.includes('Vụ '+(index+2)));}else{$('close').click();assert($('next').hidden);}
 }
}
$('tarot').click();assert(!$('shade').hidden);assert($('dialogBody').textContent.includes('không mở nguồn chưa kiếm'));document.events.keydown({key:'Escape'});assert($('shade').hidden);
$('motion').click();assert(document.body.classList.contains('paused'));$('motion').click();assert(!document.body.classList.contains('paused'));
$('reset').click();$('dialogBody').querySelectorAll('button')[0].click();assert($('caseTitle').textContent.includes('Vụ 3'));$('reset').click();$('dialogBody').querySelectorAll('button')[1].click();assert($('caseTitle').textContent.includes('Vụ 1'));assert($('levels').querySelectorAll('button')[1].disabled);assert($('evidenceCount').textContent.startsWith('0/'));
const css=fs.readFileSync(path.join(__dirname,'style.css'),'utf8');assert(css.includes('prefers-reduced-motion')&&css.includes('@keyframes idle'));assert(!/fetch\(|XMLHttpRequest|WebSocket|localStorage|sessionStorage/.test(fs.readFileSync(path.join(__dirname,'app.js'),'utf8')));
$('characters').querySelector('button').click();const focusables=$('modal').querySelectorAll('button:not(:disabled),input,select,a[href]');assert(focusables.length>=4);focusables.at(-1).focus();let trapped=false;document.events.keydown({key:'Tab',preventDefault(){trapped=true}});assert(trapped);assert.equal(document.activeElement,focusables[0]);$('close').click();
console.log(JSON.stringify({actual_model_and_app_scripts:true,art_directions:2,playable_cases:6,earned_and_pinned_challenges:challengeCount,profile_dialogues:profileCount,wrong_guess_and_missing_evidence_gates:true,locked_progression_and_reset:true,personality_never_used_to_grade:true,external_api_calls:false,browser_visual_qa:false},null,2));
