#!/usr/bin/env python3
"""Rebuild explanatory SVG covers. No network or third-party dependencies.

Only LABS and the Fano covering use frozen project witnesses. Other diagrams
illustrate the problem's structure; they are not claimed frontier results.
"""
from pathlib import Path
import html
import json
import math

OUT = Path(__file__).resolve().parents[1] / 'site/visuals'
TEAL, GOLD, INK, DIM = '#65dacb', '#ffca79', '#112733', '#456373'

def line(a, b, color=TEAL, width=3, extra=''):
    return f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]}" fill="none" stroke="{color}" stroke-width="{width}" {extra}/>'

def dot(x, y, r=7, color=TEAL):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>'

def text(x, y, s, size=20, color='#ecf6f7', anchor='start'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-family="Arial,sans-serif">{html.escape(str(s))}</text>'

def rect(x,y,w,h,color=TEAL,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{color}" {extra}/>'

def save(slug, body, title):
    grid=''.join(line((x,0),(x,400),'#19323e',1) for x in range(0,801,40))+''.join(line((0,y),(800,y),'#19323e',1) for y in range(0,401,40))
    (OUT/(slug+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400"><title>{html.escape(title)}</title><rect width="800" height="400" fill="{INK}"/>{grid}{body}</svg>\n')

def butterfly(slug, stages, subtitle):
    body=''
    for j in range(stages):
        for i in range(8):
            a=(85+j*125,70+i*36)
            for target in (i,i^(1<<(j%3))):
                body+=line(a,(210+j*125,70+target*36),GOLD if i==3 else DIM,2.5)
    for j in range(stages+1):
        for i in range(8):body+=dot(85+j*125,70+i*36,5,GOLD if i==3 else TEAL)
    save(slug,body,subtitle)

butterfly('applied-butterfly-mult',5,'Reuse the work. Move fewer numbers.')
# A layered construction distinguishes the theoretical project from the hardware pipeline.
body=''
levels=[[(100,200)],[(290,110),(290,290)],[(490,80),(490,160),(490,240),(490,320)],[(700,200)]]
for left,right in zip(levels,levels[1:]):
    for a in left:
        for b in right:body+=line(a,b,DIM,2)
for level in levels:
    for x,y in level:body+=rect(x-27,y-22,54,44,TEAL)+dot(x,y,7,INK)
save('integer-mult-bounds',body,'Schematic composition of finite constructions, not a certified witness')

# Exact seven blocks of the project's Fano control, shown as an incidence matrix.
fano=json.loads((OUT/'sources/covering-design-fano.json').read_text())
body=''
for j,block in enumerate(fano['blocks']):
    body+=text(248,103+j*36,f'{j+1}',17)
    for i in range(1,8):body+=dot(280+(i-1)*40,97+j*36,11,TEAL if i in block else '#28434f')
save('covering-design',body,'Fano control: seven triples cover every pair of seven points')

# LABS: actual N=13 reference sequence and exact aperiodic autocorrelations.
w=json.loads((OUT/'sources/labs-13.json').read_text());seq=[1 if x=='1' else -1 for x in w['sequence']]
corr=[sum(seq[i]*seq[i+k] for i in range(len(seq)-k)) for k in range(len(seq))]
assert sum(x*x for x in corr[1:])==w['E']
body=''
for i,s in enumerate(seq):body+=rect(50+i*54,83,43,44,TEAL if s==1 else '#314e60')+text(71+i*54,112,'+' if s==1 else '−',26,INK if s==1 else '#fff','middle')
body+=line((50,320),(750,320),DIM,1)
for i,c in enumerate(corr):body+=rect(60+i*54,320-c*11 if c>=0 else 320,18,max(2,abs(c)*11),GOLD if i==0 else TEAL)
save('labs',body,'N=13 reference sequence and its exact aperiodic autocorrelation')

# Unit-distance triangular patch: illustrative, not a conjecture counterexample.
pts=[(190+j*62+(i%2)*31,88+i*53.693575) for i in range(5) for j in range(5)]
body=''
for i,a in enumerate(pts):
    for b in pts[i+1:]:
        if abs(math.dist(a,b)-62)<.01:body+=line(a,b,DIM,2)
for a in pts:body+=dot(*a,7)
a,b,c=pts[6],pts[7],pts[12]
assert all(abs(math.dist(u,v)-62)<.01 for u,v in [(a,b),(b,c),(c,a)])
body+=f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]} L{c[0]},{c[1]} Z" fill="#ffca7933" stroke="{GOLD}" stroke-width="5"/>'
save('erdos-99',body,'Unit-distance triangular patch, illustrating the triangle sought in Erdős Problem 99')

# Hamming distance as visibly different bit positions.
body=''
a='0000000';b='1110000'
for row,bits in enumerate([a,b]):
    for i,s in enumerate(bits):
        x,y=90+i*89,110+row*100;body+=rect(x,y,65,65,GOLD if i<3 else '#284a58')+text(x+32,y+45,s,38,INK if i<3 else '#fff','middle')
for i in range(3):body+=line((122+i*89,178),(122+i*89,205),GOLD,4)
save('binary-linear-codes',body,'Two illustrative binary words differ in three positions; not a project code witness')

# Reusing an XOR subexpression produces identical outputs with one fewer gate.
body=''
for y,label in [(120,'a'),(200,'b'),(280,'c')]:body+=dot(90,y,8)+text(52,y+7,label,24)
body+=line((90,120),(280,170))+line((90,200),(280,170))+dot(280,170,26,GOLD)+text(280,179,'⊕',26,INK,'middle')
body+=line((307,170),(475,170))+line((90,280),(475,280))+line((475,280),(535,230))+line((395,170),(535,230))
body+=dot(535,230,26,GOLD)+text(535,239,'⊕',26,INK,'middle')+line((560,230),(655,230))+text(670,237,'a⊕b⊕c',18)
body+=text(500,155,'a⊕b',22)
save('crypto-circuits',body,'XOR circuit sharing a subexpression between two outputs')

# Reversible pebbling: illustrative activation schedule.
body=''
for j in range(6):
    x=95+j*121
    if j<5:body+=line((x,150),(x+121,150),DIM,5)
    body+=dot(x,150,25,TEAL if j in (0,3,5) else '#294553')+text(x,157,j+1,20,INK if j in (0,3,5) else '#94b5c4','middle')
body+='<path d="M458,215 Q280,330 216,215" fill="none" stroke="#ffca79" stroke-width="4" stroke-dasharray="9 8"/>'
save('neural-net-memory',body,'A schematic activation graph: retain checkpoints or recompute intermediate values')

# Unrooted binary tree (all internal nodes degree three).
nodes=[(135,100),(135,300),(300,200),(440,200),(550,110),(550,290),(700,65),(700,155),(700,245),(700,335)]
edges=[(0,2),(1,2),(2,3),(3,4),(3,5),(4,6),(4,7),(5,8),(5,9)]
body=''.join(line(nodes[a],nodes[b],TEAL,4) for a,b in edges)
for i,(x,y) in enumerate(nodes):body+=dot(x,y,8,GOLD if i in (0,1,6,7,8,9) else TEAL)
for i,label in [(0,'ACGT'),(1,'ACGA'),(6,'TCGA'),(7,'TCGT'),(8,'ATGT'),(9,'ATGA')]:
 x,y=nodes[i];body+=text(x-30,y-18,label,17,GOLD)
save('phylogenetic-parsimony',body,'Illustrative unrooted binary tree and toy DNA sequences; no inferred evolutionary history')

# IBP one-loop diagram collection condenses to a basis.
body=''
for x,y,r in [(100,135,33),(220,130,40),(340,150,29),(135,265,42),(285,265,34)]:
 body+=f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{TEAL}" stroke-width="3"/>'
 body+=line((x-r-25,y),(x-r,y))+line((x+r,y),(x+r+25,y))
body+=line((420,200),(530,200),GOLD,5)+line((510,180),(530,200),GOLD,5)+line((510,220),(530,200),GOLD,5)
for y in [135,270]:
 body+=f'<circle cx="650" cy="{y}" r="40" fill="#ffca7915" stroke="{GOLD}" stroke-width="4"/>'+line((585,y),(610,y),GOLD)+line((690,y),(715,y),GOLD)
save('ibp-reduction',body,'Schematic one-loop integrals reduced to a smaller master-integral basis')

# Half-plane illustration uses the preprint reference, not a current record.
body=rect(485,60,235,255,'#234e50')+line((100,315),(730,315),DIM,3)+line((100,65),(100,315),DIM,3)
body+=line((340,65),(340,315),TEAL,2,'stroke-dasharray="6 6"')+line((485,60),(485,315),GOLD,4)
body+=text(340,345,'1/2',20,TEAL,'middle')+text(485,345,'7/8',20,GOLD,'middle')+text(720,345,'Re(s)',20)
body+=text(525,150,'ZERO-FREE',23)+text(525,184,'REGION',23)
body+=line((470,235),(380,235),GOLD,4)+line((380,235),(395,220),GOLD,4)+line((380,235),(395,250),GOLD,4)
save('quasi-rh-hillclimb',body,'Schematic zero-free half-plane with the 7/8 preprint reference line')

# Primality: one exact arithmetic example rather than a fabricated tested record.
body=''
for i,n in enumerate([3,5,7,11,13,17,19]):body+=dot(85+i*102,145,30,GOLD if n==7 else '#284a58')+text(85+i*102,153,n,23,INK if n==7 else '#fff','middle')
body+=line((80,215),(710,215),DIM,3)+line((540,195),(540,235),GOLD,4)
save('miller-rabin',body,'Schematic prime witness search and a rigorous cutoff; no example bound is asserted')

# ZK relational example: x*x=y public, x private. Not a full protocol.
body=''
body+=rect(80,110,170,170,'#294553')+text(165,210,'x',64,TEAL,'middle')+text(165,315,'PRIVATE INPUT',18,TEAL,'middle')
body+=line((270,195),(375,195),GOLD,4)+rect(380,145,105,100,GOLD)+text(432,210,'×',50,INK,'middle')+line((490,195),(575,195),GOLD,4)
body+=rect(585,110,140,170,'#294553')+text(655,210,'y',64,TEAL,'middle')+text(655,315,'PUBLIC OUTPUT',18,TEAL,'middle')
save('zk-gadgets',body,'Toy private-input relation x squared equals public y; not a complete zero-knowledge protocol')

# Super-1: conceptual fast / segment / document recurrent memory.
# Spacing conveys timescale, not literal update intervals or model dimensions.
body=''
tiers=[([120,200,280,360,440,520,600,680],290,TEAL,12),
       ([160,320,480,640],190,'#8bbbdc',18),
       ([240,560],90,GOLD,25)]
# Cross-scale connections, behind the state nodes.
for (xs,y,color,r),(parents,py,pc,pr) in zip(tiers,tiers[1:]):
    for i,x in enumerate(xs):
        px=parents[i//2]
        body+=line((x,y-r-5),(px,py+pr+6),DIM,2)
        # Upward update arrow and a short downward readout arrow.
        dx,dy=px-x,py+pr+6-(y-r-5);length=math.hypot(dx,dy)
        ux,uy=dx/length,dy/length
        end=(px,py+pr+6)
        body+=line(end,(end[0]-ux*9-uy*4,end[1]-uy*9+ux*4),color,2)
        body+=line(end,(end[0]-ux*9+uy*4,end[1]-uy*9-ux*4),color,2)
for xs,y,color,r in tiers:
    for a,b in zip(xs,xs[1:]):
        body+=line((a+r+4,y),(b-r-5,y),color,3)
        body+=line((b-r-5,y),(b-r-13,y-5),color,3)+line((b-r-5,y),(b-r-13,y+5),color,3)
    for x in xs:
        body+=f'<circle cx="{x}" cy="{y}" r="{r}" fill="{INK}" stroke="{color}" stroke-width="3"/>'
        body+=dot(x,y,4,color)
        # Feedback loop returning to the same state.
        body+=f'<path d="M{x-r*.6},{y-r*.8} C{x-r*2.2},{y-r*3.4} {x+r*2.2},{y-r*3.4} {x+r*.6},{y-r*.8}" fill="none" stroke="{color}" stroke-width="2"/>'
        body+=line((x+r*.6,y-r*.8),(x+r*.6+7,y-r*.8-4),color,2)
for x in tiers[0][0]:
    body+=rect(x-9,349,18,18,'#355363')+line((x,344),(x,309),DIM,2)
save('super-1',body,'Conceptual hierarchy of recurrent memory across fast, segment and document timescales')

# Numerical computation: phi_1 and an illustrative degree-four Taylor polynomial.
# The lower strip plots the actual difference on the same x-domain, rescaled.
def phi1(x):
    return math.expm1(x)/x if x else 1.0

def taylor_phi1(x):
    return sum(x**n/math.factorial(n+1) for n in range(5))

xs=[-4+i*8/240 for i in range(241)]
def curve(points, color, width=3, extra=''):
    coords=' '.join(f'{x:.3f},{y:.3f}' for x,y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" {extra}/>'

body=line((65,250),(735,250),DIM,2)+line((400,55),(400,250),DIM,1)
body+=curve([(70+(x+4)*82.5,250-phi1(x)*14) for x in xs],TEAL,4)
body+=curve([(70+(x+4)*82.5,250-taylor_phi1(x)*14) for x in xs],GOLD,3,'stroke-dasharray="9 6"')
body+=line((65,343),(735,343),DIM,2)
errors=[phi1(x)-taylor_phi1(x) for x in xs]
scale=62/max(abs(e) for e in errors)
error_points=[(70+(x+4)*82.5,343-e*scale) for x,e in zip(xs,errors)]
body+=f'<polygon points="70,343 '+ ' '.join(f'{x:.3f},{y:.3f}' for x,y in error_points)+' 730,343" fill="#ffca791c"/>'
body+=curve(error_points,GOLD,3)
save('numerical-computation',body,'Phi-one and a degree-four Taylor approximation; the lower strip shows their rescaled difference')

# Exact substring indexing on a toy sequence, not biological experimental data.
sequence='ACGTACGACGTACGT'
query='ACG'
hits=[i for i in range(len(sequence)) if sequence.startswith(query,i)]
suffixes=sorted(sequence[i:] for i in range(len(sequence)))
shown=[s for s in suffixes if s.startswith(query)]+[s for s in suffixes if not s.startswith(query)][:4]
colors={'A':TEAL,'C':'#8bbbdc','G':GOLD,'T':'#bd9cdb'}
body=''
for i,ch in enumerate(sequence):
    x=69+i*44
    body+=rect(x,48,34,37,colors[ch])+text(x+17,75,ch,23,INK,'middle')
for hit in hits:body+=line((69+hit*44,99),(69+(hit+3)*44-10,99),GOLD,4)
# Ordered suffix rows make the matching prefixes form one contiguous interval.
for row,suffix in enumerate(shown):
    for col,ch in enumerate(suffix[:8]):
        x,y=115+col*29,147+row*25
        body+=rect(x,y,22,19,colors[ch],extra='opacity=".9"' if row<4 else 'opacity=".35"')
body+=f'<path d="M103,147 H92 V241 H103" fill="none" stroke="{GOLD}" stroke-width="3"/>'
body+=line((376,220),(470,220),DIM,3)+line((470,220),(459,212),DIM,3)+line((470,220),(459,228),DIM,3)
for i,ch in enumerate(query):body+=rect(510+i*47,161,37,42,colors[ch])+text(528+i*47,191,ch,27,INK,'middle')
for j in range(len(hits)):body+=dot(530+j*39,254,9,GOLD)
save('genomic-sequence-indexing',body,'Toy DNA substring search: four ACG occurrences and an ordered suffix interval')

# Two real snapshots from the project's 160-agent room-map plan.
plan=json.loads((OUT/'sources/pathfinding-room-plan.json').read_text())
paths=plan['paths']
def cell_at(path,t):
    return path[min(t,len(path)-1)]

# Check the whole saved plan for traversability, legal moves and both collision types.
for i,path in enumerate(paths):
    assert path[-1]==plan['goals'][i]
    for cell in path:assert plan['rows'][cell//32][cell%32]=='.'
    for a,b in zip(path,path[1:]):assert abs(a%32-b%32)+abs(a//32-b//32)<=1
for t in range(max(map(len,paths))):
    cells=[cell_at(path,t) for path in paths]
    assert len(cells)==len(set(cells))
    if t:
        edges={(cell_at(path,t-1),cell_at(path,t)) for path in paths}
        assert all(a==b or (b,a) not in edges for a,b in edges)
body=''
palette=[TEAL,GOLD,'#8bbbdc','#bd9cdb','#ef9c92']
for ox,t in [(43,0),(437,25)]:
    size=10
    for row,cells in enumerate(plan['rows']):
        for col,ch in enumerate(cells):
            if ch!='.':body+=rect(ox+col*size,40+row*size,9,9,'#36515e')
    for i,path in enumerate(paths):
        if i<5:
            pts=[(ox+(c%32+.5)*size,40+(c//32+.5)*size) for c in path[:min(t+1,len(path))]]
            body+=curve(pts,palette[i],2)
        c=cell_at(path,t)
        body+=dot(ox+(c%32+.5)*size,40+(c//32+.5)*size,3.4,palette[i%5])
body+=line((379,200),(420,200),GOLD,3)+line((420,200),(409,191),GOLD,3)+line((420,200),(409,209),GOLD,3)
save('pathfinding',body,'Real 160-agent room-map plan at steps zero and twenty-five, with five highlighted trails')
