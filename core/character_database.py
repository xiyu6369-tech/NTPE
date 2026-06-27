
from __future__ import annotations
import csv,json,re
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parent.parent
MEMORY_DIR=ROOT/'memory'; LOG_DIR=ROOT/'logs'
OVERRIDE_FILE=ROOT/'character_database_override.json'
OLD_CHARACTER_MEMORY_FILE=MEMORY_DIR/'character_memory.json'
OUTPUT_DB_FILE=MEMORY_DIR/'character_database.json'
OUTPUT_MATCH_FILE=MEMORY_DIR/'character_match_dictionary.json'
OUTPUT_REPORT_FILE=MEMORY_DIR/'character_database_report.txt'
OUTPUT_CSV_FILE=MEMORY_DIR/'character_database_index.csv'
VERSION='2.0'
def ensure_dirs():
    MEMORY_DIR.mkdir(parents=True,exist_ok=True); LOG_DIR.mkdir(parents=True,exist_ok=True)
def log(msg):
    ensure_dirs(); line=f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"; print(line)
    (LOG_DIR/'character_database_log.txt').open('a',encoding='utf-8').write(line+'\n')
def load_json(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save_json(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def safe_get(d,*keys):
    cur=d
    for k in keys:
        if not isinstance(cur,dict): return ''
        cur=cur.get(k,'')
    return str(cur).strip() if cur else ''
def regex_pattern_for_token(token):
    esc=re.escape(token)
    if re.fullmatch(r"[A-Za-z0-9 .'\-]+",token): return rf"\b{esc}\b"
    return rf"(?<![A-Za-z0-9가-힣一-龥]){esc}(?![A-Za-z0-9가-힣一-龥])"
def add_match(matches,source,target,cid,typ,priority,locked):
    source=str(source).strip(); target=str(target).strip()
    if not source or not target: return
    item={'source':source,'target':target,'character_id':cid,'match_type':typ,'priority':priority,'locked':locked,'regex':regex_pattern_for_token(source)}
    old=matches.get(source)
    if old is None or priority>old.get('priority',0): matches[source]=item
def normalize_character(raw,index):
    cid=raw.get('character_id') or f'CHAR{index:06d}'; locked=bool(raw.get('locked',True))
    return {'character_id':cid,'status':raw.get('status','unknown'),'locked':locked,'single_name':raw.get('single_name',{}),'fullname':raw.get('fullname',{}),'firstname':raw.get('firstname',{}),'lastname':raw.get('lastname',{}),'aliases':raw.get('aliases',[]),'relations':raw.get('relations',[]),'confidence':1.0 if locked else 0.75,'note':raw.get('note',''),'history':[{'at':datetime.now().isoformat(timespec='seconds'),'action':'created_or_updated_by_character_database_v2'}]}
def load_override_characters():
    if not OVERRIDE_FILE.exists(): log('未找到 character_database_override.json'); return []
    data=load_json(OVERRIDE_FILE); chars=data.get('characters',[])
    if not isinstance(chars,list): log('character_database_override.json 格式錯誤：characters 不是 list'); return []
    return [normalize_character(c,i) for i,c in enumerate(chars,1) if isinstance(c,dict)]
def collect_known_sources(chars):
    s=set()
    for c in chars:
        for field in ['single_name','fullname','firstname','lastname']:
            b=c.get(field,{})
            if isinstance(b,dict):
                for lang in ['ko','en','zh_tw']:
                    v=str(b.get(lang,'')).strip()
                    if v: s.add(v)
        for a in c.get('aliases',[]):
            v=str(a.get('source','')).strip() if isinstance(a,dict) else str(a).strip()
            if v: s.add(v)
    return s
def load_auto_candidates(existing):
    if not OLD_CHARACTER_MEMORY_FILE.exists(): return []
    try:
        data=load_json(OLD_CHARACTER_MEMORY_FILE); chars=data.get('characters',data)
        if not isinstance(chars,dict): return []
    except Exception as e:
        log(f'讀取舊 character_memory.json 失敗，略過自動候選：{e}'); return []
    out=[]; n=900001
    for source,item in chars.items():
        source=str(source).strip()
        if not source or source in existing or not isinstance(item,dict): continue
        trans=str(item.get('translation','')).strip()
        raw={'character_id':f'AUTO{n}','status':'auto_candidate','locked':False,'single_name':{'ko':source,'en':'','zh_tw':trans},'aliases':[],'relations':[],'note':'auto imported from character_memory.json'}
        out.append(normalize_character(raw,n)); n+=1
    return out
def build_match_dictionary(chars):
    m={}
    for c in chars:
        cid=c['character_id']; locked=c.get('locked',False)
        single=c.get('single_name',{}); full=c.get('fullname',{}); first=c.get('firstname',{}); last=c.get('lastname',{})
        add_match(m,safe_get(full,'ko'),safe_get(full,'zh_tw'),cid,'fullname_ko',120,locked)
        add_match(m,safe_get(full,'en'),safe_get(full,'zh_tw'),cid,'fullname_en',110,locked)
        add_match(m,safe_get(single,'ko'),safe_get(single,'zh_tw'),cid,'single_name_ko',90,locked)
        add_match(m,safe_get(single,'en'),safe_get(single,'zh_tw'),cid,'single_name_en',80,locked)
        add_match(m,safe_get(first,'ko'),safe_get(first,'zh_tw'),cid,'firstname_ko',70,locked)
        add_match(m,safe_get(first,'en'),safe_get(first,'zh_tw'),cid,'firstname_en',65,locked)
        add_match(m,safe_get(last,'ko'),safe_get(last,'zh_tw'),cid,'lastname_ko',60,locked)
        add_match(m,safe_get(last,'en'),safe_get(last,'zh_tw'),cid,'lastname_en',55,locked)
        for a in c.get('aliases',[]):
            if isinstance(a,dict): source=a.get('source',''); target=a.get('target','') or safe_get(full,'zh_tw') or safe_get(single,'zh_tw'); typ=a.get('type','alias'); p=int(a.get('priority',50))
            else: source=str(a); target=safe_get(full,'zh_tw') or safe_get(single,'zh_tw'); typ='alias'; p=50
            add_match(m,source,target,cid,typ,p,locked)
    return dict(sorted(m.items(),key=lambda kv:(-kv[1]['priority'],-len(kv[0]),kv[0])))
def build_database(chars,matches):
    rules=sorted(matches.values(),key=lambda x:(-x['priority'],-len(x['source']),x['source']))
    return {'summary':{'ntpe_module':'Character Database','version':VERSION,'generated_at':datetime.now().isoformat(timespec='seconds'),'character_count':len(chars),'match_count':len(matches),'locked_character_count':sum(1 for c in chars if c.get('locked')),'auto_candidate_count':sum(1 for c in chars if c.get('status')=='auto_candidate'),'rule':'全名翻全名；名字翻名字；姓氏翻姓氏；韓文無空格姓名不拆。'},'characters':chars,'match_dictionary':matches,'priority_rules':rules}
def save_report(db):
    s=db['summary']; lines=['====================================','NTPE Character Database v2.0','====================================','',f"產生時間：{s['generated_at']}",f"角色數：{s['character_count']}",f"匹配規則數：{s['match_count']}",f"鎖定角色數：{s['locked_character_count']}",f"自動候選數：{s['auto_candidate_count']}",'','【核心規則】',s['rule'],'','【角色】']
    for c in db['characters']:
        display=safe_get(c.get('fullname',{}),'zh_tw') or safe_get(c.get('single_name',{}),'zh_tw') or c['character_id']
        lines.append(f"- {c['character_id']}｜{display}｜status={c.get('status','')}｜locked={c.get('locked',False)}")
    lines+=['','【Match Dictionary】']
    for item in db['priority_rules'][:300]: lines.append(f"- P{item['priority']} [{item['match_type']}] {item['source']} -> {item['target']} ({item['character_id']})")
    OUTPUT_REPORT_FILE.write_text('\n'.join(lines)+'\n',encoding='utf-8')
def save_csv(db):
    with OUTPUT_CSV_FILE.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(['character_id','status','locked','field','ko','en','zh_tw','note'])
        for c in db['characters']:
            for field in ['single_name','fullname','firstname','lastname']:
                b=c.get(field,{})
                if isinstance(b,dict) and any(b.get(k) for k in ['ko','en','zh_tw']): w.writerow([c['character_id'],c.get('status',''),c.get('locked',False),field,b.get('ko',''),b.get('en',''),b.get('zh_tw',''),c.get('note','')])
def main():
    ensure_dirs(); log('NTPE Character Database v2.0 啟動')
    manual=load_override_characters(); log(f'讀取人工角色：{len(manual)} 筆')
    auto=load_auto_candidates(collect_known_sources(manual)); log(f'讀取自動候選：{len(auto)} 筆')
    chars=manual+auto; matches=build_match_dictionary(chars); db=build_database(chars,matches)
    save_json(OUTPUT_DB_FILE,db); save_json(OUTPUT_MATCH_FILE,matches); save_report(db); save_csv(db)
    log('角色資料庫建立完成'); log(f"角色數：{db['summary']['character_count']}"); log(f"匹配規則數：{db['summary']['match_count']}"); log(f'輸出：{OUTPUT_DB_FILE}'); log(f'輸出：{OUTPUT_MATCH_FILE}')
if __name__=='__main__': main()
